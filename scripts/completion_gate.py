#!/usr/bin/env python3
"""Risk-aware evidence-based completion gate for meaningful software tasks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PASS_RESULTS = {"pass", "passed", "success", "ok"}
VERIFIABLE_SOURCES = {"tool", "runtime", "external"}


def passing_evidence(items: list[Any]) -> list[dict[str, Any]]:
    return [
        item for item in items
        if isinstance(item, dict)
        and str(item.get("kind") or "").strip()
        and str(item.get("result") or "").strip().lower() in PASS_RESULTS
    ]


def evaluate(report: dict[str, Any]) -> dict[str, Any]:
    status = str(report.get("status") or "").strip().lower()
    criteria = report.get("acceptance_criteria") or []
    evidence = report.get("evidence") or []
    blockers = report.get("blockers") or []
    risk_tier = report.get("risk_tier", 1)

    failures: list[str] = []
    warnings: list[str] = []

    if not isinstance(risk_tier, int) or isinstance(risk_tier, bool) or risk_tier not in {0, 1, 2, 3}:
        failures.append("risk_tier must be integer 0..3")
        risk_tier = 1

    passed = passing_evidence(evidence)
    verified = [
        item for item in passed
        if str(item.get("source") or "").strip().lower() in VERIFIABLE_SOURCES
    ]
    missing_source = [
        item for item in passed
        if not str(item.get("source") or "").strip()
    ]
    kinds = {
        str(item.get("kind") or "").strip().lower()
        for item in passed
        if str(item.get("kind") or "").strip()
    }

    if status == "done":
        if not criteria:
            failures.append("Done requires explicit acceptance criteria")
        elif any(
            not bool(item.get("met"))
            for item in criteria
            if isinstance(item, dict)
        ):
            failures.append("one or more acceptance criteria are not met")

        if not passed:
            failures.append("Done requires at least one passing evidence item")

        if blockers:
            failures.append("Done cannot have active blockers")

        if risk_tier <= 1:
            if missing_source:
                warnings.append(
                    "passing evidence should record source provenance "
                    "(tool, runtime, external, or self-reported)"
                )
        elif risk_tier == 2:
            if not verified:
                failures.append(
                    "Tier 2 Done requires at least one independently verifiable "
                    "passing evidence item from tool, runtime, or external source"
                )
        else:
            if len(passed) < 2:
                failures.append(
                    "Tier 3 Done requires at least two passing evidence items"
                )
            if not verified:
                failures.append(
                    "Tier 3 Done requires independently verifiable evidence "
                    "from tool, runtime, or external source"
                )
            if len(kinds) < 2:
                failures.append(
                    "Tier 3 Done requires at least two distinct evidence kinds"
                )

    elif status in {"blocked", "unverified", "in_progress", "in progress"}:
        if status == "blocked" and not blockers:
            warnings.append("Blocked status should include a blocker")
    else:
        failures.append("status must be Done, Blocked, Unverified, or In Progress")

    return {
        "gate": "BLOCK" if failures else ("WARN" if warnings else "PASS"),
        "status": report.get("status"),
        "risk_tier": risk_tier,
        "failures": failures,
        "warnings": warnings,
        "evidence_count": len(evidence),
        "passing_evidence_count": len(passed),
        "verifiable_evidence_count": len(verified),
        "evidence_kinds": sorted(kinds),
        "criteria_count": len(criteria),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("report_json")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    report = json.loads(Path(ns.report_json).read_text(encoding="utf-8"))
    result = evaluate(report)
    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Completion Gate: {result['gate']}")
        for item in result["failures"]:
            print(f"ERROR: {item}")
        for item in result["warnings"]:
            print(f"WARN: {item}")
    return 2 if result["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
