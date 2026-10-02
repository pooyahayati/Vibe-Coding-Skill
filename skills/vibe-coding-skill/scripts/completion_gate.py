#!/usr/bin/env python3
"""Risk-aware evidence-based completion gate for meaningful software tasks."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

REPORT_SCHEMA_VERSION = 2
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

MIN_DISTINCT_EVIDENCE_FAMILIES_BY_TIER = {
    0: 1,
    1: 1,
    2: 2,
    3: 2,
}

EVIDENCE_KIND_FAMILIES = {
    "test": "verification",
    "unit-test": "verification",
    "component-test": "verification",
    "regression-test": "verification",
    "integration": "integration",
    "integration-test": "integration",
    "contract": "integration",
    "contract-test": "integration",
    "build": "delivery",
    "artifact": "delivery",
    "package": "delivery",
    "review": "review",
    "code-review": "review",
    "independent-review": "review",
    "security": "security",
    "security-scan": "security",
    "security-review": "security",
    "smoke": "runtime",
    "runtime": "runtime",
    "runtime-check": "runtime",
    "health-check": "runtime",
    "migration": "data",
    "migration-check": "data",
    "data-integrity": "data",
    "recovery": "recovery",
    "rollback": "recovery",
    "recovery-drill": "recovery",
    "performance": "performance",
    "performance-measurement": "performance",
    "static-analysis": "static",
    "lint": "static",
    "type-check": "static",
    "manual-check": "manual",
    "visual-check": "manual",
}


def valid_risk_tier(value: Any) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value in {0, 1, 2, 3}
    )


def valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    text = value.strip()
    if "T" not in text:
        return False
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def evidence_family(kind: Any) -> str | None:
    value = str(kind or "").strip().lower().replace("_", "-")
    return EVIDENCE_KIND_FAMILIES.get(value)


def passing_evidence(evidence: list[Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in evidence
        if isinstance(item, dict)
        and str(item.get("id") or "").strip()
        and evidence_family(item.get("kind"))
        and str(item.get("result") or "").strip().lower() in PASS_RESULTS
    ]


def provenance_issues(
    item: dict[str, Any],
    risk_tier: int,
    target_commit: str | None = None,
) -> list[str]:
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

    if (
        "commit" in required
        and "missing_commit" not in issues
        and target_commit
        and str(provenance.get("commit") or "").strip() != target_commit
    ):
        issues.append("commit_mismatch")

    if "captured_at" in required and "missing_captured_at" not in issues:
        if not valid_timestamp(provenance.get("captured_at")):
            issues.append("invalid_captured_at")

    return issues


def validate_evidence_shape(evidence: Any) -> tuple[list[str], list[str]]:
    if not isinstance(evidence, list):
        return ["evidence must be an array"], []
    failures: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            failures.append(f"evidence item {index} must be an object")
            continue
        evidence_id = str(item.get("id") or "").strip()
        if not evidence_id:
            failures.append(f"evidence item {index} requires id")
        elif evidence_id in seen:
            failures.append(f"duplicate evidence id: {evidence_id}")
        else:
            seen.add(evidence_id)
        kind = str(item.get("kind") or "").strip()
        if not kind:
            failures.append(f"evidence item {index} requires kind")
        elif evidence_family(kind) is None:
            failures.append(
                f"evidence item {index} has unsupported kind {kind!r}; "
                "use a defined semantic evidence kind"
            )
        if not str(item.get("result") or "").strip():
            failures.append(f"evidence item {index} requires result")
        if not isinstance(item.get("required"), bool):
            failures.append(f"evidence item {index} requires boolean required")
            continue

        passed = str(item.get("result") or "").strip().lower() in PASS_RESULTS
        if item["required"] and not passed:
            failures.append(
                f"required evidence {evidence_id or index} did not pass"
            )
        elif not item["required"] and not passed:
            justification = str(item.get("justification") or "").strip()
            if not justification:
                failures.append(
                    f"optional failed evidence {evidence_id or index} requires justification"
                )
            else:
                warnings.append(
                    f"optional evidence {evidence_id or index} did not pass: {justification}"
                )
    return failures, warnings


def acceptance_criteria_failures(
    criteria: Any,
    evidence_ids: set[str],
) -> list[str]:
    if not isinstance(criteria, list):
        return ["acceptance_criteria must be an array"]
    if not criteria:
        return ["Done requires explicit acceptance criteria"]

    failures: list[str] = []
    seen: set[str] = set()
    if not any(isinstance(item, dict) and item.get("required") is True for item in criteria):
        failures.append("Done requires at least one required acceptance criterion")
    for index, item in enumerate(criteria):
        if not isinstance(item, dict):
            failures.append(f"acceptance criterion {index} must be an object")
            continue

        criterion_id = str(item.get("id") or "").strip()
        description = str(item.get("description") or "").strip()
        if not criterion_id:
            failures.append(f"acceptance criterion {index} requires id")
        elif criterion_id in seen:
            failures.append(f"duplicate acceptance criterion id: {criterion_id}")
        else:
            seen.add(criterion_id)
        if not description:
            failures.append(
                f"acceptance criterion {criterion_id or index} requires description"
            )
        if not isinstance(item.get("required"), bool):
            failures.append(
                f"acceptance criterion {criterion_id or index} requires boolean required"
            )
        if not isinstance(item.get("met"), bool):
            failures.append(
                f"acceptance criterion {criterion_id or index} requires boolean met"
            )
        elif item.get("required") is True and item["met"] is not True:
            failures.append(
                f"required acceptance criterion {criterion_id or index} is not met"
            )

        linked = item.get("evidence_ids")
        if not isinstance(linked, list) or not linked or not all(
            isinstance(value, str) and value.strip() for value in linked
        ):
            failures.append(
                f"acceptance criterion {criterion_id or index} requires evidence_ids"
            )
            continue
        missing = sorted(set(linked) - evidence_ids)
        if missing:
            failures.append(
                f"acceptance criterion {criterion_id or index} references unknown evidence: "
                + ", ".join(missing)
            )
    return failures


def evaluate_declared(
    report: dict[str, Any],
    acceptance_baseline: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    status = str(report.get("status") or "").strip().lower()
    raw_criteria = report.get("acceptance_criteria")
    raw_evidence = report.get("evidence")
    raw_blockers = report.get("blockers")
    risk_tier = report.get("risk_tier")
    target_commit = str(report.get("commit") or "").strip()
    schema_version = report.get("schema_version")

    criteria = raw_criteria if isinstance(raw_criteria, list) else []
    evidence = raw_evidence if isinstance(raw_evidence, list) else []
    blockers = raw_blockers if isinstance(raw_blockers, list) else []

    failures: list[str] = []
    warnings: list[str] = []
    qualified_evidence: list[dict[str, Any]] = []
    qualified_evidence_families: set[str] = set()
    evidence_provenance_issues: list[dict[str, Any]] = []

    if status == "done":
        if schema_version != REPORT_SCHEMA_VERSION:
            failures.append(
                f"Done reports require schema_version {REPORT_SCHEMA_VERSION}"
            )

        evidence_shape_failures, evidence_shape_warnings = validate_evidence_shape(
            raw_evidence
        )
        failures.extend(evidence_shape_failures)
        warnings.extend(evidence_shape_warnings)

        evidence_by_id = {
            str(item.get("id")).strip(): item
            for item in evidence
            if isinstance(item, dict) and str(item.get("id") or "").strip()
        }
        failures.extend(
            acceptance_criteria_failures(raw_criteria, set(evidence_by_id))
        )
        if acceptance_baseline is not None:
            if not isinstance(acceptance_baseline, list) or not acceptance_baseline:
                failures.append("acceptance baseline must be a nonempty criteria array")
            else:
                current = {item["id"]: item for item in criteria
                           if isinstance(item, dict) and isinstance(item.get("id"), str)}
                baseline_ids: set[str] = set()
                if not any(isinstance(item, dict) and item.get("required") is True for item in acceptance_baseline):
                    failures.append("acceptance baseline requires a required outcome")
                for criterion in acceptance_baseline:
                    if (not isinstance(criterion, dict) or not isinstance(criterion.get("id"), str)
                            or not criterion["id"].strip() or criterion["id"] in baseline_ids
                            or not isinstance(criterion.get("description"), str)
                            or not criterion["description"].strip()
                            or not isinstance(criterion.get("required"), bool)):
                        failures.append("acceptance baseline contains an invalid criterion")
                        continue
                    baseline_ids.add(criterion["id"])
                    if criterion["required"]:
                        actual = current.get(criterion["id"], {})
                        if actual.get("required") is not True or actual.get("description") != criterion.get("description"):
                            failures.append(f"approved required criterion changed or removed: {criterion['id']}")

        if raw_blockers is not None and not isinstance(raw_blockers, list):
            failures.append("blockers must be an array")

        if not valid_risk_tier(risk_tier):
            failures.append("Done requires risk_tier 0, 1, 2, or 3")
        else:
            if risk_tier >= 2 and not target_commit:
                failures.append(f"Tier {risk_tier} Done requires target commit")

            passed = passing_evidence(evidence)
            qualified_ids: set[str] = set()
            for index, item in enumerate(passed):
                issues = provenance_issues(item, risk_tier, target_commit or None)
                if issues:
                    evidence_provenance_issues.append(
                        {
                            "index": index,
                            "id": item.get("id"),
                            "kind": item.get("kind"),
                            "issues": issues,
                        }
                    )
                else:
                    qualified_evidence.append(item)
                    family = evidence_family(item.get("kind"))
                    if family:
                        qualified_evidence_families.add(family)
                    qualified_ids.add(str(item.get("id") or "").strip())

            for criterion in criteria:
                if not isinstance(criterion, dict):
                    continue
                if criterion.get("required") is not True:
                    continue
                criterion_id = str(criterion.get("id") or "").strip()
                linked = criterion.get("evidence_ids")
                if not isinstance(linked, list):
                    continue
                if not any(value in qualified_ids for value in linked):
                    failures.append(
                        f"required acceptance criterion {criterion_id or '?'} "
                        "has no linked passing evidence with required provenance"
                    )

            minimum = MIN_PASSING_EVIDENCE_BY_TIER[risk_tier]
            if len(qualified_evidence) < minimum:
                failures.append(
                    f"Tier {risk_tier} requires at least {minimum} passing "
                    "evidence item(s) with required provenance"
                )

            minimum_families = MIN_DISTINCT_EVIDENCE_FAMILIES_BY_TIER[risk_tier]
            if len(qualified_evidence_families) < minimum_families:
                failures.append(
                    f"Tier {risk_tier} requires at least {minimum_families} "
                    "distinct semantic evidence family/families"
                )

            if evidence_provenance_issues and qualified_evidence:
                warnings.append(
                    "some passing evidence items were ignored because their "
                    "provenance did not meet the current risk tier"
                )

        if not passing_evidence(evidence):
            failures.append("Done requires at least one passing evidence item")

        if blockers:
            failures.append("Done cannot have active blockers")

    elif status in {"blocked", "unverified", "in_progress", "in progress"}:
        if status == "blocked" and not blockers:
            warnings.append("Blocked status should include a blocker")
        if risk_tier is not None and not valid_risk_tier(risk_tier):
            warnings.append("risk_tier should be 0, 1, 2, or 3 when provided")
        if raw_criteria is not None and not isinstance(raw_criteria, list):
            warnings.append("acceptance_criteria should be an array")
        if raw_evidence is not None and not isinstance(raw_evidence, list):
            warnings.append("evidence should be an array")
        if raw_blockers is not None and not isinstance(raw_blockers, list):
            warnings.append("blockers should be an array")
    else:
        failures.append(
            "status must be Done, Blocked, Unverified, or In Progress"
        )

    required_fields = (
        list(PROVENANCE_FIELDS_BY_TIER[risk_tier])
        if valid_risk_tier(risk_tier)
        else []
    )

    return {
        "schema_version": schema_version,
        "gate": "BLOCK" if failures else ("WARN" if warnings else "PASS"),
        "status": report.get("status"),
        "risk_tier": risk_tier,
        "commit": target_commit or None,
        "failures": failures,
        "warnings": warnings,
        "evidence_count": len(evidence),
        "passing_evidence_count": len(passing_evidence(evidence)),
        "qualified_evidence_count": len(qualified_evidence),
        "qualified_evidence_families": sorted(qualified_evidence_families),
        "supported_evidence_kinds": sorted(EVIDENCE_KIND_FAMILIES),
        "criteria_count": len(criteria),
        "acceptance_baseline_checked": acceptance_baseline is not None,
        "required_provenance_fields": required_fields,
        "evidence_provenance_issues": evidence_provenance_issues,
    }


def evaluate(report, acceptance_baseline=None, *, task_contract=None, root=None, receipt_root=None, context=None):
    if not isinstance(report, dict):
        return {"gate": "BLOCK", "failures": ["report must be an object"], "warnings": []}
    if task_contract is not None:
        import receipt_validation
        return receipt_validation.evaluate_completion(report, task_contract, root, receipt_root, context, evaluate_declared)
    if report.get("schema_version") == 3:
        return {"gate": "BLOCK", "failures": ["schema 3 requires an independently retained task contract and project root"], "warnings": [], "receipt_verified": False}
    result = evaluate_declared(report, acceptance_baseline)
    result["receipt_verified"] = False
    return result


def main() -> int:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import behavior_contract
    behavior_contract.configure_output()
    ap = argparse.ArgumentParser()
    ap.add_argument("report_json")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--acceptance-baseline", help="independently retained approved criteria JSON array")
    ap.add_argument("--task-contract", help="retained version-1 contract; requires schema-3 receipts")
    ap.add_argument("--root", help="actual intended delivery project root")
    ap.add_argument("--context", help="independently supplied relevant delivery runtime/dataset JSON")
    ns = ap.parse_args()

    try:
        report = json.loads(Path(ns.report_json).read_text(encoding="utf-8"))
        baseline = json.loads(Path(ns.acceptance_baseline).read_text(encoding="utf-8")) if ns.acceptance_baseline else None
        contract = behavior_contract.read(ns.task_contract) if ns.task_contract else None
        result = evaluate(report, baseline, task_contract=contract, root=ns.root,
                          context=json.loads(ns.context) if ns.context else None)
    except (ValueError, OSError, TypeError, RuntimeError):
        result = {"gate": "BLOCK", "failures": ["invalid or inaccessible completion context"], "warnings": [], "receipt_verified": False}
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
