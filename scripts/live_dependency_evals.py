#!/usr/bin/env python3
"""Network-backed smoke tests for dependency intelligence evidence providers."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SAMPLES = [
    ("pypi", "requests", "2.32.5"),
    ("npm", "zod", "4.1.5"),
    ("crates", "serde", "1.0.219"),
    ("maven", "junit:junit", "4.13.2"),
    ("nuget", "Newtonsoft.Json", "13.0.3"),
    ("go", "github.com/stretchr/testify", "v1.10.0"),
]

DEEP_SAMPLES = {
    ("pypi", "requests"),
    ("npm", "zod"),
    ("crates", "serde"),
}


def load_guard():
    path = ROOT / "scripts" / "dependency_guard.py"
    spec = importlib.util.spec_from_file_location("dependency_guard_live", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    guard = load_guard()
    results = []
    failures = []

    for ecosystem, package, version in SAMPLES:
        registry = guard.registry_lookup(ecosystem, package, version)
        osv = guard.osv_lookup(ecosystem, package, version)
        ok = (
            registry.get("exists") is True
            and registry.get("version_exists") is True
            and osv.get("checked") is True
        )
        row = {
            "ecosystem": ecosystem,
            "package": package,
            "version": version,
            "registry_exists": registry.get("exists"),
            "version_exists": registry.get("version_exists"),
            "osv_checked": osv.get("checked"),
            "ok": ok,
        }

        if (ecosystem, package) in DEEP_SAMPLES:
            depsdev = guard.depsdev_lookup(
                ecosystem, package, version, registry.get("latest_version")
            )
            repository = guard.source_repository(registry, depsdev)
            repo_health = guard.github_repository_health(repository)
            licenses = guard.effective_licenses(registry, depsdev)
            license_signal = guard.license_policy_signal(licenses, [], [])
            maintenance = guard.maintenance_signal(registry, depsdev)
            similarity = guard.name_similarity_signal(package, [])
            decision, signals = guard.evaluate_dependency(
                registry,
                osv,
                depsdev,
                repo_health,
                similarity,
                maintenance,
                license_signal,
                version,
                2,
                "required",
                "Live contract sample for dependency-intelligence integration.",
            )
            row.update(
                {
                    "deps_dev_checked": depsdev.get("checked"),
                    "deps_dev_licenses": depsdev.get("licenses", []),
                    "source_repository": repository,
                    "repository_health_checked": repo_health.get("checked"),
                    "tier2_decision": decision,
                    "tier2_signals": signals,
                }
            )
            security_findings = bool(osv.get("vulnerabilities") or depsdev.get("advisories"))
            decision_consistent = decision in {"ACCEPT", "REVIEW REQUIRED"}
            if security_findings:
                decision_consistent = (
                    decision == "REVIEW REQUIRED"
                    and any(
                        signal.get("code") in {"osv.vulnerable", "depsdev.advisory"}
                        for signal in signals
                    )
                )
            deep_ok = (
                depsdev.get("checked") is True
                and bool(licenses)
                and (not guard.github_slug(repository) or repo_health.get("checked") is True)
                and decision_consistent
            )
            row["security_findings"] = security_findings
            row["decision_consistent"] = decision_consistent
            row["deep_ok"] = deep_ok
            ok = ok and deep_ok
            row["ok"] = ok

        results.append(row)
        if not ok:
            failures.append(row)

    print(json.dumps({"results": results, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
