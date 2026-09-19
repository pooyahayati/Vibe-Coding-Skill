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
            row.update(
                {
                    "deps_dev_checked": depsdev.get("checked"),
                    "deps_dev_licenses": depsdev.get("licenses", []),
                    "source_repository": repository,
                    "repository_health_checked": repo_health.get("checked"),
                }
            )
            deep_ok = depsdev.get("checked") is True and bool(
                depsdev.get("licenses") or registry.get("license")
            )
            if guard.github_slug(repository):
                deep_ok = deep_ok and repo_health.get("checked") is True
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
