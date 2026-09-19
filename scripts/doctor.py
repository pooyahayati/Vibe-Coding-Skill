#!/usr/bin/env python3
"""Project/tool health check for Vibe Coding Skill."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    return p.returncode, (p.stdout or p.stderr).strip()


def version_of(command: str, args: list[str] | None = None) -> str | None:
    path = shutil.which(command)
    if not path:
        return None
    p = subprocess.run([path, *(args or ["--version"])], text=True, capture_output=True)
    lines = (p.stdout or p.stderr).strip().splitlines()
    return lines[0] if lines else "installed"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    root = Path(ns.root).resolve()
    graph: dict[str, object] = {"state_file": None, "stale": None}
    result: dict[str, object] = {
        "root": str(root),
        "git": {"installed": bool(shutil.which("git"))},
        "tools": {
            "graphify": version_of("graphify"),
            "trivy": version_of("trivy"),
        },
        "graph": graph,
        "problems": [],
    }
    problems: list[str] = result["problems"]  # type: ignore[assignment]

    if not shutil.which("git"):
        problems.append("git is required")
    else:
        rc, inside = run(["git", "rev-parse", "--is-inside-work-tree"], root)
        if rc != 0 or inside != "true":
            problems.append("target is not a git working tree")
        else:
            _, head = run(["git", "rev-parse", "HEAD"], root)
            _, status = run(["git", "status", "--porcelain"], root)
            result["git"] = {"installed": True, "head": head, "dirty": bool(status)}

            state_path = root / ".vibe" / "graph-state.json"
            if state_path.exists():
                graph["state_file"] = str(state_path)
                try:
                    state = json.loads(state_path.read_text(encoding="utf-8"))
                    source_commit = state.get("source_commit")
                    stale = bool(source_commit and source_commit != head)
                    graph["provider"] = state.get("provider")
                    graph["provider_version"] = state.get("provider_version")
                    graph["source_commit"] = source_commit
                    graph["stale"] = stale
                    if stale:
                        problems.append("project graph may be stale")
                except Exception as exc:
                    problems.append(f"invalid graph state: {exc}")

    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Root: {root}")
        print(f"Git: {result['git']}")
        tools = result["tools"]
        print(f"Graphify: {tools['graphify']}")  # type: ignore[index]
        print(f"Trivy: {tools['trivy']}")  # type: ignore[index]
        print(f"Graph: {result['graph']}")
        print("Problems: " + ("; ".join(problems) if problems else "none"))

    return 1 if ns.strict and problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
