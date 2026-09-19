#!/usr/bin/env python3
"""Manage Graphify as the default project-intelligence provider."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
TOOLCHAIN = SCRIPT_ROOT / "config" / "toolchain.json"

def run(cmd: list[str], cwd: Path, timeout: int = 300) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    return p.returncode, ((p.stdout or "") + ("\n" + p.stderr if p.stderr else "")).strip()

def git_head(root: Path) -> str | None:
    rc, out = run(["git", "rev-parse", "HEAD"], root)
    return out.splitlines()[0].strip() if rc == 0 and out.strip() else None

def graphify_version() -> str | None:
    exe = shutil.which("graphify")
    if not exe:
        return None
    p = subprocess.run([exe, "--version"], text=True, capture_output=True)
    out = (p.stdout or p.stderr).strip()
    m = re.search(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", out)
    return m.group(0) if m else (out or "installed")

def approved_version() -> str | None:
    if not TOOLCHAIN.exists():
        return None
    try:
        return json.loads(TOOLCHAIN.read_text(encoding="utf-8")).get("graphify", {}).get("approved")
    except Exception:
        return None

def state_path(root: Path) -> Path:
    return root / ".vibe" / "graph-state.json"

def read_state(root: Path) -> dict[str, object] | None:
    path = state_path(root)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"invalid": True}

def status(root: Path) -> dict[str, object]:
    head = git_head(root)
    state = read_state(root)
    graph_json = root / "graphify-out" / "graph.json"
    source_commit = state.get("source_commit") if isinstance(state, dict) else None
    stale = None
    if source_commit and head:
        stale = source_commit != head
    elif graph_json.exists():
        stale = True
    installed = graphify_version()
    approved = approved_version()
    return {
        "provider": "graphify", "installed_version": installed,
        "approved_version": approved,
        "version_matches_approved": bool(installed and approved and installed == approved),
        "graph_exists": graph_json.exists(),
        "graph_path": str(graph_json) if graph_json.exists() else None,
        "git_head": head, "state": state, "stale": stale,
    }

def record_state(root: Path) -> dict[str, object]:
    payload = {
        "schema_version": 1, "provider": "graphify",
        "provider_version": graphify_version(),
        "source_commit": git_head(root),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    path = state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload

def build_or_update(root: Path, force_build: bool = False) -> dict[str, object]:
    if not shutil.which("graphify"):
        return {"ok": False, "error": "graphify is not installed"}
    graph_exists = (root / "graphify-out" / "graph.json").exists()
    command = ["graphify", ".", "--code-only", "--no-viz"] if force_build or not graph_exists else ["graphify", "update", "."]
    rc, out = run(command, root, timeout=600)
    result: dict[str, object] = {"ok": rc == 0, "command": command, "output": out[-4000:]}
    if rc == 0:
        graph_path = root / "graphify-out" / "graph.json"
        if not graph_path.exists():
            result["ok"] = False
            result["error"] = "Graphify command succeeded but graphify-out/graph.json was not found"
        else:
            result["state"] = record_state(root)
    return result

def query(root: Path, question: str) -> dict[str, object]:
    if not shutil.which("graphify"):
        return {"ok": False, "error": "graphify is not installed"}
    if not (root / "graphify-out" / "graph.json").exists():
        return {"ok": False, "error": "graph does not exist; build it first"}
    rc, out = run(["graphify", "query", question], root)
    return {"ok": rc == 0, "command": ["graphify", "query", question], "output": out[-8000:]}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="action", required=True)
    sub.add_parser("status")
    build = sub.add_parser("build")
    build.add_argument("--force", action="store_true")
    q = sub.add_parser("query")
    q.add_argument("question")
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    if ns.action == "status":
        result = status(root)
        ok = bool(result.get("graph_exists")) and result.get("stale") is False
    elif ns.action == "build":
        result = build_or_update(root, force_build=ns.force)
        ok = bool(result.get("ok"))
    else:
        result = query(root, ns.question)
        ok = bool(result.get("ok"))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
