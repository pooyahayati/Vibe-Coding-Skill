#!/usr/bin/env python3
"""Inspect and safely repair corrupted local Vibe Coding state."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import local_workspace
import project_state

JSON_STATE_FILES = [
    "project.json",
    "graph-state.json",
    "project-state.json",
    "traceability.json",
    "github-snapshot.json",
]


def inspect(root: Path) -> dict[str, Any]:
    root = root.resolve()
    local_workspace.ensure_git_repo(root)
    workspace = local_workspace.project_workspace(root, create=False)
    state_dir = workspace / "state"
    items: list[dict[str, Any]] = []

    for name in JSON_STATE_FILES:
        path = state_dir / name
        if not path.exists():
            items.append({"name": name, "status": "MISSING", "path": str(path)})
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("top-level JSON value is not an object")
            items.append({"name": name, "status": "OK", "path": str(path)})
        except Exception as exc:
            items.append({
                "name": name,
                "status": "CORRUPT",
                "path": str(path),
                "error": str(exc),
            })

    corrupt = [item for item in items if item["status"] == "CORRUPT"]
    return {
        "status": "WARN" if corrupt else "PASS",
        "workspace": str(workspace),
        "workspace_exists": workspace.exists(),
        "items": items,
        "corrupt": [item["name"] for item in corrupt],
    }


def recovery_plan(root: Path) -> dict[str, Any]:
    report = inspect(root)
    actions: list[dict[str, str]] = []
    for item in report["items"]:
        if item["status"] != "CORRUPT":
            continue
        name = item["name"]
        action = "quarantine"
        if name == "project-state.json":
            action = "quarantine_then_regenerate"
        elif name in {"project.json", "traceability.json"}:
            action = "quarantine_manual_rebuild"
        elif name == "graph-state.json":
            action = "quarantine_graph_refresh_required"
        elif name == "github-snapshot.json":
            action = "quarantine_snapshot_can_be_refetched"
        actions.append({"file": name, "action": action})
    return {
        "status": "ACTION_REQUIRED" if actions else "HEALTHY",
        "workspace_exists": report["workspace_exists"],
        "actions": actions,
    }


def repair(root: Path, apply: bool) -> dict[str, Any]:
    root = root.resolve()
    plan = recovery_plan(root)
    if not apply:
        return {"applied": False, "plan": plan}

    local_workspace.initialize(root)
    workspace = local_workspace.project_workspace(root, create=True)
    state_dir = workspace / "state"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = state_dir / "recovery-backups" / timestamp
    moved: list[dict[str, str]] = []

    for action in plan["actions"]:
        name = action["file"]
        source = state_dir / name
        if not source.exists():
            continue
        backup_dir.mkdir(parents=True, exist_ok=True)
        destination = backup_dir / name
        shutil.move(str(source), str(destination))
        moved.append({"file": name, "backup": str(destination)})

    regenerated = None
    if any(item["file"] == "project-state.json" for item in plan["actions"]):
        regenerated_state = project_state.capture(root)
        regenerated = regenerated_state.get("state_path")

    return {
        "applied": True,
        "plan": plan,
        "backup_dir": str(backup_dir) if moved else None,
        "moved": moved,
        "regenerated_project_state": regenerated,
        "notes": [
            "project.json is not fabricated from chat or guesses; rebuild it from verified project facts",
            "traceability.json is not fabricated; re-index GitHub objects when available",
            "graph-state.json removal intentionally forces graph refresh before authoritative use",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    for command in ("inspect", "repair"):
        p = sub.add_parser(command)
        p.add_argument("--root", default=".")
        p.add_argument("--json", action="store_true")
        if command == "repair":
            p.add_argument("--apply", action="store_true")

    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    try:
        result = inspect(root) if ns.command == "inspect" else repair(root, ns.apply)
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
