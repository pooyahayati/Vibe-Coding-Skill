#!/usr/bin/env python3
"""Preserve observable task contracts; this module does not verify execution."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

_spec = importlib.util.spec_from_file_location("_behavior_completion", Path(__file__).with_name("completion_gate.py"))
_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gate)


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def configure_output() -> None:
    """Keep non-ASCII task/handoff output readable through Windows pipes."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def strings(value: Any, nonempty: bool = False) -> bool:
    return isinstance(value, list) and (bool(value) or not nonempty) and all(text(v) for v in value)


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def validate(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("format") != "vibe-task-contract":
        raise ValueError("expected vibe-task-contract object")
    if type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise ValueError("unsupported task-contract schema_version")
    if not all(text(value.get(k)) for k in ("task_id", "objective")) or not strings(value.get("scope"), True):
        raise ValueError("task contract requires task_id, objective and scope")
    if not _gate.valid_risk_tier(value.get("risk_tier")):
        raise ValueError("task contract requires risk_tier 0-3")
    if "specialist_assignment_ids" in value and (not strings(value["specialist_assignment_ids"]) or len(set(value["specialist_assignment_ids"])) != len(value["specialist_assignment_ids"])):
        raise ValueError("invalid retained specialist assignment IDs")
    criteria = value.get("acceptance_criteria")
    obligations = value.get("evidence_requirements")
    if not isinstance(criteria, list) or not criteria or not isinstance(obligations, list) or not obligations:
        raise ValueError("task contract requires criteria and evidence requirements")
    ids: set[str] = set()
    for row in criteria:
        if (not isinstance(row, dict) or not text(row.get("id")) or row["id"] in ids
                or not text(row.get("description")) or type(row.get("required")) is not bool):
            raise ValueError("invalid or duplicate acceptance criterion")
        ids.add(row["id"])
        if "met" in row or "evidence_ids" in row:
            raise ValueError("task snapshot must not contain completion outcome fields")
        if "behavior" in row:
            b = row["behavior"]
            allowed = {"user_action", "expected_result", "starting_state", "failure_expectation", "protected_invariants"}
            if (not isinstance(b, dict) or set(b) - allowed
                    or not all(text(b.get(k)) for k in ("user_action", "expected_result"))
                    or any(k in b and not text(b[k]) for k in ("starting_state", "failure_expectation"))
                    or ("protected_invariants" in b and not strings(b["protected_invariants"]))):
                raise ValueError("invalid behavior: preserve action/result and relevant constraints")
    required_ids = {c["id"] for c in criteria if c["required"]}
    if not required_ids:
        raise ValueError("task contract requires a required outcome")
    seen: set[str] = set()
    covered: set[str] = set()
    for row in obligations:
        if (not isinstance(row, dict) or not text(row.get("id")) or row["id"] in seen
                or not strings(row.get("criterion_ids"), True) or set(row["criterion_ids"]) - ids
                or not _gate.evidence_family(row.get("kind")) or not text(row.get("origin")) or row["origin"] not in {"collected", "reported", "manual"}
                or type(row.get("required")) is not bool):
            raise ValueError("invalid or unlinked evidence requirement")
        seen.add(row["id"])
        for field in ("input_paths", "input_excludes", "artifact_paths"):
            if field in row and not strings(row[field]):
                raise ValueError("invalid requirement " + field)
        if row["origin"] == "collected" and not strings(row.get("input_paths"), True):
            raise ValueError("collected requirement needs meaningful input_paths")
        if row["required"]:
            covered.update(row["criterion_ids"])
    if required_ids - covered:
        raise ValueError("required outcomes lack required evidence obligations")
    digest(value)  # Reject non-JSON/non-finite extensions before persistence.
    return copy.deepcopy(value)


def read(path: str | Path) -> dict[str, Any]:
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))


