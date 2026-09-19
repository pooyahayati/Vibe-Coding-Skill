#!/usr/bin/env python3
"""GitHub traceability adapter with safe defaults and local state."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import local_workspace


def run(cmd: list[str], cwd: Path, timeout: int = 120) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
        return p.returncode, ((p.stdout or "") + "\n" + (p.stderr or "")).strip()
    except Exception as exc:
        return 127, str(exc)


def git(root: Path, *args: str) -> tuple[int, str]:
    return run(["git", *args], root, timeout=60)


def github_slug(root: Path) -> str | None:
    rc, remote = git(root, "remote", "get-url", "origin")
    if rc != 0:
        return None
    remote = remote.strip()
    for pattern in (
        r"github\.com[:/](?P<slug>[^\s]+?)(?:\.git)?$",
        r"https://github\.com/(?P<slug>[^\s]+?)(?:\.git)?$",
    ):
        match = re.search(pattern, remote)
        if match:
            return match.group("slug").removesuffix(".git")
    return None


def detect(root: Path) -> dict[str, Any]:
    slug = github_slug(root)
    gh = shutil.which("gh")
    authenticated = False
    if gh and slug:
        rc, _ = run([gh, "auth", "status"], root, timeout=60)
        authenticated = rc == 0
    return {
        "detected": bool(slug),
        "repository": slug,
        "gh_installed": bool(gh),
        "authenticated": authenticated,
    }


def require_gh(root: Path) -> tuple[str, str]:
    info = detect(root)
    if not info["detected"]:
        raise RuntimeError("GitHub remote not detected")
    if not info["gh_installed"]:
        raise RuntimeError("gh CLI is not installed")
    if not info["authenticated"]:
        raise RuntimeError("gh CLI is not authenticated")
    return shutil.which("gh") or "gh", str(info["repository"])


def gh_json(root: Path, args: list[str]) -> Any:
    gh, _ = require_gh(root)
    rc, out = run([gh, *args], root)
    if rc != 0:
        raise RuntimeError(out or f"gh {' '.join(args)} failed")
    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"gh returned non-JSON output: {out[-1000:]}") from exc


def snapshot(root: Path, limit: int = 100) -> dict[str, Any]:
    gh, slug = require_gh(root)
    issues = gh_json(
        root,
        ["issue", "list", "--state", "all", "--limit", str(limit), "--json",
         "number,title,state,url,updatedAt,labels,milestone"],
    )
    prs = gh_json(
        root,
        ["pr", "list", "--state", "all", "--limit", str(limit), "--json",
         "number,title,state,isDraft,mergedAt,url,headRefName,baseRefName,updatedAt"],
    )
    releases: Any = []
    rc, out = run(
        [gh, "release", "list", "--limit", str(limit), "--json",
         "tagName,name,isDraft,isPrerelease,publishedAt"],
        root,
    )
    if rc == 0:
        try:
            releases = json.loads(out)
        except json.JSONDecodeError:
            releases = []
    result = {
        "schema_version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "repository": slug,
        "issues": issues,
        "pull_requests": prs,
        "releases": releases,
    }
    path = local_workspace.state_path(root, "github-snapshot.json", create=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    result["state_path"] = str(path)
    return result


def traceability_path(root: Path, create: bool = False) -> Path:
    return local_workspace.state_path(root, "traceability.json", create=create)


def load_traceability(root: Path) -> dict[str, Any]:
    path = traceability_path(root, create=False)
    if not path.exists():
        return {"schema_version": 1, "requirements": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def record(
    root: Path,
    requirement_id: str,
    issue: int | None = None,
    pr: int | None = None,
    test: str | None = None,
    release: str | None = None,
) -> dict[str, Any]:
    local_workspace.initialize(root)
    data = load_traceability(root)
    requirements = data.setdefault("requirements", {})
    entry = requirements.setdefault(requirement_id, {"tests": []})
    if issue is not None:
        entry["issue"] = issue
    if pr is not None:
        entry["pr"] = pr
    if release:
        entry["release"] = release
    if test and test not in entry.setdefault("tests", []):
        entry["tests"].append(test)
    entry["updated_at"] = datetime.now(timezone.utc).isoformat()
    data["updated_at"] = entry["updated_at"]
    path = traceability_path(root, create=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return {"requirement_id": requirement_id, "entry": entry, "state_path": str(path)}


def verify_entry(root: Path, requirement_id: str, entry: dict[str, Any]) -> dict[str, Any]:
    gh, slug = require_gh(root)
    failures: list[str] = []
    warnings: list[str] = []
    evidence: dict[str, Any] = {}

    issue_number = entry.get("issue")
    issue = None
    if issue_number is not None:
        rc, out = run([gh, "api", f"repos/{slug}/issues/{issue_number}"], root)
        if rc != 0:
            failures.append(f"issue #{issue_number} could not be verified")
        else:
            issue = json.loads(out)
            evidence["issue"] = {
                "number": issue.get("number"),
                "state": issue.get("state"),
                "url": issue.get("html_url"),
            }
            haystack = f"{issue.get('title','')}\n{issue.get('body','')}"
            if requirement_id not in haystack:
                warnings.append(f"{requirement_id} is not present in issue #{issue_number} title/body")

    pr_number = entry.get("pr")
    if pr_number is not None:
        rc, out = run([gh, "api", f"repos/{slug}/pulls/{pr_number}"], root)
        if rc != 0:
            failures.append(f"PR #{pr_number} could not be verified")
        else:
            pr = json.loads(out)
            evidence["pr"] = {
                "number": pr.get("number"),
                "state": pr.get("state"),
                "merged_at": pr.get("merged_at"),
                "url": pr.get("html_url"),
            }
            if issue_number is not None:
                body = pr.get("body") or ""
                issue_url = str(issue.get("html_url") or "") if issue else ""
                if f"#{issue_number}" not in body and (not issue_url or issue_url not in body):
                    warnings.append(f"PR #{pr_number} does not visibly reference issue #{issue_number}")

    release_tag = entry.get("release")
    if release_tag:
        rc, out = run([gh, "api", f"repos/{slug}/releases/tags/{release_tag}"], root)
        if rc != 0:
            failures.append(f"release {release_tag!r} could not be verified")
        else:
            release = json.loads(out)
            evidence["release"] = {
                "tag": release.get("tag_name"),
                "published_at": release.get("published_at"),
                "url": release.get("html_url"),
            }

    return {
        "requirement_id": requirement_id,
        "status": "FAIL" if failures else ("WARN" if warnings else "PASS"),
        "failures": failures,
        "warnings": warnings,
        "evidence": evidence,
        "tests": entry.get("tests", []),
    }


def verify(root: Path, requirement_id: str | None = None) -> dict[str, Any]:
    data = load_traceability(root)
    requirements = data.get("requirements", {})
    selected = {requirement_id: requirements.get(requirement_id)} if requirement_id else requirements
    results = []
    for rid, entry in selected.items():
        if not entry:
            results.append({
                "requirement_id": rid,
                "status": "FAIL",
                "failures": ["requirement is not recorded"],
                "warnings": [],
                "evidence": {},
                "tests": [],
            })
        else:
            results.append(verify_entry(root, rid, entry))
    overall = "FAIL" if any(x["status"] == "FAIL" for x in results) else (
        "WARN" if any(x["status"] == "WARN" for x in results) else "PASS"
    )
    return {"status": overall, "results": results}


def issue_plan(
    root: Path,
    title: str,
    body: str,
    labels: list[str],
    milestone: str | None,
    apply: bool,
) -> dict[str, Any]:
    gh, slug = require_gh(root)
    cmd = [gh, "issue", "create", "--repo", slug, "--title", title, "--body", body]
    for label in labels:
        cmd.extend(["--label", label])
    if milestone:
        cmd.extend(["--milestone", milestone])
    if not apply:
        return {
            "applied": False,
            "repository": slug,
            "command": " ".join(shlex.quote(x) for x in cmd),
        }
    rc, out = run(cmd, root)
    if rc != 0:
        raise RuntimeError(out or "failed to create issue")
    return {"applied": True, "repository": slug, "issue_url": out.splitlines()[-1].strip()}


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("status")
    p.add_argument("--root", default=".")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("snapshot")
    p.add_argument("--root", default=".")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("record")
    p.add_argument("requirement_id")
    p.add_argument("--root", default=".")
    p.add_argument("--issue", type=int)
    p.add_argument("--pr", type=int)
    p.add_argument("--test")
    p.add_argument("--release")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("verify")
    p.add_argument("--root", default=".")
    p.add_argument("--requirement-id")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("create-issue")
    p.add_argument("--root", default=".")
    p.add_argument("--title", required=True)
    p.add_argument("--body", required=True)
    p.add_argument("--label", action="append", default=[])
    p.add_argument("--milestone")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--json", action="store_true")

    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    try:
        if ns.command == "status":
            result = detect(root)
        elif ns.command == "snapshot":
            result = snapshot(root, ns.limit)
        elif ns.command == "record":
            result = record(root, ns.requirement_id, ns.issue, ns.pr, ns.test, ns.release)
        elif ns.command == "verify":
            result = verify(root, ns.requirement_id)
        else:
            result = issue_plan(root, ns.title, ns.body, ns.label, ns.milestone, ns.apply)
    except (RuntimeError, json.JSONDecodeError) as exc:
        if getattr(ns, "json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}")
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
