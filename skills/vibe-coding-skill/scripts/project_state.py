#!/usr/bin/env python3
"""Local project-state capture, drift detection, and handoff summary."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import graph_provider
import github_traceability
import local_workspace

DOCS = [
    "STATUS.md",
    "PROJECT.md",
    "ROADMAP.md",
    "ARCHITECTURE.md",
    "PROJECT_GRAPH.md",
    "AGENTS.md",
    "README.md",
]


def run_git(root: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    return p.returncode, (p.stdout or p.stderr).strip()


def file_hash(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_state(root: Path) -> dict[str, Any]:
    root = root.resolve()
    local_workspace.ensure_git_repo(root)
    _, head = run_git(root, "rev-parse", "HEAD")
    _, branch = run_git(root, "branch", "--show-current")
    _, status = run_git(root, "status", "--porcelain")
    _, origin = run_git(root, "remote", "get-url", "origin")

    project_meta_path = local_workspace.state_path(root, "project.json", create=False)
    project_meta = None
    if project_meta_path.exists():
        try:
            project_meta = json.loads(project_meta_path.read_text(encoding="utf-8"))
        except Exception:
            project_meta = None

    return {
        "schema_version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "project_id": local_workspace.project_id(root),
        "root": str(root),
        "git": {
            "head": head or None,
            "branch": branch or None,
            "dirty": bool(status),
            "origin": origin or None,
            "working_tree_fingerprint": graph_provider.working_tree_fingerprint(root),
        },
        "graph": graph_provider.status(root),
        "github": github_traceability.detect(root),
        "project": project_meta,
        "documents": {
            name: {"present": (root / name).exists(), "sha256": file_hash(root / name)}
            for name in DOCS
        },
    }


def state_path(root: Path, create: bool = False) -> Path:
    return local_workspace.state_path(root, "project-state.json", create=create)


def load_previous(root: Path) -> dict[str, Any] | None:
    path = state_path(root, create=False)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def compare(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    if not previous:
        return {"baseline_exists": False, "changes": ["no previous local state snapshot"]}
    changes: list[str] = []
    if previous.get("git", {}).get("head") != current.get("git", {}).get("head"):
        changes.append("git head changed")
    if previous.get("git", {}).get("branch") != current.get("git", {}).get("branch"):
        changes.append("git branch changed")
    if previous.get("git", {}).get("working_tree_fingerprint") != current.get("git", {}).get("working_tree_fingerprint"):
        changes.append("working tree changed")
    if previous.get("graph", {}).get("fresh") != current.get("graph", {}).get("fresh"):
        changes.append("graph freshness changed")
    if previous.get("github", {}).get("repository") != current.get("github", {}).get("repository"):
        changes.append("GitHub repository identity changed")
    previous_docs = previous.get("documents", {})
    current_docs = current.get("documents", {})
    for name in DOCS:
        if previous_docs.get(name, {}).get("sha256") != current_docs.get(name, {}).get("sha256"):
            changes.append(f"{name} changed")
    return {"baseline_exists": True, "changes": changes}


def capture(root: Path) -> dict[str, Any]:
    local_workspace.initialize(root)
    previous = load_previous(root)
    current = current_state(root)
    current["drift_from_previous"] = compare(previous, current)
    path = state_path(root, create=True)
    path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    current["state_path"] = str(path)
    return current


def drift(root: Path) -> dict[str, Any]:
    previous = load_previous(root)
    current = current_state(root)
    comparison = compare(previous, current)
    status = "WARN" if comparison["changes"] else "PASS"
    if not comparison["baseline_exists"]:
        status = "WARN"
    return {"status": status, "comparison": comparison, "current": current}


def handoff_markdown(state: dict[str, Any]) -> str:
    project = state.get("project") or {}
    objective = project.get("current_objective") or "Read STATUS.md / PROJECT.md if present."
    graph = state.get("graph") or {}
    github = state.get("github") or {}
    git_state = state.get("git") or {}
    lines = [
        "# Local Handoff Snapshot",
        "",
        f"- Objective: {objective}",
        f"- Branch: {git_state.get('branch')}",
        f"- HEAD: {git_state.get('head')}",
        f"- Working tree dirty: {git_state.get('dirty')}",
        f"- Graph fresh: {graph.get('fresh')}",
        f"- Graph path: {graph.get('graph_path')}",
        f"- GitHub repository: {github.get('repository')}",
        "",
        "Resume order:",
        "STATUS.md -> PROJECT.md -> ROADMAP.md -> ARCHITECTURE.md -> PROJECT_GRAPH.md -> AGENTS.md -> GitHub -> source/tests",
        "",
        "This file is local operational state. Do not commit it to the project repository.",
        "",
    ]
    return "\n".join(lines)


def handoff(root: Path, write_local: bool) -> dict[str, Any]:
    state = capture(root)
    markdown = handoff_markdown(state)
    result = {"state": state, "markdown": markdown}
    if write_local:
        path = local_workspace.state_path(root, "handoff.md", create=True)
        path.write_text(markdown, encoding="utf-8")
        result["handoff_path"] = str(path)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    for command in ("capture", "drift", "handoff"):
        p = sub.add_parser(command)
        p.add_argument("--root", default=".")
        p.add_argument("--json", action="store_true")
        if command == "handoff":
            p.add_argument("--write-local", action="store_true")

    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    try:
        if ns.command == "capture":
            result = capture(root)
        elif ns.command == "drift":
            result = drift(root)
        else:
            result = handoff(root, ns.write_local)
    except RuntimeError as exc:
        if ns.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}")
        return 2

    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif ns.command == "handoff":
        print(result["markdown"])
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