def compare(baseline: dict[str, Any], current: dict[str, Any]) -> list[str]:
    baseline, current = validate(baseline), validate(current)
    failures = []
    for field in ("task_id", "objective", "scope"):
        if baseline[field] != current[field]:
            failures.append("retained task " + field + " changed")
    if current["risk_tier"] < baseline["risk_tier"]:
        failures.append("retained risk floor lowered")
    for field in ("acceptance_criteria", "evidence_requirements"):
        actual = {r["id"]: r for r in current[field]}
        for row in baseline[field]:
            if row["required"] and actual.get(row["id"]) != row:
                failures.append("required " + field + " changed or removed: " + row["id"])
    return failures


def plan_failures(plan: dict[str, Any], baseline: dict[str, Any] | None = None) -> list[str]:
    if "task_contract" not in plan:
        return ["retained task contract missing from plan"] if baseline is not None or "task_contract_sha256" in plan else []
    try:
        contract = validate(plan["task_contract"])
        failures = compare(baseline, contract) if baseline is not None else []
    except ValueError as exc:
        return [str(exc)]
    if plan.get("task_contract_sha256") != digest(contract):
        failures.append("task contract fingerprint mismatch")
    if plan.get("objective") != contract["objective"]:
        failures.append("plan objective differs from task contract")
    basis = plan.get("planning_basis") or {}
    routed = (plan.get("context_plan") or {}).get("task", {}).get("risk", {}).get("tier", contract["risk_tier"])
    if type(basis.get("risk_tier")) is not int or basis["risk_tier"] < contract["risk_tier"]:
        failures.append("plan lost retained risk floor")
    if contract["risk_tier"] >= 2 and plan.get("execution_plan_required") is not True:
        failures.append("retained high-risk task requires execution plan")
    if _gate.valid_risk_tier(routed) and (type(basis.get("risk_tier")) is not int or basis["risk_tier"] < routed):
        failures.append("plan lost classified risk floor")
    ids = {c["id"] for c in contract["acceptance_criteria"]}
    obligations = {e["id"] for e in contract["evidence_requirements"]}
    covered: set[str] = set()
    streams = plan.get("workstreams")
    for row in (streams if isinstance(streams, list) else []):
        if not isinstance(row, dict):
            continue
        links, evidence = row.get("criterion_ids"), row.get("evidence_requirement_ids")
        if not strings(links) or not strings(evidence) or set(links) - ids or set(evidence) - obligations:
            failures.append("workstream has missing or unknown acceptance links")
            continue
        covered.update(links)
        if "." not in contract["scope"]:
            for path in (row.get("scope") or []):
                if text(path) and not any(path == scope or path.startswith(scope.rstrip("/") + "/") for scope in contract["scope"]):
                    failures.append("workstream exceeds retained task scope: " + path)
        for item in contract["evidence_requirements"]:
            if item["required"] and set(item["criterion_ids"]) & set(links) and item["id"] not in evidence:
                failures.append("workstream lost required evidence obligation: " + item["id"])
    if {c["id"] for c in contract["acceptance_criteria"] if c["required"]} - covered:
        failures.append("required acceptance outcomes lost from workstreams")
    return failures


