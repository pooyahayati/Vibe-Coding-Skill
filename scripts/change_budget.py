#!/usr/bin/env python3
"""Summarize Git diff size and risk-sensitive paths."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

SENSITIVE = {
    "auth_security": re.compile(r"(^|/)(auth|security|permissions?|iam)(/|\.|$)", re.I),
    "migrations": re.compile(r"(^|/)(migrations?|schema)(/|\.|$)", re.I),
    "infra": re.compile(r"(Dockerfile|compose\.ya?ml|terraform|\.tf$|k8s|kubernetes|helm)", re.I),
    "ci": re.compile(r"(^|/)\.github/workflows/|gitlab-ci|Jenkinsfile", re.I),
    "dependencies": re.compile(
        r"(package(-lock)?\.json|pyproject\.toml|uv\.lock|requirements.*\.txt|Cargo\.toml|Cargo\.lock|go\.mod|go\.sum|pom\.xml|build\.gradle)",
        re.I,
    ),
}


def git(root: Path, args: list[str]) -> str:
    p = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    if p.returncode:
        raise SystemExit((p.stderr or p.stdout).strip())
    return p.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--base", default="HEAD~1")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    root = Path(ns.root).resolve()

    numstat = git(root, ["diff", "--numstat", ns.base, ns.head])
    files: list[dict[str, object]] = []
    added_total = deleted_total = 0
    flags: dict[str, list[str]] = {k: [] for k in SENSITIVE}

    for line in numstat.splitlines():
        if not line.strip():
            continue
        added, deleted, path = line.split("\t", 2)
        a = int(added) if added.isdigit() else 0
        d = int(deleted) if deleted.isdigit() else 0
        added_total += a
        deleted_total += d
        files.append({"path": path, "added": a, "deleted": d})
        for name, rx in SENSITIVE.items():
            if rx.search(path):
                flags[name].append(path)

    file_count = len(files)
    churn = added_total + deleted_total

    if any(flags[k] for k in ("auth_security", "migrations", "infra")):
        tier = "significant"
    elif file_count > 15 or churn > 800:
        tier = "large"
    elif file_count <= 3 and churn <= 120:
        tier = "tiny"
    else:
        tier = "standard"

    result = {
        "base": ns.base,
        "head": ns.head,
        "files_changed": file_count,
        "lines_added": added_total,
        "lines_deleted": deleted_total,
        "churn": churn,
        "suggested_change_class": tier,
        "sensitive_paths": {k: v for k, v in flags.items() if v},
        "files": files,
    }

    if ns.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Change class: {tier}")
        print(f"Files: {file_count}  +{added_total} -{deleted_total}  churn={churn}")
        for name, paths in result["sensitive_paths"].items():
            print(f"{name}: {', '.join(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
