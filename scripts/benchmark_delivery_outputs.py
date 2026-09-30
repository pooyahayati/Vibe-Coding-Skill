#!/usr/bin/env python3
"""Aggregate real-delivery benchmark evidence without treating gaps as success."""

from __future__ import annotations

import argparse
import json
import importlib.util
import re
from datetime import datetime
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


def schema_issues(value: Any, schema: dict[str, Any], path: str = "result") -> list[str]:
    """Validate the JSON-schema keywords used by the maintained envelope schema."""
    issues: list[str] = []
    kinds = schema.get("type", [])
    kinds = [kinds] if isinstance(kinds, str) else kinds
    matches = {"object": isinstance(value, dict), "array": isinstance(value, list),
               "string": isinstance(value, str), "boolean": isinstance(value, bool),
               "integer": isinstance(value, int) and not isinstance(value, bool), "null": value is None}
    if kinds and not any(matches.get(kind, False) for kind in kinds):
        return [f"{path} has invalid type"]
    if "const" in schema and (value != schema["const"] or type(value) is not type(schema["const"])):
        issues.append(f"{path} has invalid constant")
    if "enum" in schema and value not in schema["enum"]:
        issues.append(f"{path} has invalid enum value")
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        issues.append(f"{path} is too short")
    if isinstance(value, int) and not isinstance(value, bool) and value < schema.get("minimum", value):
        issues.append(f"{path} is below minimum")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                issues.append(f"{path}.{key} is required")
        for key, item in value.items():
            if key in properties:
                issues.extend(schema_issues(item, properties[key], path + "." + key))
            elif schema.get("additionalProperties") is False:
                issues.append(f"{path}.{key} is unsupported")
    if isinstance(value, list):
        for index, item in enumerate(value):
            issues.extend(schema_issues(item, schema.get("items", {}), f"{path}[{index}]"))
    return issues


def envelope_issues(raw: Any) -> list[str]:
    schema = load_json(ROOT / "evals/delivery-result.schema.json")
    issues = schema_issues(raw, schema)
    if issues:
        return issues
    runtime, workspace, grader, integrity = (raw[key] for key in ("runtime", "workspace", "grader", "integrity"))
    for key in ("agent_version", "model"):
        if not isinstance(raw.get(key), str) or not raw[key].strip():
            issues.append(f"delivery envelope requires identifiable {key}")
    dates = []
    for key in ("started_at", "completed_at"):
        try:
            date = datetime.fromisoformat(raw[key].replace("Z", "+00:00"))
            if date.tzinfo is None:
                raise ValueError("timezone missing")
            dates.append(date)
        except ValueError:
            issues.append(f"delivery envelope {key} must be timezone-aware ISO timestamp")
    if len(dates) == 2 and dates[1] < dates[0]:
        issues.append("delivery completion precedes start")
    for container, keys in ((workspace, ("final_tree_sha256", "diff_sha256")),
                            (integrity, ("fixture_sha256", "grader_sha256", "catalog_sha256",
                                         "result_schema_sha256", "skill_tree_sha256", "prompt_sha256"))):
        for key in keys:
            if not re.fullmatch(r"[0-9a-f]{64}", container[key]):
                issues.append(f"delivery {key} must be SHA-256 hex")
    paths = workspace["changed_paths"]
    if workspace["changed_file_count"] != len(paths) or len(paths) != len(set(paths)):
        issues.append("delivery changed-file count/paths disagree")
    checks = grader["checks"]
    ids = [check["id"] for check in checks]
    if any(not cid.strip() for cid in ids) or len(ids) != len(set(ids)):
        issues.append("delivery check IDs must be nonempty and unique")
    required = [check for check in checks if check["required"]]
    success = (runtime["exit_code"] == 0 and not runtime["timed_out"]
               and grader["exit_code"] == 0 and not grader["timed_out"]
               and bool(required) and all(check["passed"] for check in required)
               and not grader["failures"] and not workspace["forbidden_path_hits"])
    if grader["delivery_success"] is not success:
        issues.append("delivery_success contradicts executor/grader/required-check outcomes")
    if integrity["skill_installed"] is not (raw["arm"] == "treatment"):
        issues.append("delivery skill_installed does not match arm")
    return issues


def expected_scenario_integrity(catalog: dict[str, Any], delivery_root: Path) -> dict[str, dict[str, str]]:
    spec = importlib.util.spec_from_file_location("delivery_identity_helpers", ROOT / "scripts/run_delivery_benchmark.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    result = {}
    for scenario in catalog.get("scenarios", []):
        fixture, grader = runner.scenario_paths(scenario, delivery_root)
        result[scenario["id"]] = {"fixture_sha256": runner.tree_hash(fixture),
                                  "grader_sha256": runner.sha256_file(grader)}
    return result


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
    delivery_root: Path = ROOT / "evals/delivery",
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    invalid_files: list[dict[str, str]] = []
    seen: Counter[tuple[str, str, str, int]] = Counter()
    expected_integrity = expected_scenario_integrity(catalog, delivery_root)
    scenarios = {item["id"]: item for item in catalog.get("scenarios", [])}

    for path in result_files(results_dir):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            invalid_files.append({"file": str(path), "error": str(exc)})
            continue
        issues = envelope_issues(raw)
        if not issues:
            sid = raw["scenario_id"]
            if sid in expected_integrity:
                for field, expected_hash in expected_integrity[sid].items():
                    if raw["integrity"].get(field) != expected_hash:
                        issues.append(f"delivery {field} does not match trusted current scenario")
                expected_checks = set(scenarios[sid].get("required_check_ids", []))
                supplied_checks = {check["id"] for check in raw["grader"]["checks"] if check["required"]}
                if raw["grader"]["exit_code"] == 0 and not expected_checks.issubset(supplied_checks):
                    issues.append("delivery result omits catalog-required checks")
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
        and all(len(values) == 1 for values in agent_versions.values())
        and all(len(values) == 1 for values in models.values())
    )
    framework_complete = (
        bool(required_agents)
        and bool(catalog.get("scenarios"))
        and not invalid_files
        and not missing
        and not unexpected
        and not duplicates
        and identity_consistent
        and all(row["effect"] != "incomplete" for row in comparisons)
    )

    real_execution = bool(rows) and all(
        row["agent"] in {"codex", "claude-code"}
        and row["integrity"]["executor_id"] == "real-" + row["agent"] for row in rows
    )
    evidence_complete = framework_complete and real_execution

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
        "framework_complete": framework_complete,
        "execution_class": "real" if real_execution else "framework",
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
    ap.add_argument("--delivery-root", default=str(ROOT / "evals/delivery"))
    ap.add_argument("--required-agent", action="append", default=[])
    ap.add_argument("--require-complete", action="store_true")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    result = aggregate(
        Path(ns.results_dir),
        load_json(Path(ns.catalog)),
        required_agents=ns.required_agent,
        delivery_root=Path(ns.delivery_root),
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 2 if ns.require_complete and not result["evidence_complete"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
