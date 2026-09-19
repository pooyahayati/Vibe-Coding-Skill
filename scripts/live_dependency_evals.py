#!/usr/bin/env python3
"""Network-backed smoke tests for supported registry and OSV adapters."""

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
            "ecosystem": ecosystem, "package": package, "version": version,
            "registry_exists": registry.get("exists"),
            "version_exists": registry.get("version_exists"),
            "osv_checked": osv.get("checked"),
            "ok": ok,
        }
        results.append(row)
        if not ok:
            failures.append(row)
    print(json.dumps({"results": results, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
