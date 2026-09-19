#!/usr/bin/env python3
"""Run evidence-oriented integration checks for Git, Graphify, Trivy, and GitHub."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

def run(cmd: list[str], cwd: Path, timeout: int = 300) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def parse_github_remote(url: str) -> str | None:
    url = url.strip()
    patterns = [
        r"https?://github\.com/([^/]+/[^/]+?)(?:\.git)?$",
        r"git@github\.com:([^/]+/[^/]+?)(?:\.git)?$",
        r"ssh://git@github\.com/([^/]+/[^/]+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        m = re.match(pattern, url)
        if m:
            return m.group(1)
    return None

def graph_status(root: Path) -> dict[str, Any]:
    graph = root / "graphify-out" / "graph.json"
    state_file = root / ".vibe" / "graph-state.json"
    state: dict[str, Any] | None = None
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"installed": bool(shutil.which("graphify")), "graph_exists": graph.exists(), "state_error": str(exc), "stale": True}
    rc, head, _ = run(["git", "rev-parse", "HEAD"], root)
    source = state.get("source_commit") if state else None
    stale = None
    if graph.exists():
        stale = not bool(state and rc == 0 and source == head)
    return {
        "installed": bool(shutil.which("graphify")), "graph_exists": graph.exists(),
        "state_exists": state_file.exists(), "source_commit": source,
        "git_head": head if rc == 0 else None, "stale": stale,
    }

def count_trivy_findings(payload: dict[str, Any]) -> dict[str, int]:
    counts = {"vulnerabilities": 0, "misconfigurations": 0, "secrets": 0, "licenses": 0}
    for result in payload.get("Results") or []:
        counts["vulnerabilities"] += len(result.get("Vulnerabilities") or [])
        counts["misconfigurations"] += len(result.get("Misconfigurations") or [])
        counts["secrets"] += len(result.get("Secrets") or [])
        counts["licenses"] += len(result.get("Licenses") or [])
    return counts

def run_trivy(root: Path) -> dict[str, Any]:
    if not shutil.which("trivy"):
        return {"available": False, "ran": False, "warning": "trivy is not installed"}
    cmd = ["trivy", "fs", "--scanners", "vuln,misconfig,secret", "--format", "json", "--exit-code", "0", str(root)]
    rc, stdout, stderr = run(cmd, root, timeout=900)
    if rc != 0:
        return {"available": True, "ran": True, "ok": False, "command": cmd, "error": stderr or stdout}
    try:
        payload = json.loads(stdout)
    except Exception as exc:
        return {"available": True, "ran": True, "ok": False, "command": cmd, "error": f"invalid Trivy JSON: {exc}"}
    return {"available": True, "ran": True, "ok": True, "command": cmd, "counts": count_trivy_findings(payload)}

def github_status(root: Path, live: bool) -> dict[str, Any]:
    rc, remote, err = run(["git", "remote", "get-url", "origin"], root)
    if rc != 0:
        return {"remote": None, "repository": None, "live_checked": False, "warning": err or "no origin remote"}
    repo = parse_github_remote(remote)
    result: dict[str, Any] = {"remote": remote, "repository": repo, "live_checked": False}
    if not live:
        return result
    if not repo:
        result["warning"] = "origin is not a recognized github.com repository"
        return result
    if not shutil.which("gh"):
        result["warning"] = "gh CLI is not installed; remote detection succeeded but live GitHub check was skipped"
        return result
    rc, stdout, stderr = run(["gh", "repo", "view", repo, "--json", "nameWithOwner,url,defaultBranchRef"], root)
    result["live_checked"] = True
    result["ok"] = rc == 0
    if rc == 0:
        try: result["metadata"] = json.loads(stdout)
        except Exception: result["metadata_raw"] = stdout
    else:
        result["error"] = stderr or stdout
    return result

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--tier", type=int, choices=[0,1,2,3], default=1)
    ap.add_argument("--security", action="store_true")
    ap.add_argument("--github-live", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    evidence: dict[str, Any] = {"root": str(root), "tier": ns.tier}
    problems: list[str] = []
    warnings: list[str] = []
    if not shutil.which("git"):
        problems.append("git is required")
        evidence["git"] = {"installed": False}
    else:
        rc, inside, err = run(["git", "rev-parse", "--is-inside-work-tree"], root)
        evidence["git"] = {"installed": True, "working_tree": rc == 0 and inside == "true"}
        if rc != 0 or inside != "true":
            problems.append(err or "target is not a Git working tree")
    graph = graph_status(root) if evidence["git"].get("working_tree") else {"installed": bool(shutil.which("graphify"))}
    evidence["graphify"] = graph
    if ns.tier >= 2:
        if not graph.get("installed"):
            warnings.append("Graphify is recommended for Tier 2+ impact analysis but is not installed")
        elif not graph.get("graph_exists"):
            warnings.append("Tier 2+ project has no Graphify graph yet")
        elif graph.get("stale"):
            problems.append("project graph is stale for Tier 2+ work")
    if ns.security:
        trivy = run_trivy(root)
        evidence["trivy"] = trivy
        if not trivy.get("available"):
            warnings.append("Trivy security scan requested but Trivy is not installed")
        elif not trivy.get("ok"):
            problems.append("Trivy scan failed")
        else:
            counts = trivy.get("counts") or {}
            if counts.get("secrets", 0):
                problems.append(f"Trivy found {counts['secrets']} secret finding(s)")
            if counts.get("vulnerabilities", 0) or counts.get("misconfigurations", 0):
                warnings.append("Trivy reported vulnerabilities/misconfigurations; review scan evidence before release")
    else:
        evidence["trivy"] = {"available": bool(shutil.which("trivy")), "ran": False}
    evidence["github"] = github_status(root, ns.github_live) if evidence["git"].get("working_tree") else {"live_checked": False}
    if ns.github_live and evidence["github"].get("live_checked") and not evidence["github"].get("ok", True):
        warnings.append("live GitHub metadata check failed")
    result = {"ok": not problems and (not ns.strict or not warnings), "problems": problems, "warnings": warnings, "evidence": evidence}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
