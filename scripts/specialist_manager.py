#!/usr/bin/env python3
"""Resolve current registered skills, install safely, and return scoped handoffs."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import io
import json
import os
import posixpath
import re
import shutil
import stat
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config/specialists.json"
MAX_BYTES = 64 * 1024 * 1024
TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".txt", ".svg", ".toml"}
PACKAGE_ADAPTER = 2
COMPATIBILITY_AREAS = {"authority", "platform", "dependencies", "verification", "scope-authorization"}
MAX_REVIEW_BYTES = 128 * 1024
RESOURCE_RE = re.compile(r"(?<![\w:/])(?:\.{1,2}/)*(?:references|upstream-references|packs|scripts|config|assets)/[A-Za-z0-9_./-]+\.(?:md|py|json|ya?ml|svg)(?![\w.-])")
LINK_RE = re.compile(r"\]\((?P<path>[A-Za-z0-9_./-]+\.(?:md|py|json|ya?ml|svg))(?:#[^\s)]*)?\)")


def registry() -> dict:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if data.get("schema_version") != 2 or data.get("lifecycle") != ["discover", "define", "plan", "design", "build", "verify", "review", "ship"]:
        raise ValueError("invalid specialist lifecycle schema")
    entries = [data["head"], *data["specialists"]]
    names, skills = set(), set()
    for entry in entries:
        if (entry["id"] in names or entry["skill_name"] in skills
                or any(not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", entry[key]) for key in ("id", "skill_name"))):
            raise ValueError("invalid or duplicate registered skill")
        names.add(entry["id"])
        skills.add(entry["skill_name"])
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", entry["repository"]):
            raise ValueError("invalid canonical repository")
        path = PurePosixPath(entry["skill_path"])
        if path.is_absolute() or ".." in path.parts or "\\" in entry["skill_path"] or ":" in entry["skill_path"]:
            raise ValueError("invalid installable skill path")
        if any(key in entry for key in ("version", "ref", "commit", "tag")):
            raise ValueError("fixed dependency revisions are not permitted")
        if entry in data["specialists"]:
            if (entry.get("mode") != "head-delegated" or entry.get("requirement") != "required-on-match"
                    or not set(entry.get("primary_stages", [])) <= set(entry.get("stages", []))
                    or not set(entry.get("stages", [])) <= set(data["lifecycle"])):
                raise ValueError("invalid specialist stage or authority contract")
            if entry.get("shared_resources", []) not in ([], ["references"]):
                raise ValueError("unapproved shared resource root")
            for pattern in entry["activation"].get("path_patterns", []):
                re.compile(pattern)
    if data["primary_ui_specialist"] not in {item["id"] for item in data["specialists"]} or data["policy"] != {
        "version_strategy": "latest-stable-release-or-default-branch", "allow_version_pins": False,
        "head_precedence": True, "inventory_interval_hours": 24,
    }:
        raise ValueError("invalid specialist freshness or precedence policy")
    return data


def select_specialists(task: str, paths: list[str] | None = None,
                       facts: dict | None = None, explicit: list[str] | None = None,
                       stage: str = "discover", risk_facts: dict | None = None) -> list[dict]:
    data = registry()
    entries = {item["id"]: item for item in data["specialists"]}
    if stage not in data["lifecycle"]:
        raise ValueError("unknown lifecycle stage")
    if any(name not in entries for name in explicit or []):
        raise ValueError("select registered specialists only")
    concerns = (facts or {}).get("concern", [])
    concerns = {concerns} if isinstance(concerns, str) else set(concerns)
    if (risk_facts or {}).get("data_sensitivity") in {"personal", "sensitive", "financial", "payment", "health", "credentials", "secret", "private-key"}:
        concerns.add("sensitive-data")
    paths = [path.replace("\\", "/") for path in paths or []]
    # Documentation edits do not change the discussed runtime boundary.
    documents_only = bool(paths) and all(Path(path).suffix.casefold() in {".md", ".txt", ".rst"} for path in paths)
    selected = []
    for entry in entries.values():
        activation = entry["activation"]
        reasons = []
        if entry["id"] in (explicit or []):
            reasons.append("explicit specialist selection")
        if concerns & set(activation["concerns"]):
            reasons.append("structured domain concern")
        if not documents_only:
            if any(re.search(r"(?<!\w)" + re.escape(term.casefold()) + r"(?!\w)", task.casefold()) for term in activation["terms"]):
                reasons.append("task domain signal; confirm affected boundary")
            if any(Path(path).suffix.casefold() in activation["extensions"] for path in paths):
                reasons.append("affected domain surface")
            if any(re.search(pattern, path.casefold()) for pattern in activation["path_patterns"] for path in paths):
                reasons.append("affected domain boundary")
        if reasons:
            selected.append({**entry, "reason": "; ".join(reasons), "required": True, "head_precedence": True,
                             "stage": stage, "active_in_stage": stage in entry["stages"],
                             "permissions": data["permissions"], "stage_owner": data["head"]["id"],
                             "handoff_required": True})
    return selected


def supported_concerns() -> set[str]:
    return {concern for item in registry()["specialists"] for concern in item["activation"]["concerns"]}


def resource_references(text: str) -> list[tuple[int, int, str]]:
    # Keep exact relative prefixes; stripping ../../ would validate a different file.
    matches = [(match.start(), match.end(), match.group()) for match in RESOURCE_RE.finditer(text)]
    for match in LINK_RE.finditer(text):
        start, end = match.span("path")
        if not any(a <= start and end <= b for a, b, _ in matches):
            matches.append((start, end, match.group("path")))
    return sorted(matches)


def resolve_resource(owner: str, reference: str) -> str:
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(owner), reference))
    if resolved == ".." or resolved.startswith("../") or resolved.startswith("/") or ":" in resolved:
        raise ValueError("external required resource: " + reference)
    return resolved


def request_bytes(url: str) -> bytes:
    headers = {"User-Agent": "vibe-coding-skill-current-source"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token and urllib.parse.urlparse(url).netloc == "api.github.com":
        headers["Authorization"] = "Bearer " + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        payload = response.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES:
        raise ValueError("source response exceeds size limit")
    return payload


def api(endpoint: str) -> dict:
    return json.loads(request_bytes("https://api.github.com/" + endpoint))


def resolve_latest(entry: dict) -> dict:
    base = "repos/" + entry["repository"]
    try:
        release = api(base + "/releases/latest")
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        metadata = api(base)
        ref, channel = metadata["default_branch"], "default-branch"
    else:
        if release.get("draft") or release.get("prerelease") or not release.get("tag_name"):
            raise ValueError("latest stable release metadata is invalid")
        ref, channel = release["tag_name"], "stable-release"
    commit = api(base + "/commits/" + urllib.parse.quote(ref, safe=""))["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("upstream did not return an immutable source revision")
    return {"repository": entry["repository"], "skill_path": entry["skill_path"],
            "commit": commit, "channel": channel, "ref": ref}


def validate_package(files: dict[str, bytes], name: str) -> None:
    text = files.get("SKILL.md", b"").decode("utf-8")
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        raise ValueError("missing Skill frontmatter")
    sections = text.split("---", 2)
    if len(sections) != 3 or not sections[2].strip():
        raise ValueError("missing Skill body or frontmatter delimiter")
    frontmatter = sections[1]
    if not re.search(r"(?m)^name:\s*[\"']?" + re.escape(name) + r"[\"']?\s*$", frontmatter):
        raise ValueError("installed Skill identity differs from registry")
    for _, _, reference in resource_references(text):
        if resolve_resource("SKILL.md", reference) not in files:
            raise ValueError("missing or external required resource: " + reference)
    for reference in ("product-types.json", "specialists.json", "vibe-head-contract.md"):
        if "`" + reference + "`" in text and reference not in files:
            raise ValueError("missing specialist routing resource: " + reference)
    for path, content in files.items():
        if path.endswith(".json"):
            json.loads(content)
        if path.endswith(".md"):
            for match in LINK_RE.finditer(content.decode("utf-8")):
                reference = match.group("path")
                if resolve_resource(path, reference) not in files:
                    raise ValueError("broken relative link in " + path + ": " + reference)


def adapt_resources(files: dict[str, bytes], entry: dict) -> dict[str, bytes]:
    """Make approved shared references self-contained without importing other skills."""
    base = entry["skill_path"].strip("/")
    prefix = base + "/" if base != "." else ""
    selected = {path for path in files if path.startswith(prefix)}
    destinations = {path: path[len(prefix):] for path in selected}
    pending = list(selected)
    replacements = {}
    while pending:
        owner = pending.pop()
        if not owner.endswith(".md"):
            continue
        refs = resource_references(files[owner].decode("utf-8"))
        for start, end, reference in refs:
            resolved = resolve_resource(owner, reference)
            if resolved not in files:
                raise ValueError("missing upstream resource: " + resolved)
            if resolved not in destinations:
                if not any(resolved.startswith(root + "/") for root in entry.get("shared_resources", [])):
                    raise ValueError("resource outside approved package roots: " + resolved)
                destinations[resolved] = "upstream-references/" + resolved.split("/", 1)[1]
                pending.append(resolved)
            replacements.setdefault(owner, []).append((start, end, resolved))
    result = {}
    for owner, destination in destinations.items():
        content = files[owner]
        if owner in replacements:
            text = content.decode("utf-8")
            for start, end, resolved in sorted(replacements[owner], reverse=True):
                relative = posixpath.relpath(destinations[resolved], posixpath.dirname(destination) or ".")
                text = text[:start] + relative + text[end:]
            content = text.encode("utf-8")
        if destination.casefold() in {path.casefold() for path in result}:
            raise ValueError("adapted resource name collision")
        result[destination] = content
    return result


def source_package(entry: dict, source: dict) -> dict[str, bytes]:
    payload = request_bytes("https://codeload.github.com/" + entry["repository"] + "/zip/" + source["commit"])
    files: dict[str, bytes] = {}
    with ZipFile(io.BytesIO(payload)) as archive:
        roots = {item.filename.split("/")[0] for item in archive.infolist()}
        if len(roots) != 1 or sum(item.file_size for item in archive.infolist()) > MAX_BYTES:
            raise ValueError("invalid or oversized source archive")
        prefix = next(iter(roots)) + "/"
        skill_prefix = (PurePosixPath(entry["skill_path"]).as_posix() + "/" if entry["skill_path"] != "." else "")
        seen = set()
        for item in archive.infolist():
            path = PurePosixPath(item.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in item.filename:
                raise ValueError("unsafe archive path")
            if item.filename.endswith("/"):
                continue
            source_relative = item.filename[len(prefix):]
            if not (source_relative.startswith(skill_prefix) or any(source_relative.startswith(root + "/") for root in entry.get("shared_resources", []))):
                continue
            if stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError("symlinks are not supported in specialist packages")
            relative = source_relative
            reserved = {"con", "prn", "aux", "nul", *("com" + str(n) for n in range(1, 10)), *("lpt" + str(n) for n in range(1, 10))}
            if (relative.casefold() in seen or ":" in relative
                    or any(part.endswith((".", " ")) or part.split(".")[0].casefold() in reserved for part in PurePosixPath(relative).parts)):
                raise ValueError("duplicate or unsafe package member")
            seen.add(relative.casefold())
            files[relative] = archive.read(item)
        files = adapt_resources(files, entry) if entry.get("shared_resources") else {name[len(skill_prefix):]: content for name, content in files.items() if name.startswith(skill_prefix)}
        for name in ("VERSION", "LICENSE"):
            if prefix + name in archive.namelist() and name not in files:
                files[name] = archive.read(prefix + name)
    if entry.get("mode") == "head-delegated":
        contract = (ROOT / "references/specialist-authority.md").read_bytes()
        if "vibe-head-contract.md" in files:
            raise ValueError("upstream collides with the Head composition resource")
        files["vibe-head-contract.md"] = contract
        text = files.get("SKILL.md", b"").decode("utf-8")
        parts = text.split("---", 2)
        if len(parts) != 3:
            raise ValueError("missing Skill frontmatter")
        parts[2] = ("\n\n## Vibe Head-delegated use\n\n"
                    "When Vibe assigns this specialist, read [vibe-head-contract.md](vibe-head-contract.md) first. "
                    "Follow the assigned stage and domain boundary; Vibe controls override standalone workflow defaults. "
                    "The upstream domain guidance follows unchanged apart from resource relocation.\n" + parts[2])
        files["SKILL.md"] = "---".join(parts).encode("utf-8")
    validate_package(files, entry["skill_name"])
    return files


def digest(path: str, content: bytes) -> str:
    if Path(path).suffix in TEXT_SUFFIXES or path in ("VERSION", "LICENSE"):
        content = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def installed_hashes(target: Path) -> dict[str, str]:
    result = {}
    if not target.exists():
        return result
    if target.is_symlink():
        raise ValueError("registered installation must not be a symlink")
    if not target.is_dir():
        raise ValueError("registered installation must be a directory")
    for path in target.rglob("*"):
        if path.is_symlink():
            raise ValueError("symlink in managed installation")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            rel = path.relative_to(target).as_posix()
            result[rel] = digest(rel, path.read_bytes())
    return result


def write_record(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


@contextmanager
def installation_lock(skills_dir: Path):
    """A short-lived host lock also protects callers with different state directories."""
    skills_dir.parent.mkdir(parents=True, exist_ok=True)
    lock = skills_dir.parent / ("." + skills_dir.name + "-vibe-update-lock")
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise ValueError("another skill update is active; inspect the host lock if a previous process crashed") from exc
    try:
        yield
    finally:
        lock.rmdir()


def ensure(entry: dict, skills_dir: Path, state: Path, apply: bool = False) -> dict:
    target = skills_dir / entry["skill_name"]
    record_path = state / (entry["id"] + ".json")
    try:
        current = installed_hashes(target)
        previous = json.loads(record_path.read_text(encoding="utf-8")) if record_path.exists() else None
        if previous is not None and (not isinstance(previous.get("files"), dict)
                                     or not isinstance(previous.get("source"), dict)):
            raise ValueError("invalid installation provenance")
    except (OSError, ValueError, AttributeError) as exc:
        return {"id": entry["id"], "status": "installation-unverified", "error": str(exc)}
    try:
        source = {**resolve_latest(entry), "package_policy": hashlib.sha256(json.dumps({
            "adapter": PACKAGE_ADAPTER, "skill_path": entry["skill_path"],
            "shared_resources": entry.get("shared_resources", []),
            "head_contract": hashlib.sha256((ROOT / "references/specialist-authority.md").read_bytes()).hexdigest() if entry.get("mode") == "head-delegated" else None,
        }, sort_keys=True).encode()).hexdigest()}
    except (OSError, ValueError, KeyError) as exc:
        return {"id": entry["id"], "status": "currency-unverified", "error": type(exc).__name__}
    result = {"id": entry["id"], "source": source, "skill_path": str(target / "SKILL.md"),
              "checked_at": datetime.now(timezone.utc).isoformat(), "updated": False}
    managed = previous and previous.get("installation") == str(target) and previous.get("source", {}).get("repository") == entry["repository"]
    if managed and current and current != previous["files"]:
        return {**result, "status": "local-modifications", "action": "preserve local edits before updating"}
    if (managed and current and previous["source"]["commit"] == source["commit"]
            and previous["source"].get("skill_path") == entry["skill_path"]
            and previous["source"].get("package_policy") == source["package_policy"]):
        write_record(record_path, {**result, "files": current, "installation": str(target), "status": "current"})
        return {**result, "status": "current"}
    if any((state / "active-assignments" / entry["id"]).glob("*.json")):
        return {**result, "status": "update-deferred-active-assignment",
                "action": "finish or explicitly abandon the active assignment before replacing its instructions"}
    try:
        files = source_package(entry, source)
    except (OSError, ValueError, KeyError, BadZipFile) as exc:
        return {**result, "status": "latest-incompatible", "error": str(exc)}
    wanted = {rel: digest(rel, data) for rel, data in files.items()}
    if current == wanted:
        result["status"] = "current"
    elif not apply:
        return {**result, "status": "outdated" if current else "missing", "action": "rerun with --apply within authorized scope"}
    else:
        skills_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".vibe-stage-", dir=skills_dir.parent) as temporary:
            staging = Path(temporary) / "candidate"
            staging.mkdir()
            for relative, content in files.items():
                path = staging / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            old = Path(temporary) / "previous"
            if target.exists():
                backup = state / "backups" / entry["id"] / uuid.uuid4().hex
                shutil.copytree(target, backup)
                result["backup"] = str(backup)
                os.replace(target, old)
            try:
                os.replace(staging, target)
                result.update(status="current", updated=True)
                write_record(record_path, {**result, "files": wanted, "installation": str(target)})
            except BaseException:
                if target.exists():
                    os.replace(target, Path(temporary) / "failed")
                if old.exists():
                    os.replace(old, target)
                raise
        return result
    write_record(record_path, {**result, "files": wanted, "installation": str(target)})
    return result


def canonical_digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def read_local_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("missing/oversized compatibility record")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("compatibility record must be an object")
    return value


def compatibility_packet(entry: dict, skills_dir: Path, state: Path, installation: dict) -> dict:
    """Describe actual changes for a Head assessment; never infer semantic approval."""
    target = skills_dir / entry["skill_name"]
    record = read_local_json(state / (entry["id"] + ".json"))
    files = installed_hashes(target)
    if (installation.get("status") != "current" or not files or record.get("files") != files
            or record.get("source") != installation.get("source") or record.get("installation") != str(target)):
        raise ValueError("compatibility needs a verified current managed installation")
    source = installation["source"]
    binding = {"specialist_id": entry["id"],
               "source": {k: source[k] for k in ("repository", "skill_path", "commit", "package_policy")}, "files": files,
               "head_controls": registry()["permissions"],
               "domain": {k: entry.get(k) for k in ("mode", "capability", "assignment", "stages", "primary_stages")}}
    key = canonical_digest(binding)
    home = state / "compatibility" / entry["id"]
    cached = home / key
    if (cached / "assessment.json").exists():
        if read_local_json(cached / "binding.json") != binding:
            raise ValueError("compatibility cache binding altered")
        review = read_local_json(cached / "review.json")
        if (set(review) != {"changed_resources", "required_review_paths", "previous_revision", "previous_resource_root"}
                or not isinstance(review["changed_resources"], list) or not isinstance(review["required_review_paths"], list)
                or any(not isinstance(p, str) for p in review["required_review_paths"])
                or any(not isinstance(r, dict) or not isinstance(r.get("path"), str) for r in review["changed_resources"])):
            raise ValueError("invalid retained compatibility review context")
        return {"binding_sha256": key, "upstream_revision": source["commit"],
                "head_contract_sha256": source["package_policy"], "binding": binding,
                **review, "resource_root": str(target), "assessment_path": str(cached / "assessment.json"), "reused": True}
    baseline = read_local_json(home / "latest.json") if (home / "latest.json").exists() else {}
    old_key = baseline.get("binding_sha256")
    if old_key is not None and not re.fullmatch(r"[0-9a-f]{64}", str(old_key)):
        raise ValueError("invalid compatibility baseline identity")
    previous = read_local_json(home / old_key / "binding.json") if old_key else {}
    old_files = previous.get("files", {})
    if not isinstance(old_files, dict):
        raise ValueError("invalid compatibility baseline manifest")
    changed = sorted(p for p in files.keys() | old_files.keys() if files.get(p) != old_files.get(p))
    # License/version-only changes need provenance review, not a domain-methodology reread.
    review_paths = sorted((set(changed) - {"LICENSE", "VERSION"}) | {"SKILL.md"}
                          | ({"vibe-head-contract.md"} if "vibe-head-contract.md" in files else set()))
    changes = [{"path": p, "action": "add" if p not in old_files else "delete" if p not in files else "modify",
                "before_sha256": old_files.get(p), "after_sha256": files.get(p)} for p in changed]
    diffs, remaining, total = [], MAX_REVIEW_BYTES, 0
    for p in review_paths:
        path = PurePosixPath(p)
        if path.is_absolute() or ".." in path.parts or "\\" in p or ":" in p:
            raise ValueError("unsafe compatibility resource")
        before = home / old_key / "resources" / p if old_key else None
        after = target / p
        for resource in (before, after if p in files else None):
            if resource and resource.is_file():
                total += resource.stat().st_size
                if resource.is_symlink() or total > 2 * MAX_BYTES:
                    raise ValueError("unsafe/oversized compatibility resources")
        old = before.read_bytes() if before and before.is_file() else b""
        new = after.read_bytes() if p in files else b""
        if before and p in old_files and (not before.is_file() or digest(p, old) != old_files[p]):
            raise ValueError("compatibility baseline resource changed or missing")
        if p in files and digest(p, new) != files[p]:
            raise ValueError("specialist resource changed during review preparation")
        diff = "".join(difflib.unified_diff(old.decode("utf-8", errors="replace").splitlines(True),
                                        new.decode("utf-8", errors="replace").splitlines(True),
                                        fromfile="previous/" + p, tofile="current/" + p))
        raw = diff.encode("utf-8")
        excerpt = raw[:remaining].decode("utf-8", errors="ignore")
        diffs.append({"path": p, "diff": excerpt, "truncated": len(raw) > remaining})
        remaining = max(0, remaining - len(excerpt.encode("utf-8")))
    return {"binding_sha256": key, "upstream_revision": source["commit"],
            "head_contract_sha256": source["package_policy"], "binding": binding,
            "previous_revision": previous.get("source", {}).get("commit"),
            "changed_resources": changes, "required_review_paths": review_paths, "diffs": diffs,
            "resource_root": str(target), "previous_resource_root": str(home / old_key / "resources") if old_key else None,
            "assessment_path": str(home / key / "assessment.json")}


def validate_assessment(value: dict, entry: dict, packet: dict) -> None:
    allowed = {"format", "schema_version", "specialist_id", "binding_sha256", "upstream_revision", "head_contract_sha256",
               "decision", "assessed_by", "assessed_at", "reason", "reviewed_paths", "checks", "conflicts"}
    if set(value) - allowed or value.get("format") != "vibe-specialist-compatibility" or type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise ValueError("unsupported compatibility assessment format")
    for k, expected in (("specialist_id", entry["id"]), *((k, packet[k]) for k in ("binding_sha256", "upstream_revision", "head_contract_sha256"))):
        if value.get(k) != expected:
            raise ValueError("compatibility assessment binding mismatch: " + k)
    if value.get("decision") not in ("accepted", "changes-required", "blocked"):
        raise ValueError("invalid Head compatibility decision")
    for k in ("assessed_by", "reason", "assessed_at"):
        if not isinstance(value.get(k), str) or not value[k].strip():
            raise ValueError("concrete Head assessment metadata required")
    if datetime.fromisoformat(value["assessed_at"].replace("Z", "+00:00")).tzinfo is None:
        raise ValueError("assessment needs a timezone-aware timestamp")
    reviewed = value.get("reviewed_paths")
    if not isinstance(reviewed, list) or any(not isinstance(p, str) for p in reviewed) or len(set(reviewed)) != len(reviewed):
        raise ValueError("invalid reviewed resources")
    if not set(packet["required_review_paths"]) <= set(reviewed) or not set(reviewed) <= set(packet["binding"]["files"]) | {r["path"] for r in packet["changed_resources"]}:
        raise ValueError("assessment did not inspect required changed resources")
    checks, conflicts = value.get("checks"), value.get("conflicts")
    if not isinstance(conflicts, list) or any(not isinstance(c, str) or not c.strip() for c in conflicts):
        raise ValueError("invalid compatibility conflicts")
    if not isinstance(checks, list) or len(checks) != len(COMPATIBILITY_AREAS):
        raise ValueError("assessment must cover the five relevant compatibility areas")
    areas = set()
    for check in checks:
        if not isinstance(check, dict) or set(check) != {"area", "status", "rationale", "resource_paths"}:
            raise ValueError("invalid compatibility area assessment")
        if check["area"] not in COMPATIBILITY_AREAS or check["area"] in areas or check["status"] not in ("compatible", "overridden", "conflict"):
            raise ValueError("invalid or duplicate compatibility area")
        areas.add(check["area"])
        if not isinstance(check["rationale"], str) or not check["rationale"].strip():
            raise ValueError("each compatibility area needs a concrete rationale")
        refs = check["resource_paths"]
        if not isinstance(refs, list) or not refs or any(not isinstance(p, str) or p not in reviewed for p in refs):
            raise ValueError("compatibility rationale needs inspected resource references")
        if check["status"] == "overridden" and "vibe-head-contract.md" not in refs:
            raise ValueError("overridden defaults need the effective Head contract reference")
    if value["decision"] == "accepted" and (conflicts or any(c["status"] == "conflict" for c in checks)):
        raise ValueError("unresolved compatibility conflicts cannot be accepted")


def compatibility(entry: dict, skills_dir: Path, state: Path, installation: dict, assessment=None) -> dict:
    try:
        packet = compatibility_packet(entry, skills_dir, state, installation)
        path = Path(packet["assessment_path"])
        if assessment is not None:
            validate_assessment(assessment, entry, packet)
            home = path.parent
            # Capture a bounded review baseline outside discovery; never execute its resources.
            if not (home / "binding.json").exists():
                home.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(prefix=".review-", dir=home.parent) as temporary:
                    staging, total = Path(temporary) / "candidate", 0
                    staging.mkdir()
                    for rel, expected in packet["binding"]["files"].items():
                        source_path = skills_dir / entry["skill_name"] / rel
                        if source_path.stat().st_size > MAX_BYTES - total:
                            raise ValueError("compatibility snapshot oversized")
                        raw = source_path.read_bytes()
                        total += len(raw)
                        if total > MAX_BYTES or digest(rel, raw) != expected:
                            raise ValueError("compatibility snapshot changed/oversized")
                        target = staging / "resources" / rel
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(raw)
                    write_record(staging / "binding.json", packet["binding"])
                    write_record(staging / "review.json", {k: packet[k] for k in ("changed_resources", "required_review_paths", "previous_revision", "previous_resource_root")})
                    os.replace(staging, home)
            write_record(path, assessment)
            write_record(home.parent / "latest.json", {"binding_sha256": packet["binding_sha256"]})
        if not path.exists():
            return {"status": "assessment-required", "review": packet}
        value = read_local_json(path)
        stored_binding = read_local_json(path.parent / "binding.json")
        if stored_binding != packet["binding"]:
            raise ValueError("compatibility cache binding altered")
        validate_assessment(value, entry, packet)
        return {"status": "accepted" if value["decision"] == "accepted" else "compatibility-blocked",
                "binding_sha256": packet["binding_sha256"], "assessment_path": str(path), "decision": value["decision"],
                "reason": value["reason"], "conflicts": value["conflicts"], "reused": packet.get("reused", False),
                **({"review": packet} if value["decision"] != "accepted" else {})}
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return {"status": "compatibility-unverified", "error": str(exc)}


def run(mode: str, skills_dir: Path, state: Path, selected: list[dict], apply: bool, assessment=None) -> dict:
    data = registry()
    inventory = state / "inventory.json"
    last = json.loads(inventory.read_text(encoding="utf-8")) if inventory.exists() else {}
    last_time = datetime.fromisoformat(last["checked_at"]) if last.get("checked_at") else None
    due = not last_time or (datetime.now(timezone.utc) - last_time).total_seconds() >= data["policy"]["inventory_interval_hours"] * 3600
    entries = {data["head"]["id"]: data["head"]}
    if mode == "inventory" or due:
        entries.update({entry["id"]: entry for entry in data["specialists"] if (skills_dir / entry["skill_name"]).exists()})
    entries.update({entry["id"]: entry for entry in selected})
    with installation_lock(skills_dir):
        head = ensure(data["head"], skills_dir, state, apply)
        # A changed manager/registry must be reloaded before it can delegate.
        if head.get("updated"):
            return {"gate": "RELOAD", "skills": [head], "reload_head_required": True,
                    "selected_specialists": [], "action": "reload the installed Head and rerun its preflight"}
        results = [head, *(ensure(entry, skills_dir, state, apply) for name, entry in entries.items() if name != data["head"]["id"])]
        if assessment is not None and (mode != "assess" or len(selected) != 1):
            raise ValueError("assess exactly one registered specialist")
        selected_by_id = {entry["id"]: entry for entry in selected}
        for item in results:
            if item["id"] in selected_by_id and item["status"] == "current":
                item["compatibility"] = compatibility(selected_by_id[item["id"]], skills_dir, state, item, assessment)
    required = {data["head"]["id"], *(entry["id"] for entry in selected)}
    blocked = [item["id"] for item in results if item["id"] in required and item["status"] != "current"]
    blocked.extend(item["id"] for item in results if item["id"] in selected_by_id
                   and (mode == "assess" or selected_by_id[item["id"]].get("active_in_stage", True))
                   and item.get("status") == "current" and item.get("compatibility", {}).get("status") != "accepted")
    if (mode == "inventory" or due) and all(item["status"] == "current" for item in results):
        write_record(inventory, {"checked_at": datetime.now(timezone.utc).isoformat()})
    return {"gate": "BLOCK" if blocked else ("WARN" if any(item["status"] != "current" for item in results) else "PASS"), "skills": results, "blocked": blocked,
            "reload_head_required": False,
            "selected_specialists": selected, "head_precedence": True,
            "missing_unselected": [entry["id"] for entry in data["specialists"] if not (skills_dir / entry["skill_name"]).exists()]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "inventory", "assess"))
    parser.add_argument("--task", default="")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--concern", action="append", default=[])
    parser.add_argument("--specialist", action="append", default=[])
    parser.add_argument("--stage", choices=registry()["lifecycle"], default="discover")
    parser.add_argument("--skills-dir", type=Path, default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "skills")
    parser.add_argument("--state-dir", type=Path, default=Path(os.environ.get("VIBE_CODING_HOME", str(Path.home() / ".vibe-coding"))) / "specialists")
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--apply", action="store_true", help="install/update registered sources within existing authorization")
    parser.add_argument("--assessment", type=Path, help="Head-authored compatibility decision JSON; assess mode only")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        skills, state = args.skills_dir.expanduser().resolve(), args.state_dir.expanduser().resolve()
        if args.project_root and any(path.is_relative_to(args.project_root.resolve()) for path in (skills, state)):
            raise ValueError("skills and update state must stay outside the product repository")
        if skills.is_relative_to(state) or state.is_relative_to(skills):
            raise ValueError("update state and skill discovery directories must be separate")
        unknown_concerns = set(args.concern) - supported_concerns()
        if unknown_concerns:
            raise ValueError("unknown specialist concerns: " + ", ".join(sorted(unknown_concerns)))
        selected = select_specialists(args.task, args.path, {"concern": args.concern}, args.specialist, args.stage)
        if (args.mode == "assess") != bool(args.assessment) or (args.mode == "assess" and len(selected) != 1):
            raise ValueError("assess requires one selected registered specialist and --assessment")
        result = run(args.mode, skills, state, selected, args.apply,
                     read_local_json(args.assessment) if args.assessment else None)
    except (OSError, ValueError, KeyError) as exc:
        result = {"gate": "BLOCK", "error": str(exc)}
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else f"Specialist preflight: {result['gate']}")
    return 2 if result["gate"] in ("BLOCK", "RELOAD") else 0


if __name__ == "__main__":
    raise SystemExit(main())
