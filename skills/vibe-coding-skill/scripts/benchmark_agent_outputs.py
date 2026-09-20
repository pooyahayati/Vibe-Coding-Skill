#!/usr/bin/env python3
"""Aggregate blind live-agent evidence without treating missing runs as success."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_evaluator():
    path = ROOT / "scripts" / "evaluate_agent_output.py"
    spec = importlib.util.spec_from_file_location(
        "evaluate_agent_output_benchmark",
        path,
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def result_files(agent_dir: Path) -> list[Path]:
    return sorted(
        p for p in agent_dir.glob("*.json")
        if p.name != "run-summary.json"
    )



def envelope_issues(raw: Any, expected_agent: str) -> list[str]:
    if not isinstance(raw, dict):
        return ["benchmark result must be a JSON object"]

    issues: list[str] = []
    if raw.get("schema_version") != 1:
        issues.append("envelope schema_version must be 1")
    if str(raw.get("agent") or "").strip() != expected_agent:
        issues.append("envelope agent does not match result directory")

    contract = raw.get("contract")
    if not isinstance(contract, dict):
        issues.append("benchmark envelope requires contract object")
        return issues

    envelope_scenario = str(raw.get("scenario_id") or "").strip()
    contract_scenario = str(contract.get("scenario_id") or "").strip()
    if not envelope_scenario:
        issues.append("benchmark envelope requires scenario_id")
    elif envelope_scenario != contract_scenario:
        issues.append("envelope scenario_id does not match contract")

    for key in ("skill_version", "agent_version", "started_at", "completed_at"):
        if not str(raw.get(key) or "").strip():
            issues.append(f"benchmark envelope requires {key}")

    integrity = raw.get("integrity")
    if not isinstance(integrity, dict):
        issues.append("benchmark envelope requires integrity object")
    else:
        for key in (
            "skill_tree_sha256",
            "catalog_sha256",
            "schema_sha256",
        ):
            if not str(integrity.get(key) or "").strip():
                issues.append(f"benchmark integrity requires {key}")

    return issues


def aggregate_agent(
    agent: str,
    agent_dir: Path | None,
    expected_ids: list[str],
    catalog: dict[str, Any],
    evaluator: Any,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    failure_types: Counter[str] = Counter()
    tier_assessments: Counter[str] = Counter()
    invalid_files: list[dict[str, str]] = []
    seen: Counter[str] = Counter()
    skill_versions: set[str] = set()
    skill_tree_sha256s: set[str] = set()
    catalog_sha256s: set[str] = set()
    schema_sha256s: set[str] = set()
    agent_versions: set[str] = set()
    models: set[str] = set()

    if agent_dir and agent_dir.exists():
        for path in result_files(agent_dir):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                issues = envelope_issues(raw, agent)
                if issues:
                    invalid_files.append({
                        "file": path.name,
                        "error": "; ".join(issues),
                    })
                    continue
                scored = evaluator.score_contract(raw, catalog)
                scenario_id = str(scored["scenario_id"])
                seen[scenario_id] += 1
                rows.append(scored)
                tier_assessments[str(scored.get("tier_assessment", "unknown"))] += 1
                for failure in scored["failures"]:
                    failure_types[str(failure).split(":", 1)[0]] += 1
                if isinstance(raw, dict) and isinstance(raw.get("contract"), dict):
                    if raw.get("skill_version"):
                        skill_versions.add(str(raw["skill_version"]))
                    integrity = raw.get("integrity") or {}
                    if isinstance(integrity, dict):
                        if integrity.get("skill_tree_sha256"):
                            skill_tree_sha256s.add(str(integrity["skill_tree_sha256"]))
                        if integrity.get("catalog_sha256"):
                            catalog_sha256s.add(str(integrity["catalog_sha256"]))
                        if integrity.get("schema_sha256"):
                            schema_sha256s.add(str(integrity["schema_sha256"]))
                    if raw.get("agent_version"):
                        agent_versions.add(str(raw["agent_version"]))
                    if raw.get("model"):
                        models.add(str(raw["model"]))
            except Exception as exc:
                invalid_files.append({"file": path.name, "error": str(exc)})

    expected = set(expected_ids)
    observed = set(seen)
    missing = sorted(expected - observed)
    unexpected = sorted(observed - expected)
    duplicates = sorted(k for k, count in seen.items() if count > 1)
    passed = sum(1 for row in rows if row["passed"] and row["scenario_id"] in expected)
    completed = sum(1 for scenario_id in expected if seen.get(scenario_id) == 1)
    complete = (
        not missing
        and not unexpected
        and not duplicates
        and not invalid_files
        and completed == len(expected_ids)
        and len(skill_versions) == 1
        and len(skill_tree_sha256s) == 1
        and len(catalog_sha256s) == 1
        and len(schema_sha256s) == 1
        and len(agent_versions) == 1
    )

    return {
        "agent": agent,
        "expected_scenarios": len(expected_ids),
        "completed_scenarios": completed,
        "passed_scenarios": passed,
        "missing_scenarios": missing,
        "unexpected_scenarios": unexpected,
        "duplicate_scenarios": duplicates,
        "invalid_files": invalid_files,
        "complete": complete,
        "conformance_rate": round(passed / len(expected_ids), 4)
        if complete and expected_ids
        else None,
        "failure_types": dict(sorted(failure_types.items())),
        "tier_assessments": dict(sorted(tier_assessments.items())),
        "skill_versions": sorted(skill_versions),
        "skill_tree_sha256s": sorted(skill_tree_sha256s),
        "catalog_sha256s": sorted(catalog_sha256s),
        "schema_sha256s": sorted(schema_sha256s),
        "agent_versions": sorted(agent_versions),
        "models": sorted(models),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "results_dir",
        help="Directory containing one subdirectory per agent",
    )
    ap.add_argument(
        "--catalog",
        default=str(ROOT / "evals" / "scenarios.json"),
    )
    ap.add_argument(
        "--required-agent",
        action="append",
        default=[],
        help="Agent evidence required for completeness; repeatable",
    )
    ap.add_argument(
        "--require-complete",
        action="store_true",
        help="Exit non-zero when required agents or scenarios are missing/invalid",
    )
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    root = Path(ns.results_dir)
    catalog = json.loads(Path(ns.catalog).read_text(encoding="utf-8"))
    expected_ids = [str(s["id"]) for s in catalog["scenarios"]]
    evaluator = load_evaluator()

    discovered = (
        sorted(p.name for p in root.iterdir() if p.is_dir())
        if root.exists()
        else []
    )
    agents = sorted(set(discovered) | set(ns.required_agent))
    rows = [
        aggregate_agent(
            agent,
            root / agent if (root / agent).exists() else None,
            expected_ids,
            catalog,
            evaluator,
        )
        for agent in agents
    ]

    missing_required_agents = sorted(
        agent for agent in ns.required_agent
        if not (root / agent).exists()
    )
    evidence_complete = (
        not missing_required_agents
        and all(
            row["complete"]
            for row in rows
            if not ns.required_agent or row["agent"] in ns.required_agent
        )
        and (bool(rows) if ns.required_agent else True)
    )

    output = {
        "schema_version": 4,
        "expected_scenarios": expected_ids,
        "required_agents": sorted(set(ns.required_agent)),
        "missing_required_agents": missing_required_agents,
        "evidence_complete": evidence_complete,
        "agents": rows,
        "note": (
            "Conformance rates are only reported for complete evidence sets. "
            "Missing runs are missing data, never success."
        ),
    }

    if ns.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"Evidence complete: {evidence_complete}")
        for row in rows:
            rate = row["conformance_rate"]
            display = "incomplete" if rate is None else f"{rate:.4f}"
            print(
                f"{row['agent']}: {row['passed_scenarios']}/"
                f"{row['expected_scenarios']} ({display})"
            )
            if row["missing_scenarios"]:
                print("  missing: " + ", ".join(row["missing_scenarios"]))

    if ns.require_complete and not evidence_complete:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
