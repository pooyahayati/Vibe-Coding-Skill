#!/usr/bin/env python3
"""Deterministic beta/RC/stable release-readiness gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "evals" / "scenarios.json"
SCHEMA_PATH = ROOT / "evals" / "agent-output.schema.json"
PORTABLE_SKILL = (
    ROOT / "skills" / "vibe-coding-skill"
    if (ROOT / "skills" / "vibe-coding-skill" / "SKILL.md").exists()
    else ROOT
)

CHANNEL_CHECKS = {
    "beta": ("Validate Skill",),
    "rc": ("Validate Skill", "Cross Platform Smoke"),
    "stable": ("Validate Skill", "Cross Platform Smoke"),
}

STABLE_AGENTS = {"codex", "claude-code"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def skill_tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def current_skill_version() -> str:
    version_file = ROOT / "VERSION"
    if version_file.exists():
        value = version_file.read_text(encoding="utf-8").strip()
        if value:
            return value

    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"(?m)^\s*version:\s*[\"']?([^\"'\s]+)", skill)
    if not match:
        raise RuntimeError("cannot determine current Skill version")
    return match.group(1).strip()


def benchmark_identity() -> dict[str, str]:
    return {
        "skill_version": current_skill_version(),
        "skill_tree_sha256": skill_tree_hash(PORTABLE_SKILL),
        "catalog_sha256": sha256_file(CATALOG_PATH),
        "schema_sha256": sha256_file(SCHEMA_PATH),
    }


def successful_checks(
    checks: list[Any],
    commit: str,
) -> set[str]:
    passed: set[str] = set()
    for item in checks:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        conclusion = str(item.get("conclusion") or "").strip().lower()
        check_commit = str(item.get("commit") or "").strip()
        if name and conclusion == "success" and check_commit == commit:
            passed.add(name)
    return passed


def validate_stable_benchmark(
    benchmark: dict[str, Any] | None,
    expected_identity: dict[str, str],
) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    summary: dict[str, Any] = {
        "required_agents": sorted(STABLE_AGENTS),
        "provided": isinstance(benchmark, dict),
        "identity": expected_identity,
    }
    if not isinstance(benchmark, dict):
        failures.append("stable requires a real-agent benchmark aggregate")
        return failures, summary

    schema_version = benchmark.get("schema_version")
    if not isinstance(schema_version, int) or schema_version < 4:
        failures.append("stable benchmark aggregate must use schema_version >= 4")

    if benchmark.get("evidence_complete") is not True:
        failures.append("stable requires complete real-agent benchmark evidence")

    required_agents = {
        str(value)
        for value in benchmark.get("required_agents", [])
        if isinstance(value, str)
    }
    missing_required = sorted(STABLE_AGENTS - required_agents)
    if missing_required:
        failures.append(
            "stable benchmark aggregate missing required agents: "
            + ",".join(missing_required)
        )

    rows = {
        str(row.get("agent")): row
        for row in benchmark.get("agents", [])
        if isinstance(row, dict) and row.get("agent")
    }

    agent_summary: dict[str, Any] = {}
    identity_fields = {
        "skill_versions": "skill_version",
        "skill_tree_sha256s": "skill_tree_sha256",
        "catalog_sha256s": "catalog_sha256",
        "schema_sha256s": "schema_sha256",
    }

    for agent in sorted(STABLE_AGENTS):
        row = rows.get(agent)
        if not isinstance(row, dict):
            failures.append(f"stable benchmark missing agent row: {agent}")
            continue

        expected_scenarios = row.get("expected_scenarios")
        passed_scenarios = row.get("passed_scenarios")
        complete = row.get("complete") is True
        conformant = (
            isinstance(expected_scenarios, int)
            and expected_scenarios > 0
            and passed_scenarios == expected_scenarios
        )

        if not complete:
            failures.append(f"stable benchmark agent incomplete: {agent}")
        if not conformant:
            failures.append(
                f"stable benchmark agent has conformance failures: {agent}"
            )

        identity_ok = True
        observed_identity: dict[str, Any] = {}
        for aggregate_key, identity_key in identity_fields.items():
            observed = row.get(aggregate_key)
            expected = expected_identity[identity_key]
            observed_identity[aggregate_key] = observed
            if observed != [expected]:
                identity_ok = False
                failures.append(
                    f"stable benchmark identity mismatch for {agent}: "
                    f"{aggregate_key}"
                )

        agent_summary[agent] = {
            "complete": complete,
            "expected_scenarios": expected_scenarios,
            "passed_scenarios": passed_scenarios,
            "conformant": conformant,
            "identity_ok": identity_ok,
            "observed_identity": observed_identity,
        }

    summary["agents"] = agent_summary
    return failures, summary


def evaluate(
    report: dict[str, Any],
    channel: str,
    benchmark: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if channel not in CHANNEL_CHECKS:
        raise ValueError(f"unknown release channel: {channel}")

    failures: list[str] = []
    warnings: list[str] = []
    version = str(report.get("version") or "").strip()
    commit = str(report.get("commit") or "").strip()
    checks = report.get("checks") or []
    current_version = current_skill_version()

    if version != current_version:
        failures.append(
            f"release version {version!r} does not match current Skill "
            f"version {current_version!r}"
        )
    if not commit:
        failures.append("release report requires target commit")
    if not isinstance(checks, list):
        failures.append("release report checks must be an array")
        checks = []

    passed = successful_checks(checks, commit)
    required_checks = set(CHANNEL_CHECKS[channel])
    missing_checks = sorted(required_checks - passed)
    if missing_checks:
        failures.append(
            "missing successful checks for target commit: "
            + ",".join(missing_checks)
        )

    expected_identity = benchmark_identity()
    benchmark_summary: dict[str, Any] = {
        "required": channel == "stable",
        "provided": isinstance(benchmark, dict),
    }
    if channel == "stable":
        benchmark_failures, benchmark_summary = validate_stable_benchmark(
            benchmark,
            expected_identity,
        )
        failures.extend(benchmark_failures)
    elif benchmark is not None:
        warnings.append(
            "benchmark aggregate provided but not required for this release channel"
        )

    return {
        "schema_version": 1,
        "gate": "BLOCK" if failures else ("WARN" if warnings else "PASS"),
        "channel": channel,
        "version": version,
        "current_skill_version": current_version,
        "commit": commit,
        "required_checks": sorted(required_checks),
        "passing_checks": sorted(passed),
        "missing_checks": missing_checks,
        "benchmark": benchmark_summary,
        "failures": failures,
        "warnings": warnings,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("report_json")
    ap.add_argument(
        "--channel",
        choices=sorted(CHANNEL_CHECKS),
        required=True,
    )
    ap.add_argument("--benchmark-aggregate")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    report = json.loads(Path(ns.report_json).read_text(encoding="utf-8"))
    benchmark = (
        json.loads(Path(ns.benchmark_aggregate).read_text(encoding="utf-8"))
        if ns.benchmark_aggregate
        else None
    )
    result = evaluate(report, ns.channel, benchmark)

    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Release Readiness: {result['gate']} ({result['channel']})")
        for item in result["failures"]:
            print(f"ERROR: {item}")
        for item in result["warnings"]:
            print(f"WARN: {item}")
    return 2 if result["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
