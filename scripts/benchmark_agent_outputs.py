#!/usr/bin/env python3
"""Aggregate blind live-agent behavior contracts without inventing model results."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_evaluator():
    path = ROOT / "scripts" / "evaluate_agent_output.py"
    spec = importlib.util.spec_from_file_location("evaluate_agent_output_benchmark", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("results_dir", help="Directory containing one subdirectory per agent")
    ap.add_argument("--catalog", default=str(ROOT / "evals" / "scenarios.json"))
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    root = Path(ns.results_dir)
    catalog = json.loads(Path(ns.catalog).read_text(encoding="utf-8"))
    evaluator = load_evaluator()
    agents: list[dict[str, object]] = []

    for agent_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        rows = []
        failure_types: Counter[str] = Counter()
        for path in sorted(agent_dir.glob("*.json")):
            result = json.loads(path.read_text(encoding="utf-8"))
            scored = evaluator.score_contract(result, catalog)
            rows.append(scored)
            for failure in scored["failures"]:
                failure_types[str(failure).split(":", 1)[0]] += 1
        passed = sum(1 for row in rows if row["passed"])
        agents.append({
            "agent": agent_dir.name,
            "scenarios": len(rows),
            "passed": passed,
            "pass_rate": round(passed / len(rows), 4) if rows else None,
            "failure_types": dict(sorted(failure_types.items())),
        })

    output = {"agents": agents}
    if ns.json:
        print(json.dumps(output, indent=2))
    else:
        for row in agents:
            print(f"{row['agent']}: {row['passed']}/{row['scenarios']} ({row['pass_rate']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
