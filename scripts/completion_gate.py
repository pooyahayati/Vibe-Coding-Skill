#!/usr/bin/env python3
"""Risk-aware evidence-based completion gate for meaningful software tasks."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

PASS_RESULTS = {"pass", "passed", "success", "ok"}

PROVENANCE_FIELDS_BY_TIER = {
    0: (),
    1: ("source", "reference"),
    2: ("source", "reference", "commit"),
    3: ("source", "reference", "commit", "captured_at"),
}

MIN_PASSING_EVIDENCE_BY_TIER = {
    0: 1,
    1: 1,
    2: 2,
    3: 2,
}

MIN_DISTINCT_EVIDENCE_KINDS_BY_TIER = {
    0: 1,
    1: 1,
    2: 2,
    3: 2,
}


def valid_risk_tier(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value in {0, 1, 2, 3}


def valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        datetime.fromisoformat(text)
    except ValueError:
        return False
    return True


def passing_evidence(evidence: list[Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in evidence
        if isinstance(item, dict)
        and str(item.get("kind") or "").strip()
        and str(item.get("result") or "").strip().lower() in PASS_RESULTS
    ]


def provenance_issues(item: dict[str, Any], risk_tier: int) -> list[str]:
    required = PROVENANCE_FIELDS_BY_TIER[risk_tier]
    if not required:
        return []

    provenance = item.get("provenance")
    if not isinstance(provenance, dict):
        return ["missing_provenance"]

    issues: list[str] = []
    for key in required:
        value = provenance.get(key)
        if not isinstance(value, str) or not value.strip():
            issues.append(f"missing_{key}")

    if "captured_at" in required and "missing_captured_at" not in issues:
        if not valid_timestamp(provenance.get("captured_at")):
            issues.append("invalid_captured_at")

    return issues


def evaluate(report: dict[str, Any]) -> dict[str, Any]:
    status = str(report.get("status") or "").strip().lower()
    criteria = report.get("acceptance_criteria") or []
    evidence = report.get("evidence") or []
    blockers = report.get("blockers") or []
    risk_tier = report.get("risk_tier")

    failures: list[str] = []
    warnings: list[str] = []
    qualified_evidence: list[dict[str, Any]] = []
    evidence_provenance_issues: list[dict[str, Any]] = []

    if status == "done":
        if not valid_risk_tier(risk_tier):
            failures.append("Done requires risk_tier 0, 1, 2, or 3")
        else:
            required_fields = PROVENANCE_FIELDS_BY_TIER[risk_tier]
            passed = passing_evidence(evidence)
            for index, item in enumerate(passed):
                issues = provenance_issues(item, risk_tier)
                if issues:
                    evidence_provenance_issues.append(
                        {
                            "index": index,
                            "kind": item.get("kind"),
                            "issues": issues,
                        }
                    )
                else:
                    qualified_evidence.append(item)

            minimum = MIN_PASSING_EVIDENCE_BY_TIER[risk_tier]
            if len(qualified_evidence) < minimum:
                failures.append(
                    f"Tier {risk_tier} requires at least {minimum} passing "
                    "evidence item(s) with required provenance"
                )

            distinct_kinds = {
                str(item.get("kind") or "").strip().lower()
                for item in qualified_evidence
                if str(item.get("kind") or "").strip()
            }
            minimum_kinds = MIN_DISTINCT_EVIDENCE_KINDS_BY_TIER[risk_tier]
            if len(distinct_kinds) < minimum_kinds:
                failures.append(
                    f"Tier {risk_tier} requires at least {minimum_kinds} "
                    "distinct passing evidence kind(s)"
                )

            if evidence_provenance_issues and qualified_evidence:
                warnings.append(
                    "some passing evidence items were ignored because their "
                    "provenance did not meet the current risk tier"
                )

        if not criteria:
            failures.append("Done requires explicit acceptance criteria")
        elif any(
            not bool(item.get("met"))
            for item in criteria
            if isinstance(item, dict)
        ):
            failures.append("one or more acceptance criteria are not met")

        if not passing_evidence(evidence):
            failures.append("Done requires at least one passing evidence item")

        if blockers:
            failures.append("Done cannot have active blockers")

    elif status in {"blocked", "unverified", "in_progress", "in progress"}:
        if status == "blocked" and not blockers:
            warnings.append("Blocked status should include a blocker")
        if risk_tier is not None and not valid_risk_tier(risk_tier):
            warnings.append("risk_tier should be 0, 1, 2, or 3 when provided")
    else:
        failures.append("status must be Done, Blocked, Unverified, or In Progress")

    required_fields = (
        list(PROVENANCE_FIELDS_BY_TIER[risk_tier])
        if valid_risk_tier(risk_tier)
        else []
    )

    return {
        "gate": "BLOCK" if failures else ("WARN" if warnings else "PASS"),
        "status": report.get("status"),
        "risk_tier": risk_tier,
        "failures": failures,
        "warnings": warnings,
        "evidence_count": len(evidence),
        "passing_evidence_count": len(passing_evidence(evidence)),
        "qualified_evidence_count": len(qualified_evidence),
        "criteria_count": len(criteria),
        "required_provenance_fields": required_fields,
        "evidence_provenance_issues": evidence_provenance_issues,
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
