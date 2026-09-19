#!/usr/bin/env python3
"""Run executable behavior-contract evals against deterministic skill policies."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".py",""), path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    risk = load("risk_classifier.py")
    catalog = json.loads((ROOT / "evals" / "scenarios.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    rows: list[dict[str, object]] = []
    for scenario in catalog["scenarios"]:
        result = risk.classify(scenario["prompt"])
        expected = scenario["expected_tier"]
        approval_expected = scenario["approval_required"]
        tier_ok = result["tier"] == expected
        approval_ok = (not approval_expected) or bool(result["approval_required"])
        rows.append({"id": scenario["id"], "expected_tier": expected, "actual_tier": result["tier"], "tier_ok": tier_ok, "approval_ok": approval_ok})
        if not tier_ok:
            failures.append(f"{scenario['id']}: expected tier {expected}, got {result['tier']}")
        if not approval_ok:
            failures.append(f"{scenario['id']}: expected approval requirement")

    print(json.dumps({"results": rows, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
