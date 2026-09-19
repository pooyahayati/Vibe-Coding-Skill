#!/usr/bin/env python3
"""Network smoke tests for dependency registry + OSV providers."""

from __future__ import annotations
import argparse, json, sys
from pathlib import Path
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path: sys.path.insert(0, str(SCRIPTS))
from dependency_guard import registry_lookup, osv_lookup

CASES = [
    ("pypi", "requests", "2.31.0"),
    ("npm", "lodash", "4.17.21"),
    ("crates", "serde", "1.0.197"),
    ("maven", "org.slf4j:slf4j-api", "2.0.16"),
    ("nuget", "Newtonsoft.Json", "13.0.3"),
    ("go", "github.com/stretchr/testify", "v1.9.0"),
]

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--json", action="store_true"); ns=ap.parse_args()
    results=[]
    for ecosystem, package, version in CASES:
        registry=registry_lookup(ecosystem, package, version)
        osv=osv_lookup(ecosystem, package, version)
        ok=(registry.get("supported") is True and registry.get("exists") is True and registry.get("version_exists") is not False and osv.get("checked") is True)
        results.append({
            "ecosystem": ecosystem, "package": package, "version": version, "ok": ok,
            "registry": registry, "osv_checked": osv.get("checked"),
            "vulnerability_count": len(osv.get("vulnerabilities") or []), "osv_warning": osv.get("warning"),
        })
    failed=[r for r in results if not r["ok"]]
    payload={"ok": not failed, "total": len(results), "failed": len(failed), "results": results}
    if ns.json: print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for r in results: print(f"{'PASS' if r['ok'] else 'FAIL'} {r['ecosystem']} {r['package']}@{r['version']}")
    return 0 if not failed else 1

if __name__ == "__main__": raise SystemExit(main())
