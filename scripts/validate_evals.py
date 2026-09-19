#!/usr/bin/env python3
"""Validate the deterministic behavior-contract eval catalog."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "evals" / "scenarios.json"
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
    scenarios = data.get("scenarios", [])
    if len(scenarios) < 8:
        raise SystemExit("eval catalog must contain at least 8 scenarios")

    seen_ids: set[str] = set()
    tags: set[str] = set()
    for item in scenarios:
        for key in ("id", "prompt", "expected_tier", "must_do", "must_not_do"):
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

    missing = REQUIRED_TAGS - tags
    if missing:
        raise SystemExit(f"eval coverage missing tags: {sorted(missing)}")

    print(f"Eval catalog validation passed: {len(scenarios)} scenarios.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
