#!/usr/bin/env python3
"""Prevent Vibe Coding / analysis artifacts from entering the project repository."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

FORBIDDEN_PREFIXES = (
    ".vibe/",
    ".vibe-coding/",
    "graphify-out/",
    ".trivy/",
    "benchmark-results/",
    "coverage/",
    "htmlcov/",
    "test-results/",
    "playwright-report/",
    "allure-results/",
)

FORBIDDEN_FILES = {
    "graphify-compat.json",
    "trivy-report.json",
    "trivy-report.sarif",
}


def git(root: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    return p.returncode, (p.stdout or p.stderr).strip()


def is_forbidden(path: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    return normalized in FORBIDDEN_FILES or any(normalized.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict-excludes", action="store_true")
    ns = ap.parse_args()
    root = Path(ns.root).resolve()

    rc, inside = git(root, "rev-parse", "--is-inside-work-tree")
    if rc != 0 or inside != "true":
        raise SystemExit("repository purity gate requires a Git working tree")

    _, tracked_text = git(root, "ls-files")
    _, staged_text = git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR")

    tracked = sorted({p for p in tracked_text.splitlines() if p and is_forbidden(p)})
    staged = sorted({p for p in staged_text.splitlines() if p and is_forbidden(p)})

    git_dir_rc, git_dir_text = git(root, "rev-parse", "--git-dir")
    exclude_ok = False
    exclude_path = None
    if git_dir_rc == 0:
        git_dir = Path(git_dir_text)
        if not git_dir.is_absolute():
            git_dir = (root / git_dir).resolve()
        exclude_path = git_dir / "info" / "exclude"
        if exclude_path.exists():
            content = exclude_path.read_text(encoding="utf-8")
            exclude_ok = "Vibe Coding Skill local-only artifacts" in content

    problems: list[str] = []
    warnings: list[str] = []
    if tracked:
        problems.append("tool-generated artifacts are already tracked")
    if staged:
        problems.append("tool-generated artifacts are staged")
    if not exclude_ok:
        message = "local Git exclude block is not configured; run local_workspace.py init"
        if ns.strict_excludes:
            problems.append(message)
        else:
            warnings.append(message)

    result = {
        "status": "BLOCK" if problems else ("WARN" if warnings else "PASS"),
        "tracked_forbidden": tracked,
        "staged_forbidden": staged,
        "local_excludes_configured": exclude_ok,
        "git_info_exclude": str(exclude_path) if exclude_path else None,
        "problems": problems,
        "warnings": warnings,
    }

    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Repository Purity: {result['status']}")
        for item in problems:
            print(f"ERROR: {item}")
        for item in warnings:
            print(f"WARN: {item}")
    return 2 if problems else (1 if ns.strict_excludes and warnings else 0)


if __name__ == "__main__":
    raise SystemExit(main())
