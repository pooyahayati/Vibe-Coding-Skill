#!/usr/bin/env python3
"""Safely bootstrap durable project state for Vibe Coding Skill."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date
from pathlib import Path

PROFILE_DOCS = {
    "minimal": ["STATUS.md"],
    "standard": ["STATUS.md", "PROJECT.md"],
    "significant": ["STATUS.md", "PROJECT.md", "ARCHITECTURE.md", "PROJECT_GRAPH.md"],
    "critical": ["STATUS.md", "PROJECT.md", "ARCHITECTURE.md", "PROJECT_GRAPH.md", "ROADMAP.md"],
}


def in_git_repo(root: Path) -> bool:
    p = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    return p.returncode == 0 and p.stdout.strip() == "true"


def write_if_safe(path: Path, content: str | None, force: bool, created: list[str], skipped: list[str]) -> None:
    if content is None:
        skipped.append(f"{path.name}: insufficient known context")
        return
    if path.exists() and not force:
        skipped.append(f"{path.name}: exists")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    created.append(path.name)


def project_doc(ns: argparse.Namespace) -> str | None:
    required = [ns.problem, ns.primary_user, ns.core_outcome, ns.mvp]
    if not all(required):
        return None
    return f"""# {ns.project_name}

## Problem

{ns.problem}

## Primary user

{ns.primary_user}

## Core outcome

{ns.core_outcome}

## MVP

{ns.mvp}

## Current objective

{ns.objective}
"""


def architecture_doc(ns: argparse.Namespace) -> str | None:
    if not ns.stack or not ns.architecture:
        return None
    return f"""# Architecture

## Stack

{ns.stack}

## Architecture

{ns.architecture}

## Current objective

{ns.objective}
"""


def graph_doc(ns: argparse.Namespace) -> str | None:
    if not ns.graph_summary:
        return None
    return f"""# Project Graph

Human-readable high-level architecture/dependency map.

## Current map

{ns.graph_summary}

Machine graph provider: Graphify when available.
"""


def roadmap_doc(ns: argparse.Namespace) -> str | None:
    if not ns.milestones:
        return None
    return f"""# Roadmap

## Milestones

{ns.milestones}
"""


def agents_doc(ns: argparse.Namespace) -> str | None:
    if not ns.multi_agent:
        return None
    if not ns.agent_plan:
        return None
    return f"""# Agents

Use the minimum effective agent team.

## Ownership and boundaries

{ns.agent_plan}
"""


def status_doc(ns: argparse.Namespace) -> str:
    return f"""# Status

Updated: {date.today().isoformat()}

## Current Objective

{ns.objective}

## Completed

None recorded yet.

## In Progress

Project bootstrap.

## Next

Execute the next Ready task supporting the Current Objective.

## Blockers

None recorded.

## Verification

Not yet recorded.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--profile", choices=PROFILE_DOCS, default="standard")
    ap.add_argument("--project-name")
    ap.add_argument("--objective", required=True)
    ap.add_argument("--problem")
    ap.add_argument("--primary-user")
    ap.add_argument("--core-outcome")
    ap.add_argument("--mvp")
    ap.add_argument("--stack")
    ap.add_argument("--architecture")
    ap.add_argument("--graph-summary")
    ap.add_argument("--milestones")
    ap.add_argument("--multi-agent", action="store_true")
    ap.add_argument("--agent-plan")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    root = Path(ns.root).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit("target root must be an existing directory")
    if not in_git_repo(root):
        raise SystemExit("bootstrap requires a Git working tree")

    ns.project_name = ns.project_name or root.name
    docs: dict[str, str | None] = {
        "STATUS.md": status_doc(ns),
        "PROJECT.md": project_doc(ns),
        "ARCHITECTURE.md": architecture_doc(ns),
        "PROJECT_GRAPH.md": graph_doc(ns),
        "ROADMAP.md": roadmap_doc(ns),
        "AGENTS.md": agents_doc(ns),
    }

    wanted = list(PROFILE_DOCS[ns.profile])
    if ns.multi_agent:
        wanted.append("AGENTS.md")

    created: list[str] = []
    skipped: list[str] = []

    if not ns.dry_run:
        for name in wanted:
            write_if_safe(root / name, docs[name], ns.force, created, skipped)

        vibe_dir = root / ".vibe"
        vibe_dir.mkdir(parents=True, exist_ok=True)
        state_path = vibe_dir / "project.json"
        if not state_path.exists() or ns.force:
            state = {
                "schema_version": 1,
                "profile": ns.profile,
                "project_name": ns.project_name,
                "current_objective": ns.objective,
                "updated": date.today().isoformat(),
            }
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            created.append(".vibe/project.json")
        else:
            skipped.append(".vibe/project.json: exists")
    else:
        for name in wanted:
            if docs[name] is None:
                skipped.append(f"{name}: insufficient known context")
            elif (root / name).exists() and not ns.force:
                skipped.append(f"{name}: exists")
            else:
                created.append(name)
        created.append(".vibe/project.json (planned)")

    result = {
        "profile": ns.profile,
        "created_or_planned": created,
        "skipped": skipped,
        "destructive": bool(ns.force),
    }
    if ns.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Profile: {ns.profile}")
        print("Created/planned: " + (", ".join(created) if created else "none"))
        print("Skipped: " + ("; ".join(skipped) if skipped else "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