def completion(contract: dict[str, Any], report: dict[str, Any] | None, stale: bool = False,
               *, root=None, expected_schema=2, context=None) -> dict[str, Any]:
    outcomes = [{"id": c["id"], "description": c["description"], "behavior": c.get("behavior"),
                 "required": c["required"], "status": "unverified", "evidence_ids": []}
                for c in contract["acceptance_criteria"]]
    if report is None or (stale and expected_schema != 3):
        return {"gate": "UNVERIFIED", "outcomes": outcomes, "execution_verified": False,
                "reason": "source/contract context changed" if stale else "no completion report"}
    if not isinstance(report, dict):
        raise ValueError("completion report must be an object")
    if expected_schema == 3:
        result = _gate.evaluate(report, task_contract=contract, root=root, context=context)
        criteria = report.get("acceptance_criteria")
        rows = {r.get("id"): r for r in (criteria if isinstance(criteria, list) else []) if isinstance(r, dict) and text(r.get("id"))}
        for outcome in outcomes:
            row = rows.get(outcome["id"], {})
            if row.get("met") is False:
                outcome["status"] = "unmet"
            elif result.get("receipt_verified") and row.get("met") is True:
                outcome["status"] = "receipt-qualified"
                outcome["evidence_ids"] = row.get("evidence_ids", [])
        collected_only = bool(result.get("receipt_resolution")) and all(r.get("qualified") and r.get("origin") == "collected" for r in result["receipt_resolution"])
        return {"gate": result["gate"], "outcomes": outcomes, "failures": result["failures"],
                "receipt_verified": result.get("receipt_verified", False),
                "execution_verified": result.get("receipt_verified", False) and collected_only,
                "reason": "receipts resolved against retained obligations and current scoped delivery inputs"}
    result = _gate.evaluate(report, contract["acceptance_criteria"])
    if type(report.get("schema_version")) is not int or report["schema_version"] != 2 or str(report.get("status") or "").lower() != "done":
        result["failures"].append("B2 outcome import requires a schema-2 Done report")
    if not _gate.valid_risk_tier(report.get("risk_tier")) or report["risk_tier"] < contract["risk_tier"]:
        result["failures"].append("completion report lowered retained risk floor")
    if report.get("task_id", contract["task_id"]) != contract["task_id"]:
        result["failures"].append("completion report task_id mismatch")
    criteria = report.get("acceptance_criteria")
    rows = {c["id"]: c for c in (criteria if isinstance(criteria, list) else []) if isinstance(c, dict) and text(c.get("id"))}
    for criterion in contract["acceptance_criteria"]:
        row = rows.get(criterion["id"], {})
        if "behavior" in row and row["behavior"] != criterion.get("behavior"):
            result["failures"].append("reported behavior differs from retained criterion: " + criterion["id"])
    result["gate"] = "BLOCK" if result["failures"] else result["gate"]
    for outcome in outcomes:
        row = rows.get(outcome["id"], {})
        if row.get("met") is False:
            outcome["status"] = "unmet"
        elif result["gate"] in {"PASS", "WARN"} and row.get("met") is True:
            outcome["status"] = "reported-met"
            outcome["evidence_ids"] = row.get("evidence_ids", [])
    return {"gate": result["gate"], "outcomes": outcomes, "failures": result["failures"],
            "execution_verified": False,
            "reason": "schema-2 declared evidence; execution receipts not verified"}


def handoff_lines(state: dict[str, Any]) -> list[str]:
    contract = state.get("task_contract")
    lines = []
    if contract:
        lines += ["", "## Task behavior and reported outcomes", "",
                  "Task: " + contract["task_id"], "Objective: " + contract["objective"],
                  "Contract SHA-256: " + state["task_contract_sha256"],
                  "Acceptance: " + state["acceptance"]["gate"], state["acceptance"]["reason"], ""]
        for row in state["acceptance"]["outcomes"]:
            lines.append(f"- {row['id']} ({'required' if row['required'] else 'optional'}): {row['description']} — {row['status']}")
            for key, value in (row.get("behavior") or {}).items():
                lines.append(f"  {key}: {json.dumps(value, ensure_ascii=False)}")
            if row["evidence_ids"]:
                lines.append("  Reported evidence: " + ", ".join(row["evidence_ids"]))
        lines += ["- " + failure for failure in state["acceptance"].get("failures", [])]
    notes = state.get("delivery") or {}
    if contract or notes:
        lines += ["", "## Use, check and next action", "",
                  "How to use: " + (notes.get("how_to_use") or "Not supplied; inspect current product setup/requirements."),
                  "How to check: " + (notes.get("how_to_check") or "Not supplied; select relevant checks for the retained outcomes."),
                  "Next action: " + (notes.get("next_action") or "Resolve unverified outcomes before claiming completion.")]
        lines += ["Limitation: " + item for item in notes.get("limitations", [])]
    return lines + ([""] if lines else [])


def main() -> int:
    configure_output()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("contract_json")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    try:
        contract = read(ns.contract_json)
        print(json.dumps({"gate": "PASS", "task_id": contract["task_id"], "sha256": digest(contract),
                          "execution_verified": False}, indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print(json.dumps({"gate": "BLOCK", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
