#!/usr/bin/env python3
"""Summarize Git diff size and risk-sensitive paths."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import hashlib
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


def verification_changes(root: Path, baseline: dict) -> dict:
    """Compare accepted check definitions, not the implementation-time receipt.

    Any edit needs Head review: patterns can explain signals but cannot prove
    equivalent assertions across languages. Explicit paths include check config.
    """
    import evidence_capture as capture
    import behavior_contract as behavior
    revision = baseline["revision"]
    paths = [capture.relative(p) for p in baseline["paths"]]
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision):
        raise ValueError("verification baseline needs an exact accepted commit")
    def read(*args):
        p = subprocess.run(["git", *args], cwd=root, capture_output=True)
        if p.returncode:
            raise ValueError("verification baseline unavailable; reconcile before completion")
        return p.stdout
    read("cat-file", "-e", revision + "^{commit}")
    entries = read("--literal-pathspecs", "ls-tree", "-r", "-z", revision, "--", *paths).split(b"\0")
    before = {}
    total = 0
    def content_digest(raw):
        # Ignore only UTF-8 checkout CRLF differences, not index flags/filters.
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            pass
        else:
            if b"\0" not in raw:
                raw = raw.replace(b"\r\n", b"\n")
        return hashlib.sha256(raw).hexdigest()
    for entry in filter(None, entries):
        metadata, name = entry.split(b"\t", 1)
        mode, kind, oid = metadata.split()
        if kind != b"blob" or mode not in (b"100644", b"100755"):
            raise ValueError("unsupported verification baseline entry")
        total += int(read("cat-file", "-s", oid.decode()))
        if len(before) >= capture.MAX_FILES or total > capture.MAX_BYTES:
            raise ValueError("verification baseline exceeds collection limits")
        before[name.decode("utf-8")] = content_digest(read("cat-file", "blob", oid.decode()))
    after_rows = capture.snapshot(root, paths, [], require_file=False)
    after = {}
    for row in after_rows:
        if "sha256" in row:
            raw = capture.checked_path(root, root / row["path"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != row["sha256"]:
                raise ValueError("check definition changed during integrity review")
            after[row["path"]] = content_digest(raw)
    changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
    return {"changed_paths": changed, "baseline_empty": not before,
            "sha256": behavior.digest({"baseline": baseline, "before": before, "after": after_rows})}


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
    ap.add_argument("--check-path", action="append", default=[], help="Accepted check/config path; compare --base to working tree")
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
    if ns.check_path:
        revision = git(root, ["rev-parse", ns.base + "^{commit}"]).strip()
        result["verification_review"] = verification_changes(root, {"revision": revision, "paths": ns.check_path})

    if ns.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Change class: {tier}")
        print(f"Files: {file_count}  +{added_total} -{deleted_total}  churn={churn}")
        for name, paths in result["sensitive_paths"].items():
            print(f"{name}: {', '.join(paths)}")
        if "verification_review" in result:
            print("Verification review: " + json.dumps(result["verification_review"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
