#!/usr/bin/env python3
"""Local-only workspace manager for Vibe Coding Skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
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
    origin = git_origin(root) or ""
    material = f"{origin}\n{root}".encode("utf-8")
    digest = hashlib.sha256(material).hexdigest()[:16]
    safe_name = "".join(ch.lower() if ch.isalnum() else "-" for ch in root.name).strip("-") or "project"
    return f"{safe_name}-{digest}"


def project_workspace(root: Path, create: bool = False) -> Path:
    ensure_git_repo(root)
    path = workspace_home() / "projects" / project_id(root)
    if create:
        path.mkdir(parents=True, exist_ok=True)
        for name in WORKSPACE_DIRS:
            (path / name).mkdir(parents=True, exist_ok=True)
        metadata = {
            "schema_version": 1,
            "project_id": project_id(root),
            "project_root": str(root.resolve()),
            "origin": git_origin(root),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        (path / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
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
