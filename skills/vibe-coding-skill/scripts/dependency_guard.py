#!/usr/bin/env python3
"""Baseline dependency verification using official registries and OSV."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

TIMEOUT = 15
OSV_NAMES = {"pypi": "PyPI", "npm": "npm", "crates": "crates.io"}


def http_json(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json", "User-Agent": "Vibe-Coding-Skill/0.2.0"}
    method = "GET"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return json.load(response)


def lookup_pypi(name: str, version: str | None) -> dict[str, Any]:
    quoted = urllib.parse.quote(name, safe="")
    data = http_json(f"https://pypi.org/pypi/{quoted}/json")
    info = data.get("info", {})
    releases = data.get("releases", {})
    return {
        "supported": True,
        "exists": True,
        "version_exists": version in releases if version else None,
        "latest_version": info.get("version"),
        "repository": (info.get("project_urls") or {}).get("Source")
        or (info.get("project_urls") or {}).get("Repository")
        or info.get("home_page"),
        "license": info.get("license") or None,
    }


def lookup_npm(name: str, version: str | None) -> dict[str, Any]:
    quoted = urllib.parse.quote(name, safe="@")
    data = http_json(f"https://registry.npmjs.org/{quoted}")
    repo = data.get("repository")
    if isinstance(repo, dict):
        repo = repo.get("url")
    versions = data.get("versions", {})
    latest = (data.get("dist-tags") or {}).get("latest")
    selected = versions.get(version or latest, {}) if versions else {}
    license_value = selected.get("license") or data.get("license")
    if isinstance(license_value, dict):
        license_value = license_value.get("type")
    return {
        "supported": True,
        "exists": True,
        "version_exists": version in versions if version else None,
        "latest_version": latest,
        "repository": repo,
        "license": license_value or None,
    }


def lookup_crates(name: str, version: str | None) -> dict[str, Any]:
    quoted = urllib.parse.quote(name, safe="")
    data = http_json(f"https://crates.io/api/v1/crates/{quoted}")
    crate = data.get("crate", {})
    versions = {v.get("num") for v in data.get("versions", [])}
    return {
        "supported": True,
        "exists": True,
        "version_exists": version in versions if version else None,
        "latest_version": crate.get("max_stable_version") or crate.get("max_version"),
        "repository": crate.get("repository"),
        "license": crate.get("license"),
    }


def registry_lookup(ecosystem: str, name: str, version: str | None) -> dict[str, Any]:
    try:
        if ecosystem == "pypi":
            return lookup_pypi(name, version)
        if ecosystem == "npm":
            return lookup_npm(name, version)
        if ecosystem == "crates":
            return lookup_crates(name, version)
        return {
            "supported": False,
            "exists": None,
            "version_exists": None,
            "error": "unsupported ecosystem; verify against the official registry manually",
        }
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"supported": True, "exists": False, "version_exists": False, "error": "not found"}
        return {"supported": True, "exists": None, "version_exists": None, "error": f"registry HTTP {exc.code}"}
    except Exception as exc:
        return {"supported": True, "exists": None, "version_exists": None, "error": f"registry unavailable: {exc}"}


def osv_lookup(ecosystem: str, name: str, version: str | None) -> dict[str, Any]:
    if not version:
        return {"checked": False, "vulnerabilities": [], "warning": "concrete version required for OSV check"}
    osv_ecosystem = OSV_NAMES.get(ecosystem)
    if not osv_ecosystem:
        return {"checked": False, "vulnerabilities": [], "warning": "ecosystem not mapped to OSV"}
    try:
        data = http_json(
            "https://api.osv.dev/v1/query",
            {"version": version, "package": {"name": name, "ecosystem": osv_ecosystem}},
        )
        vulns = [
            {
                "id": v.get("id"),
                "summary": v.get("summary"),
                "aliases": v.get("aliases", []),
            }
            for v in data.get("vulns", [])
        ]
        return {"checked": True, "vulnerabilities": vulns}
    except Exception as exc:
        return {"checked": False, "vulnerabilities": [], "warning": f"OSV unavailable: {exc}"}


def decide(registry: dict[str, Any], osv: dict[str, Any], version: str | None) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if registry.get("supported") is False:
        return "REVIEW REQUIRED", [str(registry.get("error"))]
    if registry.get("exists") is False:
        return "REJECT", ["package does not exist in the expected official registry"]
    if registry.get("exists") is None:
        return "REVIEW REQUIRED", [str(registry.get("error") or "registry evidence unavailable")]
    if version and registry.get("version_exists") is False:
        return "REJECT", ["requested version does not exist in the official registry"]

    if osv.get("vulnerabilities"):
        reasons.append("OSV reports known vulnerabilities for the requested version")
    if not osv.get("checked"):
        reasons.append(str(osv.get("warning") or "OSV evidence unavailable"))
    if not registry.get("repository"):
        reasons.append("source repository/provenance URL missing from registry metadata")
    if not registry.get("license"):
        reasons.append("license metadata missing")
    if not version:
        reasons.append("no concrete version supplied; version-specific vulnerability check not possible")

    if reasons:
        return "REVIEW REQUIRED", reasons
    return "ACCEPT", ["baseline registry, version, provenance, license, and OSV checks passed"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ecosystem", choices=["pypi", "npm", "crates", "maven", "nuget", "go"])
    ap.add_argument("package")
    ap.add_argument("--version")
    ap.add_argument("--skip-osv", action="store_true")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    registry = registry_lookup(ns.ecosystem, ns.package, ns.version)
    osv = (
        {"checked": False, "vulnerabilities": [], "warning": "OSV check explicitly skipped"}
        if ns.skip_osv
        else osv_lookup(ns.ecosystem, ns.package, ns.version)
    )
    decision, reasons = decide(registry, osv, ns.version)
    result = {
        "ecosystem": ns.ecosystem,
        "package": ns.package,
        "version": ns.version,
        "decision": decision,
        "registry": registry,
        "osv": osv,
        "reasons": reasons,
        "note": "ACCEPT means the baseline automated gate passed; it is not a guarantee that the package is safe or appropriate.",
    }

    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Dependency Decision: {decision}")
        for reason in reasons:
            print(f"- {reason}")
    return 2 if decision == "REJECT" else (1 if decision == "REVIEW REQUIRED" else 0)


if __name__ == "__main__":
    raise SystemExit(main())
