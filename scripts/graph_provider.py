#!/usr/bin/env python3
"""Provider-neutral project intelligence graph contract with a Graphify adapter."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import local_workspace

PROVIDER = "graphify"
PROVIDER_OUTPUT = "graphify-out"


def run(cmd: list[str], cwd: Path, timeout: int = 600) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
        return p.returncode, ((p.stdout or "") + "\n" + (p.stderr or "")).strip()
    except Exception as exc:
        return 127, str(exc)


def git(root: Path, *args: str) -> tuple[int, str]:
    return run(["git", *args], root, timeout=60)


def head(root: Path) -> str | None:
    rc, out = git(root, "rev-parse", "HEAD")
    return out.strip() if rc == 0 else None


def provider_version(root: Path) -> str | None:
    executable = shutil.which(PROVIDER)
    if not executable:
        return None
    rc, out = run([executable, "--version"], root, timeout=60)
    if rc != 0:
        return None
    return out.splitlines()[0].strip() if out.strip() else "installed"


def untracked_files(root: Path) -> list[str]:
    p = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if p.returncode != 0:
        return []
    return [x.decode("utf-8", "surrogateescape") for x in p.stdout.split(b"\0") if x]


def working_tree_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    current_head = head(root) or ""
    digest.update(current_head.encode("utf-8"))
    diff = subprocess.run(
        ["git", "diff", "--binary", "HEAD", "--", "."],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if diff.returncode == 0:
        digest.update(diff.stdout)
    for rel in sorted(untracked_files(root)):
        path = root / rel
        digest.update(rel.encode("utf-8", "surrogateescape"))
        try:
            if path.is_symlink():
                digest.update(os.readlink(path).encode("utf-8", "surrogateescape"))
            elif path.is_file():
                digest.update(path.read_bytes())
        except OSError:
            digest.update(b"<unreadable>")
    return digest.hexdigest()


def graph_root(root: Path, create: bool = False) -> Path:
    return local_workspace.artifact_path(root, "graph", PROVIDER_OUTPUT, create=create)


def graph_json(root: Path) -> Path:
    return graph_root(root, create=False) / "graph.json"


def graph_state_path(root: Path, create: bool = False) -> Path:
    return local_workspace.state_path(root, "graph-state.json", create=create)


def load_state(root: Path) -> dict[str, Any] | None:
    path = graph_state_path(root, create=False)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def status(root: Path) -> dict[str, Any]:
    root = root.resolve()
    local_workspace.ensure_git_repo(root)
    state = load_state(root)
    current_head = head(root)
    fingerprint = working_tree_fingerprint(root)
    graph_path = graph_json(root)
    state_head = state.get("source_commit") if state else None
    state_fingerprint = state.get("working_tree_fingerprint") if state else None
    fresh = bool(
        state
        and graph_path.exists()
        and state_head == current_head
        and state_fingerprint == fingerprint
    )
    return {
        "provider": PROVIDER,
        "available": bool(shutil.which(PROVIDER)),
        "provider_version": provider_version(root),
        "graph_exists": graph_path.exists(),
        "graph_path": str(graph_path),
        "state_path": str(graph_state_path(root, create=False)),
        "source_commit": state_head,
        "current_commit": current_head,
        "source_dirty": state.get("source_dirty") if state else None,
        "fresh": fresh,
        "stale": bool(state and graph_path.exists() and not fresh),
    }


def source_files(root: Path) -> list[str]:
    p = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if p.returncode != 0:
        raise RuntimeError("cannot enumerate project files")
    return sorted(
        {x.decode("utf-8", "surrogateescape") for x in p.stdout.split(b"\0") if x}
    )


def prepare_shadow(root: Path, include_previous_graph: bool) -> Path:
    workspace = local_workspace.project_workspace(root, create=True)
    shadow = workspace / "worktrees" / "graph-shadow"
    if shadow.exists():
        shutil.rmtree(shadow)
    shadow.mkdir(parents=True, exist_ok=True)
    for rel in source_files(root):
        src = root / rel
        if not src.exists() and not src.is_symlink():
            continue
        dst = shadow / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_symlink():
            try:
                dst.symlink_to(os.readlink(src))
            except OSError:
                pass
        elif src.is_file():
            shutil.copy2(src, dst)
    previous = graph_root(root, create=False)
    if include_previous_graph and previous.exists():
        shutil.copytree(previous, shadow / PROVIDER_OUTPUT)
    return shadow


def persist_provider_output(root: Path, shadow: Path) -> Path:
    generated = shadow / PROVIDER_OUTPUT
    graph = generated / "graph.json"
    if not graph.exists():
        raise RuntimeError("Graphify completed but graphify-out/graph.json was not produced")
    destination = graph_root(root, create=True)
    tmp = destination.parent / f"{PROVIDER_OUTPUT}.tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(generated, tmp)
    if destination.exists():
        shutil.rmtree(destination)
    tmp.rename(destination)
    return destination / "graph.json"


def refresh(root: Path, mode: str = "auto", keep_shadow: bool = False) -> dict[str, Any]:
    root = root.resolve()
    local_workspace.initialize(root)
    executable = shutil.which(PROVIDER)
    if not executable:
        raise RuntimeError("Graphify is not installed")
    previous = graph_root(root, create=False)
    if mode == "auto":
        mode = "incremental" if previous.exists() else "full"
    if mode not in {"full", "incremental"}:
        raise ValueError("mode must be auto, full, or incremental")
    shadow = prepare_shadow(root, include_previous_graph=(mode == "incremental"))
    if mode == "incremental" and not (shadow / PROVIDER_OUTPUT / "graph.json").exists():
        mode = "full"
    command = (
        [executable, "update", "."]
        if mode == "incremental"
        else [executable, "extract", ".", "--code-only", "--no-viz"]
    )
    rc, out = run(command, shadow)
    if rc != 0:
        if not keep_shadow:
            shutil.rmtree(shadow, ignore_errors=True)
        raise RuntimeError(f"Graphify {mode} failed: {out[-2000:]}")
    path = persist_provider_output(root, shadow)
    current_head = head(root)
    fingerprint = working_tree_fingerprint(root)
    dirty_rc, dirty_out = git(root, "status", "--porcelain")
    state = {
        "schema_version": 2,
        "provider": PROVIDER,
        "provider_version": provider_version(root),
        "source_commit": current_head,
        "working_tree_fingerprint": fingerprint,
        "source_dirty": bool(dirty_out.strip()) if dirty_rc == 0 else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "graph_path": str(path),
    }
    state_path = graph_state_path(root, create=True)
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    if not keep_shadow:
        shutil.rmtree(shadow, ignore_errors=True)
    return {
        "ok": True,
        "provider": PROVIDER,
        "mode": mode,
        "graph_path": str(path),
        "state_path": str(state_path),
        "source_commit": current_head,
        "fresh": True,
    }


def graph_command(
    root: Path,
    operation: str,
    values: list[str],
    allow_stale: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    current = status(root)
    if not current["graph_exists"]:
        raise RuntimeError("no local graph exists; run graph_provider.py refresh")
    if not current["fresh"] and not allow_stale:
        raise RuntimeError("local graph is stale; refresh it or pass --allow-stale")
    executable = shutil.which(PROVIDER)
    if not executable:
        raise RuntimeError("Graphify is not installed")
    cmd = [executable, operation, *values, "--graph", str(graph_json(root))]
    rc, out = run(cmd, root, timeout=180)
    if rc != 0:
        raise RuntimeError(f"Graphify {operation} failed: {out[-2000:]}")
    return {
        "operation": operation,
        "fresh": current["fresh"],
        "graph_path": str(graph_json(root)),
        "output": out,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("status")
    p.add_argument("--root", default=".")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("refresh")
    p.add_argument("--root", default=".")
    p.add_argument("--mode", choices=["auto", "full", "incremental"], default="auto")
    p.add_argument("--keep-shadow", action="store_true")
    p.add_argument("--json", action="store_true")

    for name, count in (("query", 1), ("explain", 1), ("path", 2)):
        p = sub.add_parser(name)
        p.add_argument("values", nargs=count)
        p.add_argument("--root", default=".")
        p.add_argument("--allow-stale", action="store_true")
        p.add_argument("--json", action="store_true")

    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    try:
        if ns.command == "status":
            result = status(root)
        elif ns.command == "refresh":
            result = refresh(root, ns.mode, ns.keep_shadow)
        else:
            result = graph_command(root, ns.command, list(ns.values), ns.allow_stale)
    except (RuntimeError, ValueError) as exc:
        if getattr(ns, "json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}")
        return 2
    if getattr(ns, "json", False):
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif ns.command in {"query", "explain", "path"}:
        print(result["output"])
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
