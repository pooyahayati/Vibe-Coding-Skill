#!/usr/bin/env python3
"""Evidence-based completion gate for meaningful software tasks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def evaluate(report: dict[str, Any]) -> dict[str, Any]:
    status = str(report.get("status") or "").strip().lower()
    criteria = report.get("acceptance_criteria") or []
    evidence = report.get("evidence") or []
    blockers = report.get("blockers") or []

    failures: list[str] = []
    warnings: list[str] = []

    if status == "done":
        if not criteria:
            failures.append("Done requires explicit acceptance criteria")
        elif any(not bool(item.get("met")) for item in criteria if isinstance(item, dict)):
            failures.append("one or more acceptance criteria are not met")

        valid_evidence = [
            item for item in evidence
            if isinstance(item, dict)
            and str(item.get("kind") or "").strip()
            and str(item.get("result") or "").strip().lower() in {"pass", "passed", "success", "ok"}
        ]
        if not valid_evidence:
            failures.append("Done requires at least one passing evidence item")

        if blockers:
            failures.append("Done cannot have active blockers")

    elif status in {"blocked", "unverified", "in_progress", "in progress"}:
        if status == "blocked" and not blockers:
            warnings.append("Blocked status should include a blocker")
    else:
        failures.append("status must be Done, Blocked, Unverified, or In Progress")

    return {
        "gate": "BLOCK" if failures else ("WARN" if warnings else "PASS"),
        "status": report.get("status"),
        "failures": failures,
        "warnings": warnings,
        "evidence_count": len(evidence),
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
