#!/usr/bin/env python3
"""Record a last-known-good skill install and plan safe upgrades/rollbacks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def home() -> Path:
    configured = os.environ.get("VIBE_CODING_HOME")
    return Path(configured).expanduser().resolve() if configured else (Path.home() / ".vibe-coding").resolve()


def installation_id(root: Path) -> str:
    return hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:16]


def state_dir(root: Path, create: bool = False) -> Path:
    path = home() / "skill-installations" / installation_id(root)
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def state_path(root: Path) -> Path:
    return state_dir(root, create=False) / "last-known-good.json"


def git(root: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    return p.returncode, (p.stdout or p.stderr).strip()


def version(root: Path) -> str | None:
    version_file = root / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    skill = root / "SKILL.md"
    if not skill.exists():
        return None
    match = re.search(r'(?m)^  version:\s*"([^"]+)"\s*$', skill.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def git_status(root: Path) -> dict[str, Any]:
    rc, inside = git(root, "rev-parse", "--is-inside-work-tree")
    if rc != 0 or inside != "true":
        return {"git": False}
    _, head = git(root, "rev-parse", "HEAD")
    _, branch = git(root, "branch", "--show-current")
    _, dirty = git(root, "status", "--porcelain")
    return {"git": True, "head": head, "branch": branch or None, "dirty": bool(dirty)}


def load_good(root: Path) -> dict[str, Any] | None:
    path = state_path(root)
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def record_good(root: Path) -> dict[str, Any]:
    root = root.resolve()
    current = git_status(root)
    if not current.get("git"):
        raise RuntimeError("record-good requires a Git-based skill installation")
    if current.get("dirty"):
        raise RuntimeError("refusing to record last-known-good from a dirty skill installation")
    data = {
        "schema_version": 1,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "skill_root": str(root),
        "version": version(root),
        "head": current["head"],
        "branch": current.get("branch"),
    }
    path = state_dir(root, create=True) / "last-known-good.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    data["state_path"] = str(path)
    return data


def plan_upgrade(root: Path, target_ref: str) -> dict[str, Any]:
    root = root.resolve()
    current = git_status(root)
    if not current.get("git"):
        return {"status": "BLOCK", "failures": ["upgrade planning requires a Git-based installation"]}
    if current.get("dirty"):
        return {"status": "BLOCK", "failures": ["skill installation is dirty; preserve or discard local edits first"]}

    rc, target = git(root, "rev-parse", "--verify", f"{target_ref}^{{commit}}")
    if rc != 0:
        return {
            "status": "BLOCK",
            "failures": [f"target ref {target_ref!r} is not available locally; fetch/update it explicitly first"],
            "network_used": False,
        }

    ancestor_rc, _ = git(root, "merge-base", "--is-ancestor", str(current["head"]), target)
    fast_forward = ancestor_rc == 0
    warnings = [] if fast_forward else ["target is not a fast-forward descendant of the current install"]
    return {
        "status": "WARN" if warnings else "PASS",
        "network_used": False,
        "current": current,
        "current_version": version(root),
        "target_ref": target_ref,
        "target_commit": target,
        "fast_forward": fast_forward,
        "warnings": warnings,
        "before_upgrade": "run record-good before changing the installation",
    }


def rollback(root: Path, apply: bool) -> dict[str, Any]:
    root = root.resolve()
    current = git_status(root)
    good = load_good(root)
    if not current.get("git"):
        raise RuntimeError("rollback requires a Git-based skill installation")
    if current.get("dirty"):
        raise RuntimeError("refusing rollback while skill installation has local changes")
    if not good or not good.get("head"):
        raise RuntimeError("no last-known-good installation has been recorded")

    target = str(good["head"])
    rc, resolved = git(root, "rev-parse", "--verify", f"{target}^{{commit}}")
    if rc != 0:
        raise RuntimeError("last-known-good commit is not available in this clone; reinstall/fetch that version first")

    command = ["git", "checkout", "--detach", resolved]
    if not apply:
        return {
            "applied": False,
            "target_commit": resolved,
            "target_version": good.get("version"),
            "command": command,
            "note": "dry-run; pass --apply for an explicit detached rollback",
        }

    rc, out = git(root, "checkout", "--detach", resolved)
    if rc != 0:
        raise RuntimeError(out or "rollback checkout failed")
    return {
        "applied": True,
        "target_commit": resolved,
        "target_version": good.get("version"),
        "output": out,
    }


def status(root: Path) -> dict[str, Any]:
    return {
        "skill_root": str(root.resolve()),
        "version": version(root),
        "current": git_status(root),
        "last_known_good": load_good(root),
        "state_path": str(state_path(root)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    for command in ("status", "record-good", "rollback", "plan-upgrade"):
        p = sub.add_parser(command)
        p.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
        p.add_argument("--json", action="store_true")
        if command == "rollback":
            p.add_argument("--apply", action="store_true")
        if command == "plan-upgrade":
            p.add_argument("--target-ref", required=True)

    ns = ap.parse_args()
    root = Path(ns.skill_root).resolve()
    try:
        if ns.command == "status":
            result = status(root)
        elif ns.command == "record-good":
            result = record_good(root)
        elif ns.command == "plan-upgrade":
            result = plan_upgrade(root, ns.target_ref)
        else:
            result = rollback(root, ns.apply)
    except RuntimeError as exc:
        if ns.json:
            print(json.dumps({"status": "BLOCK", "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}")
        return 2

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
