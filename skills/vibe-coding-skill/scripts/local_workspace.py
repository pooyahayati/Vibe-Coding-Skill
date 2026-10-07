#!/usr/bin/env python3
"""Local-only workspace manager for Vibe Coding Skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

LOCAL_EXCLUDES = [
    ".vibe/",
    ".vibe-coding/",
    ".claude/skills/vibe-coding-skill/",
    ".codex/skills/vibe-coding-skill/",
    ".agents/skills/vibe-coding-skill/",
    "graphify-out/",
    ".trivy/",
    "benchmark-results/",
    "coverage/",
    "htmlcov/",
    "test-results/",
    "playwright-report/",
    "allure-results/",
    "graphify-compat.json",
    "trivy-report.json",
    "trivy-report.sarif",
]

WORKSPACE_DIRS = [
    "state",
    "graph",
    "security",
    "test-artifacts",
    "benchmarks",
    "worktrees",
    "cache",
]

MARKER_START = "# >>> Vibe Coding Skill local-only artifacts >>>"
MARKER_END = "# <<< Vibe Coding Skill local-only artifacts <<<"


def run_git(root: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    return p.returncode, (p.stdout or p.stderr).strip()


def ensure_git_repo(root: Path) -> None:
    rc, inside = run_git(root, "rev-parse", "--is-inside-work-tree")
    if rc != 0 or inside != "true":
        raise RuntimeError("target is not a Git working tree")


def git_origin(root: Path) -> str | None:
    rc, out = run_git(root, "remote", "get-url", "origin")
    return out if rc == 0 and out else None


def workspace_home() -> Path:
    configured = os.environ.get("VIBE_CODING_HOME")
    return Path(configured).expanduser().resolve() if configured else (Path.home() / ".vibe-coding").resolve()


def project_id(root: Path) -> str:
    root = root.resolve()
    safe_name = "".join(ch.lower() if ch.isalnum() else "-" for ch in root.name).strip("-") or "project"
    # Adopt a unique existing checkout workspace in place. Keeping its ID also
    # keeps legacy receipt/source bindings valid; remote URLs are only metadata.
    preferred = f"{safe_name}-{hashlib.sha256(str(root).encode('utf-8')).hexdigest()[:16]}"
    matches = []
    for candidate in (workspace_home() / "projects").glob(safe_name + "-*"):
        if not candidate.is_dir():
            continue
        try:
            metadata = candidate / "metadata.json"
            # Collectors may create a task directory before workspace init.
            # The new path-derived ID already identifies this exact checkout.
            if candidate.name == preferred and not metadata.exists() and not candidate.is_symlink():
                matches.append(candidate.name)
                continue
            if candidate.is_symlink() or metadata.is_symlink() or metadata.stat().st_size > 65536:
                raise ValueError("unsafe workspace metadata")
            value = json.loads(metadata.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or value.get("project_id") != candidate.name or not isinstance(value.get("project_root"), str):
                raise ValueError("invalid workspace metadata")
            if Path(value["project_root"]).resolve() == root:
                matches.append(candidate.name)
            elif candidate.name == preferred:
                raise ValueError("workspace identity belongs to another project")
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"workspace identity needs reconciliation: {candidate}: {exc}") from exc
    if len(matches) > 1:
        raise RuntimeError("ambiguous legacy workspaces for this checkout; reconcile before continuing")
    return matches[0] if matches else preferred


def atomic_json(path: Path, value: dict) -> None:
    """Replace one local record without exposing a partially written JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def project_workspace(root: Path, create: bool = False) -> Path:
    ensure_git_repo(root)
    path = workspace_home() / "projects" / project_id(root)
    if create:
        path.mkdir(parents=True, exist_ok=True)
        for name in WORKSPACE_DIRS:
            (path / name).mkdir(parents=True, exist_ok=True)
        metadata = {
            "schema_version": 1,
            "project_id": path.name,
            "project_root": str(root.resolve()),
            "origin": git_origin(root),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        atomic_json(path / "metadata.json", metadata)
    return path


def git_info_exclude(root: Path) -> Path:
    ensure_git_repo(root)
    rc, exclude_path = run_git(root, "rev-parse", "--git-path", "info/exclude")
    if rc != 0:
        raise RuntimeError("cannot resolve Git local exclude path")
    path = Path(exclude_path)
    return path if path.is_absolute() else (root / path).resolve()


def configure_local_excludes(root: Path) -> Path:
    exclude = git_info_exclude(root)
    exclude.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""

    if MARKER_START in existing and MARKER_END in existing:
        before, rest = existing.split(MARKER_START, 1)
        _, after = rest.split(MARKER_END, 1)
        existing = before.rstrip() + ("\n" if before.strip() else "") + after.lstrip("\n")

    block = "\n".join([MARKER_START, *LOCAL_EXCLUDES, MARKER_END]) + "\n"
    if existing and not existing.endswith("\n"):
        existing += "\n"
    exclude.write_text(existing + block, encoding="utf-8")
    return exclude


def state_path(root: Path, name: str, create: bool = False) -> Path:
    return project_workspace(root, create=create) / "state" / name


def artifact_path(root: Path, category: str, name: str, create: bool = False) -> Path:
    if category not in WORKSPACE_DIRS:
        raise ValueError(f"unknown workspace category: {category}")
    base = project_workspace(root, create=create) / category
    if create:
        base.mkdir(parents=True, exist_ok=True)
    return base / name


def initialize(root: Path) -> dict[str, str]:
    workspace = project_workspace(root, create=True)
    exclude = configure_local_excludes(root)
    return {
        "project_id": project_id(root),
        "workspace": str(workspace),
        "git_info_exclude": str(exclude),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    for command in ("init", "path", "exclude"):
        p = sub.add_parser(command)
        p.add_argument("--root", default=".")
        p.add_argument("--json", action="store_true")

    ns = ap.parse_args()
    root = Path(ns.root).resolve()

    try:
        if ns.command == "init":
            result = initialize(root)
        elif ns.command == "exclude":
            result = {"git_info_exclude": str(configure_local_excludes(root))}
        else:
            result = {
                "project_id": project_id(root),
                "workspace": str(project_workspace(root, create=False)),
            }
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
