#!/usr/bin/env python3
"""Read-only integration health gate for GitHub, Graphify, Trivy, and graph freshness."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

import graph_provider
import github_traceability

ROOT = Path(__file__).resolve().parents[1]
TOOLCHAIN = ROOT / "config" / "toolchain.json"


def run(cmd: list[str], cwd: Path, timeout: int = 60) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
        return p.returncode, ((p.stdout or "") + "\n" + (p.stderr or "")).strip()
    except Exception as exc:
        return 127, str(exc)


def first_version(text: str) -> str | None:
    m = re.search(r"\b(\d+\.\d+(?:\.\d+)?)\b", text)
    return m.group(1) if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--tier", type=int, choices=[0,1,2,3], default=1)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    cfg = json.loads(TOOLCHAIN.read_text(encoding="utf-8"))

    result: dict[str, object] = {"root": str(root), "tier": ns.tier, "checks": {}, "problems": [], "warnings": []}
    checks: dict[str, object] = result["checks"]  # type: ignore[assignment]
    problems: list[str] = result["problems"]  # type: ignore[assignment]
    warnings: list[str] = result["warnings"]  # type: ignore[assignment]

    if not shutil.which("git"):
        problems.append("Git is required")
    else:
        rc, head = run(["git","rev-parse","HEAD"], root)
        rc2, remote = run(["git","remote","get-url","origin"], root)
        checks["git"] = {"ok": rc == 0, "head": head.strip() if rc == 0 else None, "origin": remote.strip() if rc2 == 0 else None}
        if rc != 0:
            problems.append("target is not a readable Git repository")

        gh_status = github_traceability.detect(root)
        checks["github"] = gh_status
        if gh_status.get("detected") and not gh_status.get("gh_installed"):
            warnings.append("GitHub remote detected but gh CLI is not installed")
        elif gh_status.get("detected") and not gh_status.get("authenticated"):
            warnings.append("GitHub remote detected but gh authentication is unavailable")

    graph = graph_provider.status(root)
    approved = cfg.get("graphify", {}).get("approved")
    installed = first_version(str(graph.get("provider_version") or ""))
    graph["approved_version"] = approved
    checks["graph_provider"] = graph
    checks["graph_state"] = {
        "present": graph.get("graph_exists"),
        "stale": graph.get("stale"),
        "fresh": graph.get("fresh"),
        "source_commit": graph.get("source_commit"),
        "graph_path": graph.get("graph_path"),
    }
    if installed and approved and installed != approved:
        warnings.append(f"Graphify {installed} differs from approved {approved}")
    if ns.tier >= 2:
        if not graph.get("available"):
            warnings.append("Graphify unavailable for a Tier 2+ change; use repository/source fallback impact analysis")
        elif not graph.get("graph_exists"):
            warnings.append("No local project graph exists; refresh it or use explicit fallback impact analysis")
        elif graph.get("stale"):
            warnings.append("project graph is stale relative to the current working tree")

    trivy = shutil.which("trivy")
    if trivy:
        rc, out = run([trivy, "--version"], root)
        checks["trivy"] = {"installed": True, "version": first_version(out), "command_ok": rc == 0}
    else:
        checks["trivy"] = {"installed": False}
        if ns.tier >= 2:
            warnings.append("Trivy unavailable for Tier 2+ baseline security scanning")

    if ns.tier == 3:
        # For critical work, missing key evidence providers are blockers unless a documented equivalent exists.
        if not trivy:
            problems.append("Tier 3 requires a security scanner or documented equivalent")
        if graph.get("stale"):
            problems.append("Tier 3 cannot rely on a stale graph")

    status = "FAIL" if problems else ("WARN" if warnings else "PASS")
    result["status"] = status
    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Integration Gate: {status}")
        for item in problems:
            print(f"ERROR: {item}")
        for item in warnings:
            print(f"WARN: {item}")

    return 2 if problems else (1 if ns.strict and warnings else 0)


if __name__ == "__main__":
    raise SystemExit(main())
