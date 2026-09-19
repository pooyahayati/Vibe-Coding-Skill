#!/usr/bin/env python3
"""Run deterministic scenario and sample-project evaluations."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from risk_classifier import classify

def run_json(cmd: list[str], cwd: Path) -> dict:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}\n{p.stdout}\n{p.stderr}")
    return json.loads(p.stdout)

def eval_scenarios() -> list[dict[str, object]]:
    catalog = json.loads((ROOT / "evals" / "scenarios.json").read_text(encoding="utf-8"))
    results = []
    for scenario in catalog.get("scenarios", []):
        risk = classify(scenario["prompt"])
        ok = risk.tier == scenario["expected_tier"] and risk.approval_required == scenario["approval_required"]
        results.append({
            "id": scenario["id"], "kind": "scenario", "ok": ok,
            "expected_tier": scenario["expected_tier"], "actual_tier": risk.tier,
            "expected_approval": scenario["approval_required"], "actual_approval": risk.approval_required,
            "signals": risk.signals,
        })
    return results

def eval_projects() -> list[dict[str, object]]:
    results = []
    project_root = ROOT / "evals" / "projects"
    for fixture in sorted(p for p in project_root.iterdir() if p.is_dir()):
        context = json.loads((fixture / "context.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="vibe-eval-") as td:
            target = Path(td)
            files_dir = fixture / "files"
            if files_dir.exists():
                shutil.copytree(files_dir, target, dirs_exist_ok=True)
            subprocess.run(["git", "init", "-q"], cwd=target, check=True)
            risk = classify(context["prompt"], context.get("changed_files", []))
            doctor = run_json([sys.executable, str(SCRIPTS / "doctor.py"), "--root", str(target), "--json"], target)
            bootstrap = run_json([
                sys.executable, str(SCRIPTS / "bootstrap_project.py"),
                "--root", str(target), "--profile", context["profile"],
                "--objective", f"Eval {context['id']}", "--dry-run", "--json",
            ], target)
            planned = set(bootstrap.get("created_or_planned", []))
            expected_bootstrap = set(context.get("expected_bootstrap", []))
            bootstrap_ok = expected_bootstrap.issubset(planned)
            doctor_ok = bool((doctor.get("git") or {}).get("installed")) and not any("not a git working tree" in p for p in doctor.get("problems", []))
            risk_ok = risk.tier == context["expected_tier"] and risk.approval_required == context["approval_required"]
            results.append({
                "id": context["id"], "kind": "sample-project",
                "ok": bool(risk_ok and bootstrap_ok and doctor_ok),
                "risk_ok": risk_ok, "bootstrap_ok": bootstrap_ok, "doctor_ok": doctor_ok,
                "expected_tier": context["expected_tier"], "actual_tier": risk.tier,
                "signals": risk.signals,
            })
    return results

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    results = eval_scenarios() + eval_projects()
    failures = [r for r in results if not r["ok"]]
    payload = {"ok": not failures, "total": len(results), "failed": len(failures), "results": results}
    if ns.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for result in results:
            print(f"{'PASS' if result['ok'] else 'FAIL'} {result['kind']} {result['id']}")
        print(f"{len(results) - len(failures)}/{len(results)} passed")
    return 0 if not failures else 1

if __name__ == "__main__":
    raise SystemExit(main())
