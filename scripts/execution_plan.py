#!/usr/bin/env python3
"""Lightweight dependency/ownership/integration planning for larger Vibe tasks."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

APPROVAL_TRIGGERS = (
    "scope",
    "architecture",
    "data_semantics",
    "public_api",
    "security_posture",
    "recurring_cost",
)


def load_context_router():
    path = ROOT / "scripts" / "context_router.py"
    spec = importlib.util.spec_from_file_location("_vibe_context_router", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load context router")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_behavior_contract():
    spec = importlib.util.spec_from_file_location("_vibe_behavior", ROOT / "scripts" / "behavior_contract.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return text or "integration"


def dependency_cycles(workstreams: list[dict[str, Any]]) -> list[list[str]]:
    graph = {
        str(row.get("id") or "").strip(): [
            str(dep).strip()
            for dep in row.get("depends_on", [])
            if str(dep).strip()
        ]
        for row in workstreams
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }
    cycles: list[list[str]] = []
    visiting: list[str] = []
    visited: set[str] = set()

    def walk(node: str) -> None:
        if node in visiting:
            start = visiting.index(node)
            cycle = visiting[start:] + [node]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if node in visited:
            return
        visiting.append(node)
        for dep in graph.get(node, []):
            if dep in graph:
                walk(dep)
        visiting.pop()
        visited.add(node)

    for node in graph:
        walk(node)
    return cycles


def normalize_scope(value: str) -> str:
    return value.replace("\\", "/").strip().strip("/").removesuffix("/*")


def scope_overlap(left: str, right: str) -> bool:
    a = normalize_scope(left)
    b = normalize_scope(right)
    if not a or not b or "refine after impact analysis" in a or "refine after impact analysis" in b:
        return False
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def path_covered(path: str, scopes: list[str]) -> bool:
    value = normalize_scope(path)
    return any(
        value == normalize_scope(scope)
        or value.startswith(normalize_scope(scope) + "/")
        for scope in scopes
        if normalize_scope(scope)
    )


def draft(
    root: Path,
    task: str,
    paths: list[str] | None = None,
    complexity_override: str = "auto",
    invariants: list[str] | None = None,
    include_packs: list[str] | None = None,
    context_facts: dict[str, Any] | None = None,
    risk_facts: dict[str, Any] | None = None,
    stage: str = "plan",
    task_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    behavior = load_behavior_contract()
    contract = behavior.validate(task_contract) if task_contract is not None else None
    if contract is not None:
        if task != contract["objective"]:
            raise ValueError("task differs from retained contract objective")
        paths = paths or contract["scope"]
        if "." not in contract["scope"] and any(not path_covered(p, contract["scope"]) for p in paths):
            raise ValueError("draft paths exceed retained task scope")
    router = load_context_router()
    route = router.plan(
        root,
        task,
        paths or [],
        complexity_override,
        invariants or [],
        include_packs or [],
        context_facts=context_facts,
        risk_facts=risk_facts,
        stage=stage,
    )
    complexity = route["project"]["complexity"]["level"]
    tier = int(route["task"]["risk"]["tier"])
    classified_tier = tier
    if contract is not None:
        tier = max(tier, contract["risk_tier"])
    task_scope = str(route["task"].get("scope", {}).get("level") or "unknown")
    integration_points = route["integration_points"]

    planning_reasons: list[str] = []
    if tier >= 2:
        planning_reasons.append(f"risk Tier {tier} requires explicit planning")
    if task_scope == "cross-boundary":
        planning_reasons.append("change scope crosses project-area boundaries")
    required = bool(planning_reasons)

    workstream = {
        "id": "implementation",
        "owner": "lead-agent",
        "scope": (
            paths
            if paths
            else ["task-defined affected subsystem; refine after impact analysis"]
        ),
        "depends_on": [],
        "shared_contracts": [],
        "completion": [
            "acceptance criteria met",
            "risk-appropriate evidence collected",
        ],
    }

    integrations = [
        {
            "id": slug(value),
            "boundary": value,
            "owner": "lead-agent",
            "status": "candidate",
            "producers": [],
            "consumers": [],
            "contract": "",
            "required_evidence": [
                "focused integration/regression check for the changed boundary"
            ],
        }
        for value in integration_points
    ]

    result = {
        "schema_version": 1,
        "mode": "execution-plan" if required else "light-task",
        "draft_status": "needs-refinement" if required else "light-task-ready",
        "execution_plan_required": required,
        "planning_basis": {
            "project_complexity": complexity,
            "task_scope": task_scope,
            "risk_tier": tier,
            "reasons": planning_reasons,
            "rule": (
                "Project size preserves project intelligence but does not by "
                "itself require a new execution plan. Require a plan for "
                "significant/critical risk or demonstrated cross-boundary scope."
            ),
        },
        "plan_reuse": {
            "allowed": True,
            "rule": (
                "Reuse and validate an existing relevant plan instead of "
                "creating a duplicate plan when objective, scope, ownership, "
                "dependencies, and contracts are still current."
            ),
        },
        "objective": task,
        "context_plan": route,
        "specialist_assignments": route["required_specialists"],
        "coordination": {
            "recommended_parallelism": 1,
            "default_owner": "lead-agent",
            "multi_agent_rule": (
                "Add parallel agents only after workstreams have disjoint "
                "ownership or stable producer/consumer contracts. Shared "
                "schemas, manifests, auth, configuration, and central contracts "
                "keep a single writer."
            ),
        },
        "workstreams": [workstream],
        "integration_points": integrations,
        "project_invariants": {
            "sources": route["project"]["invariant_sources"],
            "detected": route["project"].get("detected_invariants", []),
            "explicit": route["project"]["explicit_invariants"],
            "rule": "project-wide invariants survive context reduction",
        },
        "completion_levels": {
            "task_done": [
                "task acceptance criteria satisfied",
                "task evidence gate satisfied",
            ],
            "workstream_done": [
                "owned tasks complete",
                "owned integration points verified",
                "no unresolved blocker/dependency",
            ],
            "objective_done": [
                "all required workstreams complete",
                "cross-workstream/end-to-end regression passes when applicable",
                "project state/handoff updated when semantic state changed",
            ],
        },
        "plan_drift": {
            "approval_triggers": list(APPROVAL_TRIGGERS),
            "rule": (
                "Execution detail may adapt locally. Re-plan or request approval "
                "when scope, architecture, data semantics, public API, security "
                "posture, or significant recurring cost changes."
            ),
        },
    }
    if contract is not None:
        result["task_contract"] = contract
        result["task_contract_sha256"] = behavior.digest(contract)
        result["planning_basis"]["classified_risk_tier"] = classified_tier
        result["risk_policy"] = router.load_risk_classifier().policy_for_tier(
            tier, bool(route["task"]["risk"].get("approval_required")))
        workstream["criterion_ids"] = [c["id"] for c in contract["acceptance_criteria"]]
        workstream["evidence_requirement_ids"] = [e["id"] for e in contract["evidence_requirements"]]
    return result


def validate_plan(plan: dict[str, Any], task_contract: dict[str, Any] | None = None) -> dict[str, Any]:
    failures: list[str] = load_behavior_contract().plan_failures(plan, task_contract)
    warnings: list[str] = []

    objective = str(plan.get("objective") or "").strip()
    if not objective:
        failures.append("execution plan requires objective")

    workstreams = plan.get("workstreams")
    if not isinstance(workstreams, list) or not workstreams:
        failures.append("execution plan requires at least one workstream")
        workstreams = []

    ids: list[str] = []
    for index, row in enumerate(workstreams):
        if not isinstance(row, dict):
            failures.append(f"workstream {index} must be an object")
            continue
        wid = str(row.get("id") or "").strip()
        owner = str(row.get("owner") or "").strip()
        if not wid:
            failures.append(f"workstream {index} requires id")
        else:
            ids.append(wid)
        if not owner:
            failures.append(f"workstream {wid or index} requires owner")
        deps = row.get("depends_on", [])
        if not isinstance(deps, list):
            failures.append(f"workstream {wid or index} depends_on must be an array")
        scope = row.get("scope")
        if not isinstance(scope, list) or not any(
            isinstance(value, str) and value.strip() for value in (scope or [])
        ):
            failures.append(f"workstream {wid or index} requires non-empty scope")
        completion = row.get("completion")
        if not isinstance(completion, list) or not any(
            isinstance(value, str) and value.strip()
            for value in (completion or [])
        ):
            failures.append(
                f"workstream {wid or index} requires completion criteria"
            )

    if len(ids) != len(set(ids)):
        failures.append("workstream ids must be unique")

    id_set = set(ids)
    for row in workstreams:
        if not isinstance(row, dict):
            continue
        wid = str(row.get("id") or "").strip()
        deps = row.get("depends_on", [])
        if not isinstance(deps, list):
            continue
        for dep in deps:
            if dep == wid:
                failures.append(f"workstream {wid} cannot depend on itself")
            elif dep not in id_set:
                failures.append(f"workstream {wid} has unknown dependency {dep}")

    cycles = dependency_cycles(
        [row for row in workstreams if isinstance(row, dict)]
    )
    for cycle in cycles:
        failures.append(
            "workstream dependency cycle: " + " -> ".join(cycle)
        )

    for left_index, left in enumerate(workstreams):
        if not isinstance(left, dict):
            continue
        left_owner = str(left.get("owner") or "").strip()
        left_scope = [
            str(value)
            for value in left.get("scope", [])
            if isinstance(value, str)
        ]
        for right in workstreams[left_index + 1:]:
            if not isinstance(right, dict):
                continue
            right_owner = str(right.get("owner") or "").strip()
            if not left_owner or not right_owner or left_owner == right_owner:
                continue
            right_scope = [
                str(value)
                for value in right.get("scope", [])
                if isinstance(value, str)
            ]
            if any(
                scope_overlap(a, b)
                for a in left_scope
                for b in right_scope
            ):
                failures.append(
                    "workstream ownership scopes overlap across different owners: "
                    f"{left.get('id')} ↔ {right.get('id')}"
                )

    integrations = plan.get("integration_points", [])
    if not isinstance(integrations, list):
        failures.append("integration_points must be an array")
        integrations = []
    seen_integrations: set[str] = set()
    for index, row in enumerate(integrations):
        if not isinstance(row, dict):
            failures.append(f"integration point {index} must be an object")
            continue
        iid = str(row.get("id") or "").strip()
        owner = str(row.get("owner") or "").strip()
        boundary = str(row.get("boundary") or "").strip()
        if not iid or not boundary:
            failures.append(f"integration point {index} requires id and boundary")
        if not owner:
            failures.append(f"integration point {iid or index} requires owner")
        contract = str(row.get("contract") or "").strip()
        if not contract:
            failures.append(
                f"integration point {iid or index} requires verified contract description"
            )
        evidence = row.get("required_evidence")
        if not isinstance(evidence, list) or not any(
            isinstance(value, str) and value.strip()
            for value in (evidence or [])
        ):
            failures.append(
                f"integration point {iid or index} requires evidence expectations"
            )
        producers = row.get("producers", [])
        consumers = row.get("consumers", [])
        if not isinstance(producers, list) or not isinstance(consumers, list):
            failures.append(
                f"integration point {iid or index} producers/consumers must be arrays"
            )
        else:
            unknown_links = sorted(
                {
                    str(value)
                    for value in producers + consumers
                    if str(value) not in id_set
                }
            )
            if unknown_links:
                failures.append(
                    f"integration point {iid or index} references unknown workstreams: "
                    + ", ".join(unknown_links)
                )
            if not producers and not consumers:
                warnings.append(
                    f"integration point {iid or index} is not yet connected to producer/consumer ownership"
                )
        if row.get("status") == "candidate":
            warnings.append(
                f"integration point {iid or index} remains a candidate and must be confirmed"
            )
        if iid in seen_integrations:
            failures.append(f"duplicate integration point id: {iid}")
        seen_integrations.add(iid)

    shared_contract_owners: dict[str, set[str]] = {}
    for row in workstreams:
        if not isinstance(row, dict):
            continue
        owner = str(row.get("owner") or "").strip()
        shared = row.get("shared_contracts", [])
        if shared is None:
            shared = []
        if not isinstance(shared, list):
            failures.append(
                f"workstream {row.get('id') or '?'} shared_contracts must be an array"
            )
            continue
        for value in shared:
            contract = str(value).strip()
            if not contract or not owner:
                continue
            shared_contract_owners.setdefault(contract, set()).add(owner)

    for contract, owners in sorted(shared_contract_owners.items()):
        if len(owners) > 1:
            failures.append(
                "shared contract has multiple writers: "
                f"{contract} -> {', '.join(sorted(owners))}"
            )

    coordination = plan.get("coordination") or {}
    parallelism = coordination.get("recommended_parallelism", 1)
    if not isinstance(parallelism, int) or isinstance(parallelism, bool) or parallelism < 1:
        failures.append("recommended_parallelism must be a positive integer")
    elif parallelism > 1:
        if len(workstreams) < 2:
            warnings.append(
                "parallelism > 1 without multiple explicit workstreams/ownership"
            )
        distinct_owners = {
            str(row.get("owner") or "").strip()
            for row in workstreams
            if isinstance(row, dict) and str(row.get("owner") or "").strip()
        }
        if len(distinct_owners) < parallelism:
            warnings.append(
                "recommended parallelism exceeds distinct explicit owners"
            )

    return {
        "gate": "BLOCK" if failures else ("WARN" if warnings else "PASS"),
        "failures": failures,
        "warnings": warnings,
        "workstream_count": len(workstreams),
        "integration_point_count": len(integrations),
        "task_contract_checked": "task_contract" in plan,
        "acceptance_baseline_checked": task_contract is not None,
    }


def evaluate_drift(
    plan: dict[str, Any],
    change: dict[str, Any],
) -> dict[str, Any]:
    invalid: list[str] = []
    triggered: list[str] = []
    for key in APPROVAL_TRIGGERS:
        value = change.get(key, False)
        if not isinstance(value, bool):
            invalid.append(key)
        elif value:
            triggered.append(key)

    changed_paths = change.get("changed_paths", [])
    if changed_paths is not None and not isinstance(changed_paths, list):
        invalid.append("changed_paths")
    elif isinstance(changed_paths, list) and changed_paths:
        scopes = [
            str(scope)
            for row in plan.get("workstreams", [])
            if isinstance(row, dict)
            for scope in row.get("scope", [])
            if isinstance(scope, str)
        ]
        uncovered = [
            str(path)
            for path in changed_paths
            if isinstance(path, str) and not path_covered(path, scopes)
        ]
        if uncovered and "scope" not in triggered:
            triggered.append("scope")

    if invalid:
        return {
            "gate": "BLOCK",
            "approval_required": True,
            "triggered": triggered,
            "failures": [
                "invalid drift fields: " + ", ".join(sorted(invalid))
            ],
        }

    return {
        "gate": "APPROVAL_REQUIRED" if triggered else "CONTINUE",
        "approval_required": bool(triggered),
        "triggered": triggered,
        "reason": (
            "material plan drift crosses an approval boundary"
            if triggered
            else "change stays within approved execution detail"
        ),
        "plan_objective": plan.get("objective"),
        "changed_paths": (
            changed_paths if isinstance(changed_paths, list) else []
        ),
    }


def main() -> int:
    load_behavior_contract().configure_output()
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    draft_cmd = sub.add_parser("draft")
    draft_cmd.add_argument("--root", default=".")
    draft_cmd.add_argument("--task")
    draft_cmd.add_argument("--task-contract", help="retained task-contract JSON; optional for legacy/light tasks")
    draft_cmd.add_argument("--path", action="append", default=[])
    draft_cmd.add_argument(
        "--complexity",
        choices=["auto", "small", "medium", "large"],
        default="auto",
    )
    draft_cmd.add_argument("--invariant", action="append", default=[])
    draft_cmd.add_argument("--include-pack", action="append", default=[])
    draft_cmd.add_argument("--context-runtime", action="append", default=[])
    draft_cmd.add_argument("--context-platform", action="append", default=[])
    draft_cmd.add_argument("--context-capability", action="append", default=[])
    draft_cmd.add_argument("--context-concern", action="append", default=[])
    draft_cmd.add_argument("--stage", choices=load_context_router().load_specialist_manager().registry()["lifecycle"], default="plan")
    for field in ("operation", "environment", "data-sensitivity", "change-boundary"):
        draft_cmd.add_argument("--risk-" + field)
    draft_cmd.add_argument("--json", action="store_true")

    validate_cmd = sub.add_parser("validate")
    validate_cmd.add_argument("plan_json")
    validate_cmd.add_argument("--json", action="store_true")
    validate_cmd.add_argument("--task-contract", help="independently retained contract to detect required-outcome drift")

    drift_cmd = sub.add_parser("drift")
    drift_cmd.add_argument("plan_json")
    drift_cmd.add_argument("change_json")
    drift_cmd.add_argument("--json", action="store_true")

    ns = ap.parse_args()

    try:
        return run_cli(ns, ap)
    except (ValueError, OSError) as exc:
        print(json.dumps({"gate": "BLOCK", "error": str(exc)}))
        return 2


def run_cli(ns, ap) -> int:

    if ns.command == "draft":
        contract = load_behavior_contract().read(ns.task_contract) if ns.task_contract else None
        task = ns.task or (contract["objective"] if contract else None)
        if not task:
            ap.error("draft requires --task or --task-contract")
        context_facts = {
            field: getattr(ns, f"context_{field}")
            for field in ("runtime", "platform", "capability", "concern")
            if getattr(ns, f"context_{field}")
        }
        result = draft(
            Path(ns.root),
            task,
            ns.path,
            ns.complexity,
            ns.invariant,
            ns.include_pack,
            context_facts or None,
            risk_facts={
                field: getattr(ns, "risk_" + field)
                for field in ("operation", "environment", "data_sensitivity", "change_boundary")
                if getattr(ns, "risk_" + field) is not None
            } or None,
            stage=ns.stage,
            task_contract=contract,
        )
        exit_code = 0
    elif ns.command == "validate":
        plan = json.loads(Path(ns.plan_json).read_text(encoding="utf-8"))
        baseline = load_behavior_contract().read(ns.task_contract) if ns.task_contract else None
        result = validate_plan(plan, baseline)
        exit_code = 2 if result["failures"] else 0
    else:
        plan = json.loads(Path(ns.plan_json).read_text(encoding="utf-8"))
        change = json.loads(Path(ns.change_json).read_text(encoding="utf-8"))
        result = evaluate_drift(plan, change)
        exit_code = 2 if result["gate"] == "BLOCK" else 0

    if getattr(ns, "json", False):
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
