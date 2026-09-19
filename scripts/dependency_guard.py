#!/usr/bin/env python3
"""Baseline dependency verification using official registries and OSV.

Automated adapters intentionally cover only evidence we can verify reliably.
Missing evidence yields REVIEW REQUIRED instead of a false ACCEPT.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

TIMEOUT = 20
USER_AGENT = "Vibe-Coding-Skill/0.3.0"
OSV_NAMES = {
    "pypi": "PyPI",
    "npm": "npm",
    "crates": "crates.io",
    "maven": "Maven",
    "nuget": "NuGet",
    "go": "Go",
}

def request_bytes(url: str, payload: dict[str, Any] | None = None, accept: str = "application/json") -> bytes:
    data = None
    headers = {"Accept": accept, "User-Agent": USER_AGENT}
    method = "GET"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return response.read()

def http_json(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return json.loads(request_bytes(url, payload).decode("utf-8"))

def lookup_pypi(name: str, version: str | None) -> dict[str, Any]:
    quoted = urllib.parse.quote(name, safe="")
    data = http_json(f"https://pypi.org/pypi/{quoted}/json")
    info = data.get("info", {})
    releases = data.get("releases", {})
    return {
        "supported": True, "exists": True,
        "version_exists": version in releases if version else None,
        "latest_version": info.get("version"),
        "repository": (info.get("project_urls") or {}).get("Source")
        or (info.get("project_urls") or {}).get("Repository")
        or info.get("home_page"),
        "license": info.get("license") or None,
        "registry": "PyPI",
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
        "supported": True, "exists": True,
        "version_exists": version in versions if version else None,
        "latest_version": latest, "repository": repo,
        "license": license_value or None, "registry": "npm",
    }

def lookup_crates(name: str, version: str | None) -> dict[str, Any]:
    quoted = urllib.parse.quote(name, safe="")
    data = http_json(f"https://crates.io/api/v1/crates/{quoted}")
    crate = data.get("crate", {})
    versions = {v.get("num") for v in data.get("versions", [])}
    return {
        "supported": True, "exists": True,
        "version_exists": version in versions if version else None,
        "latest_version": crate.get("max_stable_version") or crate.get("max_version"),
        "repository": crate.get("repository"),
        "license": crate.get("license"), "registry": "crates.io",
    }

def _maven_parts(name: str) -> tuple[str, str]:
    if name.count(":") != 1:
        raise ValueError("Maven package must be groupId:artifactId")
    group, artifact = (p.strip() for p in name.split(":", 1))
    if not group or not artifact:
        raise ValueError("Maven package must be groupId:artifactId")
    return group, artifact

def _xml_local(element: ET.Element, local: str) -> ET.Element | None:
    for child in element.iter():
        if child.tag.rsplit("}", 1)[-1] == local:
            return child
    return None

def _maven_pom_metadata(group: str, artifact: str, version: str) -> tuple[str | None, str | None]:
    group_path = "/".join(urllib.parse.quote(p, safe="") for p in group.split("."))
    artifact_q = urllib.parse.quote(artifact, safe="")
    version_q = urllib.parse.quote(version, safe="")
    url = f"https://repo1.maven.org/maven2/{group_path}/{artifact_q}/{version_q}/{artifact_q}-{version_q}.pom"
    root = ET.fromstring(request_bytes(url, accept="application/xml,text/xml,*/*;q=0.1"))
    repository = None
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] == "scm":
            for child in node:
                if child.tag.rsplit("}", 1)[-1] in {"url", "connection"} and child.text:
                    repository = child.text.strip()
                    break
        if repository:
            break
    if not repository:
        url_node = _xml_local(root, "url")
        if url_node is not None and url_node.text:
            repository = url_node.text.strip()
    license_name = None
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] == "licenses":
            for license_node in node:
                if license_node.tag.rsplit("}", 1)[-1] != "license":
                    continue
                for child in license_node:
                    if child.tag.rsplit("}", 1)[-1] == "name" and child.text:
                        license_name = child.text.strip()
                        break
                if license_name:
                    break
        if license_name:
            break
    return repository, license_name

def lookup_maven(name: str, version: str | None) -> dict[str, Any]:
    group, artifact = _maven_parts(name)
    exact = f'g:"{group}" AND a:"{artifact}"'
    params = urllib.parse.urlencode({"q": exact, "rows": 20, "wt": "json"})
    data = http_json(f"https://search.maven.org/solrsearch/select?{params}")
    docs = ((data.get("response") or {}).get("docs") or [])
    if not docs:
        return {"supported": True, "exists": False, "version_exists": False, "registry": "Maven Central"}
    latest = docs[0].get("latestVersion")
    selected = version or latest
    version_exists: bool | None = None
    if version:
        version_query = f'g:"{group}" AND a:"{artifact}" AND v:"{version}"'
        vparams = urllib.parse.urlencode({"q": version_query, "rows": 1, "wt": "json"})
        vdata = http_json(f"https://search.maven.org/solrsearch/select?{vparams}")
        version_exists = bool(((vdata.get("response") or {}).get("numFound") or 0) > 0)
    repository = license_value = None
    if selected and (not version or version_exists):
        try:
            repository, license_value = _maven_pom_metadata(group, artifact, selected)
        except Exception:
            pass
    return {
        "supported": True, "exists": True, "version_exists": version_exists,
        "latest_version": latest, "repository": repository,
        "license": license_value, "registry": "Maven Central",
    }

def _nuget_resource(index: dict[str, Any], prefix: str) -> str:
    for resource in index.get("resources", []):
        types = resource.get("@type")
        if isinstance(types, str):
            types = [types]
        if any(str(t).startswith(prefix) for t in (types or [])):
            return str(resource["@id"])
    raise RuntimeError(f"NuGet service index missing {prefix}")

def lookup_nuget(name: str, version: str | None) -> dict[str, Any]:
    index = http_json("https://api.nuget.org/v3/index.json")
    flat = _nuget_resource(index, "PackageBaseAddress")
    search = _nuget_resource(index, "SearchQueryService")
    lower = name.lower()
    versions_data = http_json(f"{flat.rstrip('/')}/{urllib.parse.quote(lower, safe='.-_')}/index.json")
    versions = versions_data.get("versions", [])
    if not versions:
        return {"supported": True, "exists": False, "version_exists": False, "registry": "NuGet.org"}
    query = urllib.parse.urlencode({"q": name, "take": 30, "prerelease": "true", "semVerLevel": "2.0.0"})
    search_data = http_json(f"{search}?{query}")
    exact = next((item for item in search_data.get("data", []) if str(item.get("id", "")).lower() == lower), {})
    latest = exact.get("version") or versions[-1]
    return {
        "supported": True, "exists": True,
        "version_exists": version.lower() in {str(v).lower() for v in versions} if version else None,
        "latest_version": latest,
        "repository": exact.get("projectUrl") or exact.get("registration"),
        "license": exact.get("licenseExpression") or exact.get("licenseUrl"),
        "registry": "NuGet.org",
    }

def _go_escape(value: str) -> str:
    out: list[str] = []
    for ch in value:
        if ch == "!":
            out.append("!!")
        elif "A" <= ch <= "Z":
            out.append("!" + ch.lower())
        else:
            out.append(ch)
    return "".join(out)

def _go_repo(name: str) -> str | None:
    parts = name.split("/")
    if len(parts) >= 3 and parts[0] in {"github.com", "gitlab.com", "bitbucket.org"}:
        return "https://" + "/".join(parts[:3])
    return None

def lookup_go(name: str, version: str | None) -> dict[str, Any]:
    escaped = urllib.parse.quote(_go_escape(name), safe="/!")
    latest_data = http_json(f"https://proxy.golang.org/{escaped}/@latest")
    latest = latest_data.get("Version")
    version_exists: bool | None = None
    if version:
        escaped_version = urllib.parse.quote(_go_escape(version), safe="!")
        info = http_json(f"https://proxy.golang.org/{escaped}/@v/{escaped_version}.info")
        version_exists = info.get("Version") == version
    return {
        "supported": True, "exists": True, "version_exists": version_exists,
        "latest_version": latest, "repository": _go_repo(name),
        "license": None, "registry": "proxy.golang.org",
        "note": "Go proxy does not provide license metadata; manual/license-provider corroboration may be required.",
    }

def registry_lookup(ecosystem: str, name: str, version: str | None) -> dict[str, Any]:
    try:
        if ecosystem == "pypi": return lookup_pypi(name, version)
        if ecosystem == "npm": return lookup_npm(name, version)
        if ecosystem == "crates": return lookup_crates(name, version)
        if ecosystem == "maven": return lookup_maven(name, version)
        if ecosystem == "nuget": return lookup_nuget(name, version)
        if ecosystem == "go": return lookup_go(name, version)
        return {"supported": False, "exists": None, "version_exists": None, "error": "unsupported ecosystem"}
    except ValueError as exc:
        return {"supported": True, "exists": None, "version_exists": None, "error": str(exc)}
    except urllib.error.HTTPError as exc:
        if exc.code in {404, 410}:
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
        vulns = [{"id": v.get("id"), "summary": v.get("summary"), "aliases": v.get("aliases", [])} for v in data.get("vulns", [])]
        return {"checked": True, "ecosystem": osv_ecosystem, "vulnerabilities": vulns}
    except Exception as exc:
        return {"checked": False, "ecosystem": osv_ecosystem, "vulnerabilities": [], "warning": f"OSV unavailable: {exc}"}

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
    ap.add_argument("ecosystem", choices=list(OSV_NAMES))
    ap.add_argument("package")
    ap.add_argument("--version")
    ap.add_argument("--skip-osv", action="store_true")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    registry = registry_lookup(ns.ecosystem, ns.package, ns.version)
    osv = (
        {"checked": False, "vulnerabilities": [], "warning": "OSV check explicitly skipped"}
        if ns.skip_osv else osv_lookup(ns.ecosystem, ns.package, ns.version)
    )
    decision, reasons = decide(registry, osv, ns.version)
    result = {
        "ecosystem": ns.ecosystem, "package": ns.package, "version": ns.version,
        "decision": decision, "registry": registry, "osv": osv, "reasons": reasons,
        "note": "ACCEPT means the baseline automated gate passed; it is not a guarantee that the package is safe, maintained, or appropriate.",
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
