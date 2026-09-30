#!/usr/bin/env python3
"""Release readiness from required software checks on the target commit."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_RELEASE_CHECKS = (
    "Validate Skill", "Cross Platform Smoke", "Real World Repository Validation",
    "Agent Skills Spec Compatibility", "Tool Contract Tests", "WordPress Artifact Contract",
)
CHANNEL_CHECKS = {"beta": ("Validate Skill",), "rc": BASE_RELEASE_CHECKS, "stable": BASE_RELEASE_CHECKS}

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


def latest_check_conclusions(
    checks: list[Any],
    commit: str,
) -> dict[str, str]:
    latest: dict[str, tuple[tuple[int, int, int], str]] = {}
    for index, item in enumerate(checks):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        conclusion = str(item.get("conclusion") or "").strip().lower()
        check_commit = str(item.get("commit") or "").strip()
        if not name or check_commit != commit:
            continue

        run_id = item.get("run_id")
        if isinstance(run_id, int) and not isinstance(run_id, bool):
            rank = (1, run_id, index)
        else:
            rank = (0, index, index)

        current = latest.get(name)
        if current is None or rank > current[0]:
            latest[name] = (rank, conclusion)

    return {
        name: value[1]
        for name, value in latest.items()
    }


def evaluate(report: dict[str, Any], channel: str) -> dict[str, Any]:
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

    latest_checks = latest_check_conclusions(checks, commit)
    passed = {
        name
        for name, conclusion in latest_checks.items()
        if conclusion == "success"
    }
    required_checks = set(CHANNEL_CHECKS[channel])
    missing_checks = sorted(required_checks - passed)
    if missing_checks:
        failures.append(
            "missing successful checks for target commit: "
            + ",".join(missing_checks)
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
        "latest_check_conclusions": dict(sorted(latest_checks.items())),
        "missing_checks": missing_checks,
        "failures": failures,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report_json")
    parser.add_argument("--channel", choices=sorted(CHANNEL_CHECKS), required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = json.loads(Path(args.report_json).read_text(encoding="utf-8"))
    result = evaluate(report, args.channel)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Release Readiness: {result['gate']} ({result['channel']})")
        for failure in result["failures"]:
            print(f"ERROR: {failure}")
    return 2 if result["failures"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
