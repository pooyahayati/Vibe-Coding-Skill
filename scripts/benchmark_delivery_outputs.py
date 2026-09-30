#!/usr/bin/env python3
"""Aggregate real-delivery benchmark evidence without treating gaps as success."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "evals" / "delivery" / "scenarios.json"
ARMS = ("control", "treatment")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def result_files(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*.json")
        if path.name not in {"aggregate.json", "run-summary.json"}
    )


def scenario_repetitions(catalog: dict[str, Any], scenario: dict[str, Any]) -> int:
    return int(scenario.get("repetitions", catalog.get("default_repetitions", 1)))


def envelope_issues(raw: Any) -> list[str]:
    if not isinstance(raw, dict):
        return ["delivery result must be a JSON object"]
    issues: list[str] = []
    if raw.get("schema_version") != 1:
        issues.append("delivery envelope schema_version must be 1")
    if raw.get("benchmark") != "real-delivery":
        issues.append("delivery envelope benchmark must be real-delivery")
    if str(raw.get("arm") or "") not in ARMS:
        issues.append("delivery envelope arm must be control or treatment")
    if not str(raw.get("agent") or "").strip():
        issues.append("delivery envelope requires agent")
    if not str(raw.get("scenario_id") or "").strip():
        issues.append("delivery envelope requires scenario_id")
    repetition = raw.get("repetition")
    if not isinstance(repetition, int) or isinstance(repetition, bool) or repetition < 1:
        issues.append("delivery envelope repetition must be a positive integer")
    for key in ("skill_version", "started_at", "completed_at"):
        if not str(raw.get(key) or "").strip():
            issues.append(f"delivery envelope requires {key}")

    runtime = raw.get("runtime")
    if not isinstance(runtime, dict):
        issues.append("delivery envelope requires runtime object")
    elif not isinstance(runtime.get("exit_code"), int) or not isinstance(
        runtime.get("duration_ms"), int
    ):
        issues.append("delivery runtime requires integer exit_code/duration_ms")

    workspace = raw.get("workspace")
    if not isinstance(workspace, dict):
        issues.append("delivery envelope requires workspace object")
    else:
        for key in ("baseline_commit", "final_tree_sha256", "diff_sha256"):
            if not str(workspace.get(key) or "").strip():
                issues.append(f"delivery workspace requires {key}")
        if not isinstance(workspace.get("changed_paths"), list):
            issues.append("delivery workspace changed_paths must be an array")
        if not isinstance(workspace.get("changed_file_count"), int):
            issues.append("delivery workspace changed_file_count must be integer")

    grader = raw.get("grader")
    if not isinstance(grader, dict):
        issues.append("delivery envelope requires grader object")
    else:
        if not isinstance(grader.get("delivery_success"), bool):
            issues.append("delivery grader requires boolean delivery_success")
        if not isinstance(grader.get("checks"), list):
            issues.append("delivery grader checks must be an array")
        if not isinstance(grader.get("failures"), list):
            issues.append("delivery grader failures must be an array")

    integrity = raw.get("integrity")
    if not isinstance(integrity, dict):
        issues.append("delivery envelope requires integrity object")
    else:
        for key in (
            "fixture_sha256", "grader_sha256", "catalog_sha256",
            "result_schema_sha256", "skill_tree_sha256",
            "prompt_sha256", "executor_id",
        ):
            if not str(integrity.get(key) or "").strip():
                issues.append(f"delivery integrity requires {key}")
        if integrity.get("hidden_grader_outside_workspace") is not True:
            issues.append("delivery integrity requires hidden grader outside workspace")
        if integrity.get("skill_installed") is not (raw.get("arm") == "treatment"):
            issues.append("delivery skill_installed does not match arm")
    return issues


def expected_keys(
    catalog: dict[str, Any],
    agents: list[str],
) -> set[tuple[str, str, str, int]]:
    return {
        (agent, str(scenario["id"]), arm, repetition)
        for scenario in catalog.get("scenarios") or []
        for agent in agents
        for arm in ARMS
        for repetition in range(1, scenario_repetitions(catalog, scenario) + 1)
    }


def _median(rows: list[dict[str, Any]], path: tuple[str, str]) -> float | None:
    values = [row[path[0]][path[1]] for row in rows]
    return float(statistics.median(values)) if values else None


def aggregate(
    results_dir: Path,
    catalog: dict[str, Any],
    *,
    required_agents: list[str],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    invalid_files: list[dict[str, str]] = []
    seen: Counter[tuple[str, str, str, int]] = Counter()

    for path in result_files(results_dir):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            invalid_files.append({"file": str(path), "error": str(exc)})
            continue
        issues = envelope_issues(raw)
        if issues:
            invalid_files.append({"file": str(path), "error": "; ".join(issues)})
            continue
        key = (
            str(raw["agent"]),
            str(raw["scenario_id"]),
            str(raw["arm"]),
            int(raw["repetition"]),
        )
        seen[key] += 1
        rows.append(raw)

    required_agents = list(dict.fromkeys(required_agents))
    expected = expected_keys(catalog, required_agents)
    observed = set(seen)
    missing = sorted(expected - observed)
    unexpected = sorted(observed - expected)
    duplicates = sorted(key for key, count in seen.items() if count > 1)

    scenario_ids = {
        str(row["id"]) for row in catalog.get("scenarios") or []
        if isinstance(row, dict) and row.get("id")
    }
    paired: dict[
        tuple[str, str], dict[str, list[dict[str, Any]]]
    ] = defaultdict(lambda: {"control": [], "treatment": []})
    for row in rows:
        if row["agent"] in required_agents and row["scenario_id"] in scenario_ids:
            paired[(str(row["agent"]), str(row["scenario_id"]))][str(row["arm"])].append(row)

    comparisons: list[dict[str, Any]] = []
    effect_counts: Counter[str] = Counter()
    for agent in required_agents:
        for scenario in catalog.get("scenarios") or []:
            sid = str(scenario["id"])
            repetitions = scenario_repetitions(catalog, scenario)
            arm_rows = paired[(agent, sid)]
            result: dict[str, Any] = {
                "agent": agent,
                "scenario_id": sid,
                "expected_repetitions": repetitions,
            }
            rates: dict[str, float | None] = {}
            for arm in ARMS:
                values = arm_rows[arm]
                complete = (
                    len(values) == repetitions
                    and len({int(item["repetition"]) for item in values}) == repetitions
                )
                success_count = sum(
                    item["grader"]["delivery_success"] is True for item in values
                )
                rate = success_count / repetitions if complete else None
                rates[arm] = rate
                result[arm] = {
                    "complete": complete,
                    "completed_runs": len(values),
                    "successful_runs": success_count,
                    "success_rate": rate,
                    "median_duration_ms": _median(values, ("runtime", "duration_ms")),
                    "median_changed_files": _median(
                        values, ("workspace", "changed_file_count")
                    ),
                }

            control, treatment = rates["control"], rates["treatment"]
            if control is None or treatment is None:
                effect, delta = "incomplete", None
            else:
                delta = treatment - control
                effect = "improved" if delta > 0 else "regressed" if delta < 0 else "neutral"
            result["effect"] = effect
            result["success_rate_delta"] = delta
            effect_counts[effect] += 1
            comparisons.append(result)

    skill_versions = sorted({str(row["skill_version"]) for row in rows})
    skill_hashes = sorted({str(row["integrity"]["skill_tree_sha256"]) for row in rows})
    catalog_hashes = sorted({str(row["integrity"]["catalog_sha256"]) for row in rows})
    schema_hashes = sorted({
        str(row["integrity"]["result_schema_sha256"]) for row in rows
    })
    agent_versions = {
        agent: sorted({
            str(row["agent_version"]) for row in rows
            if row["agent"] == agent and row.get("agent_version")
        })
        for agent in required_agents
    }
    models = {
        agent: sorted({
            str(row["model"]) for row in rows
            if row["agent"] == agent and row.get("model")
        })
        for agent in required_agents
    }
    identity_consistent = (
        len(skill_versions) == 1
        and len(skill_hashes) == 1
        and len(catalog_hashes) == 1
        and len(schema_hashes) == 1
        and all(len(values) <= 1 for values in agent_versions.values())
        and all(len(values) <= 1 for values in models.values())
    )
    evidence_complete = (
        bool(required_agents)
        and bool(catalog.get("scenarios"))
        and not invalid_files
        and not missing
        and not unexpected
        and not duplicates
        and identity_consistent
        and all(row["effect"] != "incomplete" for row in comparisons)
    )

    def render(keys: list[tuple[str, str, str, int]]) -> list[dict[str, Any]]:
        return [
            {
                "agent": agent,
                "scenario_id": scenario,
                "arm": arm,
                "repetition": repetition,
            }
            for agent, scenario, arm, repetition in keys
        ]

    return {
        "schema_version": 1,
        "benchmark": "real-delivery-aggregate",
        "required_agents": required_agents,
        "expected_scenarios": [
            str(row["id"]) for row in catalog.get("scenarios") or []
        ],
        "expected_run_count": len(expected),
        "observed_valid_run_count": len(rows),
        "evidence_complete": evidence_complete,
        "missing_runs": render(missing),
        "unexpected_runs": render(unexpected),
        "duplicate_runs": render(duplicates),
        "invalid_files": invalid_files,
        "identity": {
            "consistent": identity_consistent,
            "skill_versions": skill_versions,
            "skill_tree_sha256s": skill_hashes,
            "catalog_sha256s": catalog_hashes,
            "result_schema_sha256s": schema_hashes,
            "agent_versions": agent_versions,
            "models": models,
        },
        "effect_counts": dict(sorted(effect_counts.items())),
        "comparisons": comparisons,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("results_dir")
    ap.add_argument("--catalog", default=str(CATALOG_PATH))
    ap.add_argument("--required-agent", action="append", default=[])
    ap.add_argument("--require-complete", action="store_true")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    result = aggregate(
        Path(ns.results_dir),
        load_json(Path(ns.catalog)),
        required_agents=ns.required_agent,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 2 if ns.require_complete and not result["evidence_complete"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
