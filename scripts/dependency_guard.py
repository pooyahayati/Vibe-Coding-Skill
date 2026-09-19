#!/usr/bin/env python3
"""Risk-adaptive dependency intelligence using registries, OSV, deps.dev, and source health."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TIMEOUT = 15
ROOT = Path(__file__).resolve().parents[1]
SKILL_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").exists() else "unknown"
USER_AGENT = f"Vibe-Coding-Skill/{SKILL_VERSION}"

OSV_NAMES = {
    "pypi": "PyPI",
    "npm": "npm",
    "crates": "crates.io",
    "maven": "Maven",
    "nuget": "NuGet",
    "go": "Go",
}

DEPSDEV_SYSTEMS = {
    "pypi": "pypi",
    "npm": "npm",
    "crates": "cargo",
    "maven": "maven",
    "nuget": "nuget",
    "go": "go",
}


def http_bytes(
    url: str,
    payload: dict[str, Any] | None = None,
    accept: str = "*/*",
    extra_headers: dict[str, str] | None = None,
) -> bytes:
    data = None
    headers = {"Accept": accept, "User-Agent": USER_AGENT}
    if extra_headers:
        headers.update(extra_headers)
    method = "GET"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return response.read()


def http_json(
    url: str,
    payload: dict[str, Any] | None = None,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    return json.loads(http_bytes(url, payload, "application/json", extra_headers))


def http_text(url: str) -> str:
    return http_bytes(url).decode("utf-8", errors="replace")


def iso_to_age_days(value: str | None) -> int | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0, (datetime.now(timezone.utc) - dt).days)
    except Exception:
        return None


def lookup_pypi(name: str, version: str | None) -> dict[str, Any]:
    quoted = urllib.parse.quote(name, safe="")
    data = http_json(f"https://pypi.org/pypi/{quoted}/json")
    info = data.get("info", {})
    releases = data.get("releases", {})
    latest = info.get("version")
    latest_files = releases.get(latest, []) if latest else []
    latest_published = max(
        (x.get("upload_time_iso_8601") for x in latest_files if x.get("upload_time_iso_8601")),
        default=None,
    )
    return {
        "supported": True,
        "exists": True,
        "canonical_name": info.get("name") or name,
        "version_exists": version in releases if version else None,
        "latest_version": latest,
        "latest_published_at": latest_published,
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
        "canonical_name": data.get("name") or name,
        "version_exists": version in versions if version else None,
        "latest_version": latest,
        "latest_published_at": (data.get("time") or {}).get(latest) if latest else None,
        "repository": repo,
        "license": license_value or None,
    }


def lookup_crates(name: str, version: str | None) -> dict[str, Any]:
    quoted = urllib.parse.quote(name, safe="")
    data = http_json(f"https://crates.io/api/v1/crates/{quoted}")
    crate = data.get("crate", {})
    versions = {v.get("num") for v in data.get("versions", [])}
    latest = crate.get("max_stable_version") or crate.get("max_version")
    selected_meta = next((v for v in data.get("versions", []) if v.get("num") == latest), {})
    return {
        "supported": True,
        "exists": True,
        "canonical_name": crate.get("name") or name,
        "version_exists": version in versions if version else None,
        "latest_version": latest,
        "latest_published_at": selected_meta.get("created_at") or crate.get("updated_at"),
        "repository": crate.get("repository"),
        "license": crate.get("license"),
    }


def lookup_maven(name: str, version: str | None) -> dict[str, Any]:
    if ":" not in name:
        return {
            "supported": True,
            "exists": None,
            "version_exists": None,
            "error": "Maven package must use group:artifact",
        }
    group, artifact = name.split(":", 1)
    group_path = group.replace(".", "/")
    artifact_q = urllib.parse.quote(artifact, safe="")
    base = f"https://repo.maven.apache.org/maven2/{group_path}/{artifact_q}"
    metadata_xml = http_text(f"{base}/maven-metadata.xml")
    metadata_root = ET.fromstring(metadata_xml)
    versions: list[str] = []
    latest = None
    release = None
    last_updated = None
    for elem in metadata_root.iter():
        local = elem.tag.rsplit("}", 1)[-1]
        if local == "version" and elem.text and elem.text.strip():
            versions.append(elem.text.strip())
        elif local == "latest" and elem.text and elem.text.strip():
            latest = elem.text.strip()
        elif local == "release" and elem.text and elem.text.strip():
            release = elem.text.strip()
        elif local == "lastUpdated" and elem.text and elem.text.strip():
            raw = elem.text.strip()
            if re.fullmatch(r"\d{14}", raw):
                last_updated = (
                    f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}T"
                    f"{raw[8:10]}:{raw[10:12]}:{raw[12:14]}Z"
                )
    selected = version or release or latest or (versions[-1] if versions else None)
    if not selected:
        return {"supported": True, "exists": False, "version_exists": False, "error": "no released versions found"}
    version_exists = selected in versions
    if version and not version_exists:
        return {
            "supported": True,
            "exists": True,
            "canonical_name": name,
            "version_exists": False,
            "latest_version": release or latest or (versions[-1] if versions else None),
            "latest_published_at": last_updated,
            "repository": None,
            "license": None,
        }
    pom_url = f"{base}/{urllib.parse.quote(selected, safe='')}/{artifact_q}-{urllib.parse.quote(selected, safe='')}.pom"
    pom = http_text(pom_url)
    root = ET.fromstring(pom)

    def first(local: str) -> str | None:
        for elem in root.iter():
            if elem.tag.rsplit("}", 1)[-1] == local and elem.text and elem.text.strip():
                return elem.text.strip()
        return None

    license_name = None
    for elem in root.iter():
        if elem.tag.rsplit("}", 1)[-1] == "licenses":
            for child in elem.iter():
                if child.tag.rsplit("}", 1)[-1] == "name" and child.text and child.text.strip():
                    license_name = child.text.strip()
                    break
    repository = None
    for elem in root.iter():
        if elem.tag.rsplit("}", 1)[-1] == "scm":
            for child in elem:
                local = child.tag.rsplit("}", 1)[-1]
                if local in ("url", "connection") and child.text and child.text.strip():
                    repository = child.text.strip().replace("scm:git:", "")
                    break
        if repository:
            break
    repository = repository or first("url")
    return {
        "supported": True,
        "exists": True,
        "canonical_name": name,
        "version_exists": version_exists if version else None,
        "latest_version": release or latest or (versions[-1] if versions else None),
        "latest_published_at": last_updated,
        "repository": repository,
        "license": license_name,
    }


def lookup_nuget(name: str, version: str | None) -> dict[str, Any]:
    lower = name.lower()
    versions = http_json(
        f"https://api.nuget.org/v3-flatcontainer/{urllib.parse.quote(lower, safe='')}/index.json"
    ).get("versions", [])
    if not versions:
        return {"supported": True, "exists": False, "version_exists": False, "error": "not found"}
    latest = versions[-1]
    selected = (version or latest).lower()
    version_exists = selected in {v.lower() for v in versions}
    metadata: dict[str, Any] = {}
    if version_exists:
        encoded_id = urllib.parse.quote(lower, safe="")
        encoded_version = urllib.parse.quote(selected, safe="")
        nuspec = http_text(
            f"https://api.nuget.org/v3-flatcontainer/{encoded_id}/{encoded_version}/{encoded_id}.nuspec"
        )
        root = ET.fromstring(nuspec)

        def first_text(local: str) -> str | None:
            for elem in root.iter():
                if elem.tag.rsplit("}", 1)[-1] == local and elem.text and elem.text.strip():
                    return elem.text.strip()
            return None

        repository = first_text("projectUrl")
        license_value = first_text("license")
        for elem in root.iter():
            if elem.tag.rsplit("}", 1)[-1] == "repository":
                repository = elem.attrib.get("url") or repository
            elif elem.tag.rsplit("}", 1)[-1] == "license":
                license_value = (elem.text or "").strip() or license_value
        metadata = {"repository": repository, "license": license_value or None}
    return {
        "supported": True,
        "exists": True,
        "canonical_name": name,
        "version_exists": version_exists if version else None,
        "latest_version": latest,
        "latest_published_at": None,
        **metadata,
    }


def go_escape(module: str) -> str:
    return re.sub(r"[A-Z]", lambda m: "!" + m.group(0).lower(), module)


def lookup_go(name: str, version: str | None) -> dict[str, Any]:
    escaped = urllib.parse.quote(go_escape(name), safe="/!")
    listing = http_text(f"https://proxy.golang.org/{escaped}/@v/list")
    versions = [line.strip() for line in listing.splitlines() if line.strip()]
    if not versions:
        return {"supported": True, "exists": False, "version_exists": False, "error": "not found"}
    latest = versions[-1]
    published = None
    try:
        info = http_json(
            f"https://proxy.golang.org/{escaped}/@v/{urllib.parse.quote(latest, safe='')}.info"
        )
        published = info.get("Time")
    except Exception:
        pass
    version_exists = version in versions if version else None
    repository = f"https://{name}" if name.startswith(("github.com/", "gitlab.com/")) else None
    return {
        "supported": True,
        "exists": True,
        "canonical_name": name,
        "version_exists": version_exists,
        "latest_version": latest,
        "latest_published_at": published,
        "repository": repository,
        "license": None,
    }


def registry_lookup(ecosystem: str, name: str, version: str | None) -> dict[str, Any]:
    try:
        fn = {
            "pypi": lookup_pypi,
            "npm": lookup_npm,
            "crates": lookup_crates,
            "maven": lookup_maven,
            "nuget": lookup_nuget,
            "go": lookup_go,
        }[ecosystem]
        return fn(name, version)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"supported": True, "exists": False, "version_exists": False, "error": "not found"}
        return {
            "supported": True,
            "exists": None,
            "version_exists": None,
            "error": f"registry HTTP {exc.code}",
        }
    except Exception as exc:
        return {
            "supported": True,
            "exists": None,
            "version_exists": None,
            "error": f"registry unavailable: {exc}",
        }


def osv_lookup(ecosystem: str, name: str, version: str | None) -> dict[str, Any]:
    if not version:
        return {
            "checked": False,
            "vulnerabilities": [],
            "warning": "concrete version required for OSV check",
        }
    osv_ecosystem = OSV_NAMES.get(ecosystem)
    if not osv_ecosystem:
        return {
            "checked": False,
            "vulnerabilities": [],
            "warning": "ecosystem not mapped to OSV",
        }
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


def depsdev_lookup(
    ecosystem: str,
    name: str,
    version: str | None,
    registry_latest: str | None,
) -> dict[str, Any]:
    system = DEPSDEV_SYSTEMS.get(ecosystem)
    if not system:
        return {"checked": False, "warning": "ecosystem not supported by deps.dev adapter"}
    quoted_name = urllib.parse.quote(name, safe="")
    try:
        package = http_json(f"https://api.deps.dev/v3/systems/{system}/packages/{quoted_name}")
        versions = package.get("versions", [])
        default = next(
            (v.get("versionKey", {}).get("version") for v in versions if v.get("isDefault")),
            None,
        )
        selected = version or registry_latest or default
        latest_published = None
        published_candidates = [
            v.get("publishedAt") for v in versions if v.get("publishedAt")
        ]
        if published_candidates:
            latest_published = max(published_candidates)
        result: dict[str, Any] = {
            "checked": True,
            "selected_version": selected,
            "default_version": default,
            "latest_published_at": latest_published,
            "version_count": len(versions),
        }
        if not selected:
            result["warning"] = "no version available for deps.dev version evidence"
            return result
        quoted_version = urllib.parse.quote(selected, safe="")
        detail = http_json(
            f"https://api.deps.dev/v3/systems/{system}/packages/{quoted_name}/versions/{quoted_version}"
        )
        links = detail.get("links", [])
        related = detail.get("relatedProjects", [])
        attestations = detail.get("attestations", [])
        result.update(
            {
                "published_at": detail.get("publishedAt"),
                "deprecated": bool(detail.get("isDeprecated")),
                "deprecated_reason": detail.get("deprecatedReason"),
                "licenses": detail.get("licenses", []),
                "advisories": [
                    x.get("id") for x in detail.get("advisoryKeys", []) if x.get("id")
                ],
                "links": links,
                "related_projects": related,
                "verified_attestations": sum(
                    1 for x in attestations if x.get("verified") is True
                ),
            }
        )
        return result
    except Exception as exc:
        return {"checked": False, "warning": f"deps.dev unavailable: {exc}"}


def normalize_repo_url(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if value.startswith(("git+https://", "git+http://")):
        value = value[4:]
    elif value.startswith("git://"):
        value = "https://" + value[len("git://"):]
    elif value.startswith("git+ssh://git@github.com/"):
        value = "https://github.com/" + value[len("git+ssh://git@github.com/"):]
    value = value.replace("git@github.com:", "https://github.com/")
    value = value.replace("ssh://git@github.com/", "https://github.com/")
    if value.startswith("github:"):
        value = "https://github.com/" + value.split(":", 1)[1]
    if value.endswith(".git"):
        value = value[:-4]
    return value


def github_slug(repository: str | None) -> str | None:
    value = normalize_repo_url(repository)
    if not value:
        return None
    match = re.search(r"github\.com/([^/]+)/([^/#?]+)", value)
    if not match:
        return None
    return f"{match.group(1)}/{match.group(2)}"


def source_repository(registry: dict[str, Any], depsdev: dict[str, Any]) -> str | None:
    registry_repo = normalize_repo_url(registry.get("repository"))
    if registry_repo:
        return registry_repo
    for project in depsdev.get("related_projects", []) or []:
        key = (project.get("projectKey") or {}).get("id")
        if key and project.get("relationType") == "SOURCE_REPO":
            return "https://" + key
    for link in depsdev.get("links", []) or []:
        if str(link.get("label", "")).upper() in {"SOURCE_REPO", "SOURCE", "REPOSITORY"}:
            return normalize_repo_url(link.get("url"))
    return None


def github_repository_health(repository: str | None) -> dict[str, Any]:
    slug = github_slug(repository)
    if not slug:
        return {"checked": False, "warning": "source repository is not a GitHub repository"}
    headers: dict[str, str] = {}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    try:
        data = http_json(f"https://api.github.com/repos/{slug}", extra_headers=headers)
        pushed_at = data.get("pushed_at")
        return {
            "checked": True,
            "repository": slug,
            "archived": bool(data.get("archived")),
            "disabled": bool(data.get("disabled")),
            "fork": bool(data.get("fork")),
            "pushed_at": pushed_at,
            "push_age_days": iso_to_age_days(pushed_at),
            "open_issues_count": data.get("open_issues_count"),
            "default_branch": data.get("default_branch"),
        }
    except Exception as exc:
        return {"checked": False, "repository": slug, "warning": f"GitHub evidence unavailable: {exc}"}


def normalize_name(name: str) -> str:
    value = name.lower().strip()
    if "/" in value and value.startswith("@"):
        value = value.split("/", 1)[1]
    return re.sub(r"[-_.]+", "", value)


def name_similarity_signal(name: str, candidates: list[str]) -> dict[str, Any]:
    target = normalize_name(name)
    rows: list[dict[str, Any]] = []
    for candidate in sorted(set(candidates)):
        other = normalize_name(candidate)
        if not other or other == target:
            continue
        score = difflib.SequenceMatcher(a=target, b=other).ratio()
        if score >= 0.78:
            rows.append({"candidate": candidate, "similarity": round(score, 3)})
    rows.sort(key=lambda x: x["similarity"], reverse=True)
    suspicious = [x for x in rows if x["similarity"] >= 0.86]
    return {
        "checked": True,
        "candidates_checked": len(set(candidates)),
        "suspicious": suspicious[:10],
        "nearest": rows[:10],
    }


def project_dependency_names(root: Path | None, ecosystem: str) -> list[str]:
    if not root or not root.exists():
        return []
    names: set[str] = set()
    if ecosystem == "npm":
        path = root / "package.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                    names.update((data.get(key) or {}).keys())
            except Exception:
                pass
    elif ecosystem == "pypi":
        for path in root.glob("requirements*.txt"):
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith(("#", "-", "git+", "http:")):
                    continue
                match = re.match(r"([A-Za-z0-9][A-Za-z0-9._-]*)", line)
                if match:
                    names.add(match.group(1))
    elif ecosystem == "crates":
        path = root / "Cargo.toml"
        if path.exists():
            in_deps = False
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                stripped = line.strip()
                if stripped.startswith("["):
                    in_deps = bool(re.match(r"^\[(dev-|build-)?dependencies", stripped))
                    continue
                if in_deps:
                    match = re.match(r"([A-Za-z0-9_-]+)\s*=", stripped)
                    if match:
                        names.add(match.group(1))
    elif ecosystem == "go":
        path = root / "go.mod"
        if path.exists():
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                match = re.match(r"\s*([A-Za-z0-9._~/-]+)\s+v\d", line)
                if match:
                    names.add(match.group(1))
    elif ecosystem == "nuget":
        for path in root.rglob("*.csproj"):
            text = path.read_text(encoding="utf-8", errors="replace")
            names.update(re.findall(r'<PackageReference\s+Include="([^"]+)"', text))
    elif ecosystem == "maven":
        path = root / "pom.xml"
        if path.exists():
            try:
                tree = ET.fromstring(path.read_text(encoding="utf-8"))
                for dep in tree.iter():
                    if dep.tag.rsplit("}", 1)[-1] != "dependency":
                        continue
                    group = artifact = None
                    for child in dep:
                        local = child.tag.rsplit("}", 1)[-1]
                        if local == "groupId":
                            group = (child.text or "").strip()
                        elif local == "artifactId":
                            artifact = (child.text or "").strip()
                    if group and artifact:
                        names.add(f"{group}:{artifact}")
            except Exception:
                pass
    return sorted(names)


def effective_licenses(registry: dict[str, Any], depsdev: dict[str, Any]) -> list[str]:
    values: list[str] = []
    raw = registry.get("license")
    if raw:
        values.append(str(raw))
    for item in depsdev.get("licenses", []) or []:
        if item and item not in values:
            values.append(str(item))
    return values


def license_policy_signal(
    licenses: list[str],
    allow: list[str],
    deny: list[str],
) -> dict[str, Any]:
    upper = [x.upper() for x in licenses]
    denied = [
        policy for policy in deny
        if any(re.search(rf"(^|[^A-Z0-9.-]){re.escape(policy.upper())}([^A-Z0-9.-]|$)", item) for item in upper)
    ]
    allowed_match = [
        policy for policy in allow
        if any(re.search(rf"(^|[^A-Z0-9.-]){re.escape(policy.upper())}([^A-Z0-9.-]|$)", item) for item in upper)
    ]
    return {
        "checked": bool(allow or deny),
        "licenses": licenses,
        "allowed_policy": allow,
        "denied_policy": deny,
        "denied_matches": denied,
        "allowed_matches": allowed_match,
    }


def maintenance_signal(registry: dict[str, Any], depsdev: dict[str, Any]) -> dict[str, Any]:
    latest = depsdev.get("latest_published_at") or registry.get("latest_published_at")
    return {
        "latest_published_at": latest,
        "latest_release_age_days": iso_to_age_days(latest),
        "deprecated": bool(depsdev.get("deprecated")),
        "deprecated_reason": depsdev.get("deprecated_reason"),
        "version_count": depsdev.get("version_count"),
    }


def decide(
    registry: dict[str, Any],
    osv: dict[str, Any],
    version: str | None,
) -> tuple[str, list[str]]:
    """Backward-compatible baseline decision used by deterministic legacy tests."""
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


def evaluate_dependency(
    registry: dict[str, Any],
    osv: dict[str, Any],
    depsdev: dict[str, Any],
    repo_health: dict[str, Any],
    similarity: dict[str, Any],
    maintenance: dict[str, Any],
    license_signal: dict[str, Any],
    version: str | None,
    risk_tier: int,
    necessity: str,
    purpose: str | None,
) -> tuple[str, list[dict[str, str]]]:
    signals: list[dict[str, str]] = []

    def add(level: str, code: str, message: str) -> None:
        signals.append({"level": level, "code": code, "message": message})

    if registry.get("exists") is False:
        add("reject", "registry.missing", "package does not exist in the expected official registry")
    elif registry.get("exists") is None:
        add("review", "registry.unavailable", str(registry.get("error") or "registry evidence unavailable"))
    if version and registry.get("version_exists") is False:
        add("reject", "registry.version_missing", "requested version does not exist in the official registry")
    if not version:
        add("review", "version.unspecified", "a concrete version is required for version-specific dependency evidence")

    if osv.get("vulnerabilities"):
        add("review", "osv.vulnerable", "OSV reports known vulnerabilities for the requested version")
    if depsdev.get("advisories"):
        add("review", "depsdev.advisory", "deps.dev reports security advisories for the selected version")
    if not osv.get("checked"):
        add("review", "osv.unavailable", str(osv.get("warning") or "OSV evidence unavailable"))

    if necessity == "unknown":
        add("review", "necessity.unknown", "dependency necessity has not been justified")
    if necessity != "unknown" and not (purpose or "").strip():
        add("review", "necessity.no_purpose", "dependency purpose must be recorded for a justified necessity decision")

    repository = source_repository(registry, depsdev)
    if not repository:
        add("review", "provenance.repository_missing", "source repository/provenance URL is unavailable")

    licenses = license_signal.get("licenses", [])
    if not licenses:
        add("review", "license.missing", "license metadata is unavailable")
    if license_signal.get("denied_matches"):
        add("reject", "license.denied", "package license matches an explicitly denied project policy")
    if license_signal.get("allowed_policy") and not license_signal.get("allowed_matches"):
        add("review", "license.not_allowlisted", "package license does not match the project's explicit allow-list")

    if similarity.get("suspicious"):
        nearest = similarity["suspicious"][0]
        add(
            "review",
            "name.similar",
            f"package name is highly similar to {nearest['candidate']!r}; verify typo-squatting risk",
        )

    if maintenance.get("deprecated"):
        add("review", "maintenance.deprecated", "package/version is marked deprecated")
    age = maintenance.get("latest_release_age_days")
    if age is not None:
        if risk_tier >= 2 and age > 730:
            add("review", "maintenance.stale", f"latest known release is {age} days old")
        elif risk_tier <= 1 and age > 1095:
            add("review", "maintenance.stale", f"latest known release is {age} days old")

    if risk_tier >= 2:
        if not depsdev.get("checked"):
            add("review", "depsdev.unavailable", str(depsdev.get("warning") or "deps.dev evidence unavailable"))
        if repository and not repo_health.get("checked"):
            add("review", "repository.health_unavailable", str(repo_health.get("warning") or "source repository health unavailable"))
        if repo_health.get("archived"):
            add("review", "repository.archived", "source repository is archived")
        if repo_health.get("disabled"):
            add("review", "repository.disabled", "source repository is disabled")
        push_age = repo_health.get("push_age_days")
        if push_age is not None and push_age > 730:
            add("review", "repository.stale", f"source repository has not been pushed for {push_age} days")

    if risk_tier >= 3:
        if depsdev.get("checked") and int(depsdev.get("verified_attestations") or 0) == 0:
            add("review", "provenance.attestation_missing", "no verified build/publish attestation is visible in deps.dev")

    if any(x["level"] == "reject" for x in signals):
        return "REJECT", signals
    if any(x["level"] == "review" for x in signals):
        return "REVIEW REQUIRED", signals
    return "ACCEPT", [
        {
            "level": "pass",
            "code": "dependency.evidence_complete",
            "message": "risk-appropriate automated evidence and explicit necessity justification passed",
        }
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ecosystem", choices=list(OSV_NAMES))
    ap.add_argument("package")
    ap.add_argument("--version")
    ap.add_argument("--risk-tier", type=int, choices=[0, 1, 2, 3], default=1)
    ap.add_argument(
        "--necessity",
        choices=["required", "optional", "replacement", "unknown"],
        default="unknown",
    )
    ap.add_argument("--purpose")
    ap.add_argument("--project-root")
    ap.add_argument("--compare-name", action="append", default=[])
    ap.add_argument("--allow-license", action="append", default=[])
    ap.add_argument("--deny-license", action="append", default=[])
    ap.add_argument("--skip-osv", action="store_true")
    ap.add_argument("--skip-deps-dev", action="store_true")
    ap.add_argument("--skip-repo-health", action="store_true")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    registry = registry_lookup(ns.ecosystem, ns.package, ns.version)
    osv = (
        {"checked": False, "vulnerabilities": [], "warning": "OSV check explicitly skipped"}
        if ns.skip_osv
        else osv_lookup(ns.ecosystem, ns.package, ns.version)
    )
    depsdev = (
        {"checked": False, "warning": "deps.dev check explicitly skipped"}
        if ns.skip_deps_dev
        else depsdev_lookup(ns.ecosystem, ns.package, ns.version, registry.get("latest_version"))
    )

    repository = source_repository(registry, depsdev)
    repo_health = (
        {"checked": False, "warning": "source repository health check explicitly skipped"}
        if ns.skip_repo_health
        else github_repository_health(repository)
    )

    project_root = Path(ns.project_root).resolve() if ns.project_root else None
    comparison_names = list(ns.compare_name)
    comparison_names.extend(project_dependency_names(project_root, ns.ecosystem))
    canonical = registry.get("canonical_name")
    if canonical and normalize_name(str(canonical)) != normalize_name(ns.package):
        comparison_names.append(str(canonical))
    similarity = name_similarity_signal(ns.package, comparison_names)

    licenses = effective_licenses(registry, depsdev)
    license_signal = license_policy_signal(licenses, ns.allow_license, ns.deny_license)
    maintenance = maintenance_signal(registry, depsdev)

    decision, signals = evaluate_dependency(
        registry,
        osv,
        depsdev,
        repo_health,
        similarity,
        maintenance,
        license_signal,
        ns.version,
        ns.risk_tier,
        ns.necessity,
        ns.purpose,
    )

    result = {
        "schema_version": 2,
        "ecosystem": ns.ecosystem,
        "package": ns.package,
        "version": ns.version,
        "risk_tier": ns.risk_tier,
        "decision": decision,
        "judgment": {
            "necessity": ns.necessity,
            "purpose": ns.purpose,
            "note": "Necessity is an explicit project/agent judgment, not an automated trust score.",
        },
        "evidence": {
            "registry": registry,
            "osv": osv,
            "deps_dev": depsdev,
            "repository_health": repo_health,
            "name_similarity": similarity,
            "maintenance": maintenance,
            "license": license_signal,
        },
        "signals": signals,
        "reasons": [x["message"] for x in signals],
        "note": (
            "ACCEPT means the risk-appropriate evidence gate passed. It does not prove the package "
            "is safe, legally compatible, necessary, or appropriate in every deployment context."
        ),
    }

    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Dependency Decision: {decision}")
        for signal in signals:
            print(f"- [{signal['code']}] {signal['message']}")
    return 2 if decision == "REJECT" else (1 if decision == "REVIEW REQUIRED" else 0)


if __name__ == "__main__":
    raise SystemExit(main())
