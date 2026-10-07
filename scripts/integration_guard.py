#!/usr/bin/env python3
"""Integration health checks with explicit delegation to the native publication scanner."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

import graph_provider
import github_traceability
import trivy_compat

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


def check(root: Path, tier: int, *, operation: str = "health", graph_use: str = "auto",
          release_target: str | None = None, release_report: Path | None = None,
          target_type: str = "fs", scanners: str = "vuln,secret") -> dict:
    root = root.resolve()
    cfg = json.loads(TOOLCHAIN.read_text(encoding="utf-8"))

    result: dict[str, object] = {
        "root": str(root), "tier": tier, "operation": operation, "graph_use": graph_use,
        "checks": {}, "problems": [], "warnings": [], "task_evidence_checked": False,
        "release_scan_verified": False, "publication_security_gate": "NOT_CHECKED",
    }
    checks: dict[str, object] = result["checks"]  # type: ignore[assignment]
    problems: list[str] = result["problems"]  # type: ignore[assignment]
    warnings: list[str] = result["warnings"]  # type: ignore[assignment]

    if operation not in {"health", "development", "publication"} or graph_use not in {"auto", "source", "authoritative"}:
        return dict(result, status="FAIL", problems=["unsupported operation or graph-use context"])
    if operation != "publication" and (release_target is not None or release_report is not None):
        return dict(result, status="FAIL", problems=["release inputs require explicit publication operation"])

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

    try:
        graph = graph_provider.status(root)
    except (OSError, ValueError, RuntimeError) as exc:
        graph = {"available": False, "fresh": False, "error": str(exc)}
    resolution = cfg.get("graphify", {}).get("resolution")
    installed = first_version(str(graph.get("provider_version") or ""))
    graph["resolution"] = resolution
    checks["graph_provider"] = graph
    checks["graph_state"] = {
        "present": graph.get("graph_exists"),
        "stale": graph.get("stale"),
        "fresh": graph.get("fresh"),
        "source_commit": graph.get("source_commit"),
        "graph_path": graph.get("graph_path"),
    }
    if installed:
        checks["graph_provider"]["runtime_version_detected"] = installed
    if graph_use == "authoritative" and not graph.get("fresh"):
        problems.append("authoritative graph use requires a present, fresh graph; refresh it or select source analysis")
    if tier >= 2:
        if not graph.get("available"):
            warnings.append("Graphify unavailable for a Tier 2+ change; use repository/source fallback impact analysis")
        elif not graph.get("graph_exists"):
            warnings.append("No local project graph exists; refresh it or use explicit fallback impact analysis")
        elif graph.get("stale"):
            warnings.append("project graph is stale; source analysis must supply impact evidence without relying on this graph")

    ready = trivy_compat.local_readiness()
    checks["trivy"] = {"installed": bool(shutil.which("trivy")), "version": ready.get("version"),
                       "command_ok": ready.get("gate") == "PASS", "preflight": ready}
    if ready.get("gate") != "PASS" and tier >= 2:
        warnings.append("native Trivy unavailable; safe development may continue with task-required native security checks")

    if operation == "publication":
        result["publication_security_gate"] = "BLOCK"
        if not release_target or release_report is None:
            problems.append("publication requires the final release target and a private release report path; tool presence is not scan evidence")
        elif release_report.expanduser().resolve().is_relative_to(root):
            problems.append("release report/cache must stay outside the project source")
        elif not problems:
            target = str((root / release_target).expanduser().resolve()) if target_type == "fs" else release_target
            scan = trivy_compat.release_scan(target, release_report, target_type=target_type, scanners=scanners)
            checks["publication_security"] = scan
            result["publication_security_gate"] = scan["gate"]
            result["release_scan_verified"] = scan.get("release_scan_verified") is True
            if scan["gate"] != "PASS" or not result["release_scan_verified"]:
                problems.append("native publication scan did not qualify; resolve its failures or required Head assessment")

    result["status"] = "FAIL" if problems else ("WARN" if warnings else "PASS")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--tier", type=int, choices=[0,1,2,3], default=1)
    ap.add_argument("--operation", choices=["health", "development", "publication"], default="health")
    ap.add_argument("--graph-use", choices=["auto", "source", "authoritative"], default="auto")
    ap.add_argument("--release-target", help="final delivery directory or immutable image; publication only")
    ap.add_argument("--release-report", type=Path, help="private Trivy report outside source; publication only")
    ap.add_argument("--target-type", choices=["fs", "image"], default="fs")
    ap.add_argument("--scanners", default="vuln,secret")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ns = ap.parse_args()
    result = check(Path(ns.root), ns.tier, operation=ns.operation, graph_use=ns.graph_use,
                   release_target=ns.release_target, release_report=ns.release_report,
                   target_type=ns.target_type, scanners=ns.scanners)
    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Integration {ns.operation}: {result['status']} (task evidence checked: false)")
        for item in result["problems"]:
            print(f"ERROR: {item}")
        for item in result["warnings"]:
            print(f"WARN: {item}")

    return 2 if result["problems"] else (1 if ns.strict and result["warnings"] else 0)


if __name__ == "__main__":
    raise SystemExit(main())
