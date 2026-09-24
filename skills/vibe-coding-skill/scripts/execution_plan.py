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


def slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return text or "integration"


def draft(
    root: Path,
    task: str,
    paths: list[str] | None = None,
    complexity_override: str = "auto",
    invariants: list[str] | None = None,
) -> dict[str, Any]:
    router = load_context_router()
    route = router.plan(
        root,
        task,
        paths or [],
        complexity_override,
        invariants or [],
    )
    complexity = route["project"]["complexity"]["level"]
    tier = int(route["task"]["risk"]["tier"])
    integration_points = route["integration_points"]
    required = (
        complexity in {"medium", "large"}
        or tier >= 2
        or len(integration_points) >= 2
    )

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
            "producers": [],
            "consumers": [],
            "contract": "identify/verify the shared contract before changing it",
            "required_evidence": [
                "focused integration/regression check for the changed boundary"
            ],
        }
        for value in integration_points
    ]

    return {
        "schema_version": 1,
        "mode": "execution-plan" if required else "light-task",
        "execution_plan_required": required,
        "objective": task,
        "context_plan": route,
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


def validate_plan(plan: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []

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
        if iid in seen_integrations:
            failures.append(f"duplicate integration point id: {iid}")
        seen_integrations.add(iid)

    coordination = plan.get("coordination") or {}
    parallelism = coordination.get("recommended_parallelism", 1)
    if (
        isinstance(parallelism, int)
        and not isinstance(parallelism, bool)
        and parallelism > 1
        and len(workstreams) < 2
    ):
        warnings.append(
            "parallelism > 1 without multiple explicit workstreams/ownership"
        )

    return {
        "gate": "BLOCK" if failures else ("WARN" if warnings else "PASS"),
        "failures": failures,
        "warnings": warnings,
        "workstream_count": len(workstreams),
        "integration_point_count": len(integrations),
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

    if invalid:
        return {
            "gate": "BLOCK",
            "approval_required": True,
            "triggered": triggered,
            "failures": [
                "drift flags must be boolean: " + ", ".join(sorted(invalid))
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
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    draft_cmd = sub.add_parser("draft")
    draft_cmd.add_argument("--root", default=".")
    draft_cmd.add_argument("--task", required=True)
    draft_cmd.add_argument("--path", action="append", default=[])
    draft_cmd.add_argument(
        "--complexity",
        choices=["auto", "small", "medium", "large"],
        default="auto",
    )
    draft_cmd.add_argument("--invariant", action="append", default=[])
    draft_cmd.add_argument("--json", action="store_true")

    validate_cmd = sub.add_parser("validate")
    validate_cmd.add_argument("plan_json")
    validate_cmd.add_argument("--json", action="store_true")

    drift_cmd = sub.add_parser("drift")
    drift_cmd.add_argument("plan_json")
    drift_cmd.add_argument("change_json")
    drift_cmd.add_argument("--json", action="store_true")

    ns = ap.parse_args()

    if ns.command == "draft":
        result = draft(
            Path(ns.root),
            ns.task,
            ns.path,
            ns.complexity,
            ns.invariant,
        )
        exit_code = 0
    elif ns.command == "validate":
        plan = json.loads(Path(ns.plan_json).read_text(encoding="utf-8"))
        result = validate_plan(plan)
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
