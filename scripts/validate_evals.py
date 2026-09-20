#!/usr/bin/env python3
"""Validate the deterministic behavior-contract eval catalog."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "evals" / "scenarios.json"
OUTPUT_SCHEMA = ROOT / "evals" / "agent-output.schema.json"
REQUIRED_TAGS = {
    "tiny",
    "brownfield",
    "auth",
    "migration",
    "dependency",
    "prompt-injection",
    "graph",
    "production",
}


def main() -> int:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    schema = json.loads(OUTPUT_SCHEMA.read_text(encoding="utf-8"))
    required_output = {
        "scenario_id", "tier", "approval_required", "controls", "forbidden_actions"
    }
    if set(schema.get("required", [])) != required_output:
        raise SystemExit("agent output schema required fields drifted")
    if schema.get("additionalProperties") is not False:
        raise SystemExit("agent output schema must reject additional properties")
    if data.get("schema_version") != 3:
        raise SystemExit("eval catalog schema_version must be 3")
    scenarios = data.get("scenarios", [])
    if len(scenarios) < 8:
        raise SystemExit("eval catalog must contain at least 8 scenarios")

    seen_ids: set[str] = set()
    tags: set[str] = set()
    for item in scenarios:
        for key in ("id", "prompt", "expected_tier", "tier_policy", "must_do", "must_not_do", "required_controls", "forbidden_controls"):
            if key not in item:
                raise SystemExit(f"scenario missing {key}: {item.get('id')}")
        if item["id"] in seen_ids:
            raise SystemExit(f"duplicate scenario id: {item['id']}")
        seen_ids.add(item["id"])
        tags.update(item.get("tags", []))
        if item["expected_tier"] not in [0, 1, 2, 3]:
            raise SystemExit(f"invalid tier in {item['id']}")
        tier_policy = item.get("tier_policy")
        if not isinstance(tier_policy, dict):
            raise SystemExit(f"invalid tier_policy in {item['id']}")
        allowed_policy_keys = {"max_acceptable_tier", "escalation_rationale"}
        extra_policy_keys = set(tier_policy) - allowed_policy_keys
        if extra_policy_keys:
            raise SystemExit(
                f"unknown tier_policy keys in {item['id']}: {sorted(extra_policy_keys)}"
            )
        max_acceptable_tier = tier_policy.get("max_acceptable_tier")
        if (
            not isinstance(max_acceptable_tier, int)
            or isinstance(max_acceptable_tier, bool)
            or max_acceptable_tier not in [0, 1, 2, 3]
        ):
            raise SystemExit(f"invalid max_acceptable_tier in {item['id']}")
        if max_acceptable_tier < item["expected_tier"]:
            raise SystemExit(
                f"tier ceiling below expected tier in {item['id']}"
            )
        if max_acceptable_tier > item["expected_tier"]:
            rationale = tier_policy.get("escalation_rationale")
            if not isinstance(rationale, str) or not rationale.strip():
                raise SystemExit(
                    f"conservative escalation needs rationale in {item['id']}"
                )
        if not item["must_do"]:
            raise SystemExit(f"must_do cannot be empty in {item['id']}")
        required_controls = item.get("required_controls", [])
        forbidden_controls = item.get("forbidden_controls", [])
        if not required_controls:
            raise SystemExit(f"required_controls cannot be empty in {item['id']}")
        overlap = set(required_controls) & set(forbidden_controls)
        if overlap:
            raise SystemExit(f"control contract overlaps in {item['id']}: {sorted(overlap)}")
        for control in required_controls + forbidden_controls:
            if not control or control.lower() != control or " " in control:
                raise SystemExit(f"control must be lowercase token in {item['id']}: {control!r}")

    missing = REQUIRED_TAGS - tags
    if missing:
        raise SystemExit(f"eval coverage missing tags: {sorted(missing)}")

    print(f"Eval catalog validation passed: {len(scenarios)} scenarios.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
