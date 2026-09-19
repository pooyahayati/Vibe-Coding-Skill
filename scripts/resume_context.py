#!/usr/bin/env python3
"""Build a bounded, local recovery context without relying on chat history."""

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

DOC_ORDER = [
    "STATUS.md",
    "PROJECT.md",
    "ROADMAP.md",
    "ARCHITECTURE.md",
    "PROJECT_GRAPH.md",
    "AGENTS.md",
    "README.md",
]

MANIFESTS = [
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "pnpm-lock.yaml",
    "package-lock.json",
    "yarn.lock",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Dockerfile",
    "compose.yaml",
    "docker-compose.yml",
]


def git(root: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    return p.returncode, (p.stdout or p.stderr).strip()


def read_bounded(path: Path, max_bytes: int) -> dict[str, Any]:
    raw = path.read_bytes()
    truncated = len(raw) > max_bytes
    data = raw[:max_bytes]
    text = data.decode("utf-8", "replace")
    if truncated:
        text += "\n\n[TRUNCATED BY RESUME CONTEXT]"
    return {
        "path": str(path),
        "size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "truncated": truncated,
        "content": text,
    }


def load_local_json(root: Path, name: str) -> tuple[dict[str, Any] | None, str | None]:
    path = local_workspace.state_path(root, name, create=False)
    if not path.exists():
        return None, None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            return None, f"{name} is not a JSON object"
        return value, None
    except Exception as exc:
        return None, f"{name} is unreadable: {exc}"


def build_context(root: Path, max_bytes_per_doc: int = 16000) -> dict[str, Any]:
    root = root.resolve()
    local_workspace.ensure_git_repo(root)

    warnings: list[str] = []
    docs: list[dict[str, Any]] = []
    for name in DOC_ORDER:
        path = root / name
        if path.exists() and path.is_file():
            doc = read_bounded(path, max_bytes_per_doc)
            doc["name"] = name
            docs.append(doc)

    if not docs:
        warnings.append("no durable project documents were found; inspect source/manifests before continuing")
    elif not any(d["name"] in {"STATUS.md", "PROJECT.md", "README.md"} for d in docs):
        warnings.append("core resume documents are missing")

    rc, head = git(root, "rev-parse", "HEAD")
    if rc != 0:
        raise RuntimeError("cannot resolve Git HEAD")
    _, branch = git(root, "branch", "--show-current")
    _, status = git(root, "status", "--porcelain")
    _, recent = git(root, "log", "-5", "--pretty=format:%h %s")
    _, origin = git(root, "remote", "get-url", "origin")

    if status:
        warnings.append("working tree has uncommitted changes; preserve and inspect them before modifying")

    project_state, project_state_error = load_local_json(root, "project-state.json")
    project_meta, project_meta_error = load_local_json(root, "project.json")
    for error in (project_state_error, project_meta_error):
        if error:
            warnings.append(error)

    graph = graph_provider.status(root)
    if graph.get("stale"):
        warnings.append("local project graph is stale; refresh it before relying on graph evidence")

    present_manifests = [name for name in MANIFESTS if (root / name).exists()]

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "readiness": "WARN" if warnings else "PASS",
        "warnings": warnings,
        "resume_order": DOC_ORDER + ["Git/GitHub", "source", "tests"],
        "git": {
            "head": head,
            "branch": branch or None,
            "dirty": bool(status),
            "status_porcelain": status.splitlines(),
            "origin": origin or None,
            "recent_commits": recent.splitlines() if recent else [],
        },
        "github": {
            "repository": github_traceability.github_slug(root),
            "network_checked": False,
        },
        "graph": graph,
        "local_state": {
            "workspace": str(local_workspace.project_workspace(root, create=False)),
            "project_state": project_state,
            "project": project_meta,
        },
        "manifests": present_manifests,
        "documents": docs,
        "instruction": (
            "Resume from repository and local evidence only. Do not assume chat history. "
            "Resolve contradictions in favor of current repository state, verified tests, "
            "approved architecture, and explicit user decisions."
        ),
    }


def render_markdown(context: dict[str, Any]) -> str:
    git_state = context["git"]
    lines = [
        "# Resume Context",
        "",
        f"- Readiness: {context['readiness']}",
        f"- Branch: {git_state.get('branch')}",
        f"- HEAD: {git_state.get('head')}",
        f"- Dirty: {git_state.get('dirty')}",
        f"- GitHub: {context['github'].get('repository')}",
        f"- Graph fresh: {context['graph'].get('fresh')}",
        "",
        "## Resume order",
        "",
        " -> ".join(context["resume_order"]),
        "",
    ]
    if context["warnings"]:
        lines += ["## Warnings", ""]
        lines += [f"- {item}" for item in context["warnings"]]
        lines.append("")

    lines += ["## Recent commits", ""]
    lines += [f"- {item}" for item in git_state.get("recent_commits", [])] or ["- None"]
    lines.append("")

    for doc in context["documents"]:
        lines += [
            f"## {doc['name']}",
            "",
            "----- BEGIN DOCUMENT -----",
            doc["content"],
            "----- END DOCUMENT -----",
            "",
        ]

    lines += ["## Recovery instruction", "", context["instruction"], ""]
    return "\n".join(lines)


def write_local(root: Path, context: dict[str, Any]) -> dict[str, str]:
    local_workspace.initialize(root)
    json_path = local_workspace.state_path(root, "resume-context.json", create=True)
    md_path = local_workspace.state_path(root, "resume-context.md", create=True)
    json_path.write_text(json.dumps(context, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(context), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--max-bytes-per-doc", type=int, default=16000)
    ap.add_argument("--write-local", action="store_true")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    root = Path(ns.root).resolve()

    try:
        context = build_context(root, ns.max_bytes_per_doc)
        if ns.write_local:
            context["written"] = write_local(root, context)
    except RuntimeError as exc:
        if ns.json:
            print(json.dumps({"readiness": "BLOCK", "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}")
        return 2

    if ns.json:
        print(json.dumps(context, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(context))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
