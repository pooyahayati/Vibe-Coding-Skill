#!/usr/bin/env python3
"""Risk-aware project gate integrating Git, Graphify, Trivy, and GitHub remote evidence."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_classifier():
    path = HERE / "risk_classifier.py"
    spec = importlib.util.spec_from_file_location("risk_classifier", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def run(cmd: list[str], cwd: Path, timeout: int = 300) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    return p.returncode, ((p.stdout or "") + "\n" + (p.stderr or "")).strip()


def git(root: Path, *args: str) -> str | None:
    rc, out = run(["git", *args], root)
    return out.strip() if rc == 0 else None


def graph_status(root: Path, head: str | None) -> dict[str, object]:
    state_path = root / ".vibe" / "graph-state.json"
    state = None
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"available": bool(shutil.which("graphify")), "state_valid": False, "error": str(exc)}
    source_commit = state.get("source_commit") if state else None
    return {
        "available": bool(shutil.which("graphify")),
        "state_file": str(state_path) if state_path.exists() else None,
        "source_commit": source_commit,
        "fresh": bool(head and source_commit == head),
    }


def trivy_summary(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"ran": False, "report": None}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ran": True, "report": str(path), "parse_error": str(exc)}
    severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    secrets = 0
    misconfigs = 0
    for result in data.get("Results", []) or []:
        for vuln in result.get("Vulnerabilities", []) or []:
            key = str(vuln.get("Severity") or "UNKNOWN").upper()
            severity[key] = severity.get(key, 0) + 1
        secrets += len(result.get("Secrets", []) or [])
        misconfigs += len(result.get("Misconfigurations", []) or [])
    return {
        "ran": True,
        "report": str(path),
        "vulnerabilities": severity,
        "secrets": secrets,
        "misconfigurations": misconfigs,
        "blocking": bool(severity.get("CRITICAL") or secrets),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--change", required=True)
    ap.add_argument("--base", default="HEAD~1")
    ap.add_argument("--execute", action="store_true", help="Run Graphify update and Trivy scan when required/available.")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    root = Path(ns.root).resolve()
    if git(root, "rev-parse", "--is-inside-work-tree") != "true":
        raise SystemExit("project gate requires a Git working tree")

    head = git(root, "rev-parse", "HEAD")
    changed = git(root, "diff", "--name-only", ns.base, "HEAD")
    files = [x for x in (changed or "").splitlines() if x.strip()]
    classifier = load_classifier()
    risk = classifier.classify(ns.change, files)

    remote = git(root, "remote", "get-url", "origin")
    github = bool(remote and ("github.com" in remote or "github" in remote.lower()))
    graph = graph_status(root, head)

    vibe_dir = root / ".vibe"
    vibe_dir.mkdir(exist_ok=True)
    executed: list[dict[str, object]] = []

    if ns.execute and int(risk["tier"]) >= 2 and shutil.which("graphify"):
        rc, out = run(["graphify", "update", "."], root)
        executed.append({"tool": "graphify", "ok": rc == 0, "output": out[-2000:]})
        if rc == 0 and head:
            version_rc, version = run(["graphify", "--version"], root)
            state = {
                "provider": "graphify",
                "provider_version": version.splitlines()[0] if version_rc == 0 else None,
                "source_commit": head,
                "schema_version": 1,
            }
            (vibe_dir / "graph-state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            graph = graph_status(root, head)

    trivy_path = vibe_dir / "trivy.json"
    if ns.execute and int(risk["tier"]) >= 2 and shutil.which("trivy"):
        rc, out = run(["trivy", "fs", "--format", "json", "--output", str(trivy_path), "."], root, 600)
        executed.append({"tool": "trivy", "ok": rc == 0, "output": out[-2000:]})

    trivy = trivy_summary(trivy_path)
    blockers: list[str] = []
    warnings: list[str] = []

    if int(risk["tier"]) >= 2:
        if not graph.get("available"):
            warnings.append("Graphify unavailable; use repository/source/config/test fallback impact analysis")
        elif not graph.get("fresh"):
            blockers.append("project graph is missing or stale for significant change")
        if not shutil.which("trivy"):
            warnings.append("Trivy unavailable; use an equivalent risk-appropriate security check")
        elif not trivy.get("ran"):
            warnings.append("Trivy installed but no current report recorded")
        elif trivy.get("blocking"):
            blockers.append("Trivy report contains critical vulnerabilities or secrets")

    result = {
        "risk": risk,
        "git": {"head": head, "changed_files": files, "origin": remote},
        "github": {"detected": github, "gh_cli": bool(shutil.which("gh"))},
        "graph": graph,
        "trivy": trivy,
        "executed": executed,
        "blockers": blockers,
        "warnings": warnings,
        "gate": "BLOCK" if blockers else ("WARN" if warnings else "PASS"),
    }

    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Gate: {result['gate']}")
        print(f"Risk: Tier {risk['tier']} — {risk['tier_name']}")
        for item in blockers:
            print(f"BLOCKER: {item}")
        for item in warnings:
            print(f"WARNING: {item}")
    return 2 if blockers else (1 if warnings else 0)


if __name__ == "__main__":
    raise SystemExit(main())
