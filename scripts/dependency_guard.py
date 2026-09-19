#!/usr/bin/env python3
"""Dependency verification using official registries and OSV."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

TIMEOUT = 15
USER_AGENT = "Vibe-Coding-Skill/0.3.0"
OSV_NAMES = {
    "pypi": "PyPI",
    "npm": "npm",
    "crates": "crates.io",
    "maven": "Maven",
    "nuget": "NuGet",
    "go": "Go",
}


def request(url: str, payload: dict[str, Any] | None = None) -> bytes:
    data = None
    headers = {"Accept": "*/*", "User-Agent": USER_AGENT}
    method = "GET"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return response.read()


def http_json(url: str, payload: dict[str, Any] | None = None) -> Any:
    return json.loads(request(url, payload))


def http_text(url: str) -> str:
    return request(url).decode("utf-8")


def strip_ns(root: ET.Element) -> None:
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]


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


def lookup_maven(name: str, version: str | None) -> dict[str, Any]:
    if ":" not in name:
        return {
            "supported": True,
            "exists": None,
            "version_exists": None,
            "error": "Maven package must use group:artifact format",
        }
    group, artifact = name.split(":", 1)
    base = "https://repo1.maven.org/maven2/" + group.replace(".", "/") + "/" + artifact
    metadata = ET.fromstring(http_text(f"{base}/maven-metadata.xml"))
    strip_ns(metadata)
    versions = [x.text for x in metadata.findall("./versioning/versions/version") if x.text]
    latest = metadata.findtext("./versioning/release") or metadata.findtext("./versioning/latest")
    selected = version or latest
    repository = None
    license_value = None
    if selected and (not version or version in versions):
        try:
            pom = ET.fromstring(http_text(f"{base}/{selected}/{artifact}-{selected}.pom"))
            strip_ns(pom)
            repository = pom.findtext("./scm/url") or pom.findtext("./url")
            license_value = pom.findtext("./licenses/license/name")
        except Exception:
            pass
    return {
        "supported": True,
        "exists": True,
        "version_exists": version in versions if version else None,
        "latest_version": latest or (versions[-1] if versions else None),
        "repository": repository,
        "license": license_value,
    }


def lookup_nuget(name: str, version: str | None) -> dict[str, Any]:
    package_id = name.lower()
    base = f"https://api.nuget.org/v3-flatcontainer/{urllib.parse.quote(package_id, safe='')}"
    index = http_json(f"{base}/index.json")
    versions = index.get("versions", [])
    latest = versions[-1] if versions else None
    selected = (version or latest)
    repository = None
    license_value = None
    if selected and (not version or version.lower() in {v.lower() for v in versions}):
        try:
            nuspec = ET.fromstring(http_text(f"{base}/{selected.lower()}/{package_id}.nuspec"))
            strip_ns(nuspec)
            metadata = nuspec.find("./metadata")
            if metadata is not None:
                repository_elem = metadata.find("./repository")
                repository = (
                    repository_elem.get("url") if repository_elem is not None else None
                ) or metadata.findtext("./projectUrl")
                license_elem = metadata.find("./license")
                license_value = (
                    license_elem.text if license_elem is not None and license_elem.text else None
                ) or metadata.findtext("./licenseUrl")
        except Exception:
            pass
    return {
        "supported": True,
        "exists": True,
        "version_exists": version.lower() in {v.lower() for v in versions} if version else None,
        "latest_version": latest,
        "repository": repository,
        "license": license_value,
    }


def go_proxy_escape(module: str) -> str:
    out = []
    for ch in module:
        if "A" <= ch <= "Z":
            out.extend(["!", ch.lower()])
        else:
            out.append(ch)
    return "".join(out)


def lookup_go(name: str, version: str | None) -> dict[str, Any]:
    escaped = urllib.parse.quote(go_proxy_escape(name), safe="/!")
    versions = [x.strip() for x in http_text(f"https://proxy.golang.org/{escaped}/@v/list").splitlines() if x.strip()]
    latest_meta = http_json(
        f"https://pkg.go.dev/v1/module/{urllib.parse.quote(name, safe='/')}?version={urllib.parse.quote(version or 'latest')}&licenses=true"
    )
    licenses = latest_meta.get("licenses") or []
    if isinstance(licenses, list):
        license_value = ", ".join(
            str(item.get("type") or item.get("name") or item) if isinstance(item, dict) else str(item)
            for item in licenses
        ) or None
    else:
        license_value = str(licenses) if licenses else None
    return {
        "supported": True,
        "exists": True,
        "version_exists": version in versions if version else None,
        "latest_version": latest_meta.get("version") or (versions[-1] if versions else None),
        "repository": latest_meta.get("repoUrl"),
        "license": license_value,
    }


LOOKUPS = {
    "pypi": lookup_pypi,
    "npm": lookup_npm,
    "crates": lookup_crates,
    "maven": lookup_maven,
    "nuget": lookup_nuget,
    "go": lookup_go,
}


def registry_lookup(ecosystem: str, name: str, version: str | None) -> dict[str, Any]:
    try:
        return LOOKUPS[ecosystem](name, version)
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 410):
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
            {"id": v.get("id"), "summary": v.get("summary"), "aliases": v.get("aliases", [])}
            for v in data.get("vulns", [])
        ]
        return {"checked": True, "vulnerabilities": vulns}
    except Exception as exc:
        return {"checked": False, "vulnerabilities": [], "warning": f"OSV unavailable: {exc}"}


def decide(registry: dict[str, Any], osv: dict[str, Any], version: str | None) -> tuple[str, list[str]]:
    reasons: list[str] = []
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
    ap.add_argument("ecosystem", choices=sorted(LOOKUPS))
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
