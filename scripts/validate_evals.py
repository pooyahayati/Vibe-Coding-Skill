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
    scenarios = data.get("scenarios", [])
    if len(scenarios) < 8:
        raise SystemExit("eval catalog must contain at least 8 scenarios")

    seen_ids: set[str] = set()
    tags: set[str] = set()
    for item in scenarios:
        for key in ("id", "prompt", "expected_tier", "must_do", "must_not_do", "required_controls", "forbidden_controls"):
            if key not in item:
                raise SystemExit(f"scenario missing {key}: {item.get('id')}")
        if item["id"] in seen_ids:
            raise SystemExit(f"duplicate scenario id: {item['id']}")
        seen_ids.add(item["id"])
        tags.update(item.get("tags", []))
        if item["expected_tier"] not in [0, 1, 2, 3]:
            raise SystemExit(f"invalid tier in {item['id']}")
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
