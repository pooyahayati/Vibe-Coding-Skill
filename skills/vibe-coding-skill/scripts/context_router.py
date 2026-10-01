#!/usr/bin/env python3
"""Evidence-based context routing for Vibe Coding Skill."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "context-routing.json"
TEXT_SUFFIXES = {
    ".php", ".json", ".js", ".jsx", ".ts", ".tsx", ".md", ".txt",
    ".yml", ".yaml", ".xml", ".html", ".css",
}
SOURCE_MARKER_SUFFIXES = {
    ".php", ".json", ".js", ".jsx", ".ts", ".tsx", ".yml", ".yaml", ".xml",
}
EXCLUDED_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build", ".next",
    ".cache", ".venv", "venv", "__pycache__",
}
PROJECT_DOCS = [
    "AGENTS.md",
    "STATUS.md",
    "PROJECT.md",
    "ARCHITECTURE.md",
    "PROJECT_GRAPH.md",
    "ROADMAP.md",
    "README.md",
]
MONOREPO_CONTAINERS = {"apps", "packages", "services", "plugins", "themes"}
WORDPRESS_SCOPED_CONTAINERS = {
    ("wp-content", "plugins"),
    ("wp-content", "themes"),
    ("wp-content", "mu-plugins"),
}
CONTEXT_FACT_FIELDS = ("runtime", "platform", "capability", "concern")


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_risk_classifier():
    path = ROOT / "scripts" / "risk_classifier.py"
    spec = importlib.util.spec_from_file_location("_vibe_risk_classifier", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load risk classifier")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_specialist_manager():
    path = ROOT / "scripts" / "specialist_manager.py"
    spec = importlib.util.spec_from_file_location("_vibe_specialist_manager", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load specialist manager")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_files(root: Path) -> list[str]:
    p = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if p.returncode != 0:
        return []
    return sorted(
        {
            value.decode("utf-8", "surrogateescape")
            for value in p.stdout.split(b"\0")
            if value
        }
    )


def fallback_files(root: Path) -> list[str]:
    result: list[str] = []
    for directory, children, names in os.walk(root):
        children[:] = [child for child in children if child not in EXCLUDED_DIRS]
        for name in names:
            result.append((Path(directory) / name).relative_to(root).as_posix())
    return sorted(result)


def project_files(root: Path) -> list[str]:
    files = git_files(root)
    return files if files else fallback_files(root)


def normalize_rel(raw: str) -> str:
    return raw.replace("\\", "/").lstrip("./").rstrip("/")


def normalize_context_fact_value(value: Any) -> str:
    text = str(value or "").strip().lower().replace("_", "-")
    return "-".join(text.split())


def normalize_context_facts(
    facts: dict[str, Any] | None,
) -> dict[str, list[str]]:
    if not facts:
        return {}

    result: dict[str, list[str]] = {}
    for field, raw in facts.items():
        if field not in CONTEXT_FACT_FIELDS:
            raise ValueError(f"unsupported structured context field: {field}")
        values = (
            list(raw)
            if isinstance(raw, (list, tuple, set))
            else [raw]
        )
        normalized = [
            normalize_context_fact_value(value)
            for value in values
            if normalize_context_fact_value(value)
        ]
        if normalized:
            result[field] = list(dict.fromkeys(normalized))
    return result


def validate_context_facts(
    config: dict[str, Any],
    facts: dict[str, list[str]],
) -> None:
    supported: dict[str, set[str]] = {
        field: set() for field in CONTEXT_FACT_FIELDS
    }
    supported["concern"].update(load_specialist_manager().supported_concerns())
    for pack in config.get("packs", {}).values():
        for field, values in pack.get("context_facts", {}).items():
            if field not in supported:
                continue
            supported[field].update(
                normalize_context_fact_value(value)
                for value in values
                if normalize_context_fact_value(value)
            )

    invalid = [
        f"{field}={value}"
        for field, values in facts.items()
        for value in values
        if value not in supported.get(field, set())
        and not (field == "runtime" and re.fullmatch(r"[a-z0-9][a-z0-9.+-]{0,63}", value))
    ]
    if invalid:
        raise ValueError(
            "unsupported structured context fact(s): " + ", ".join(invalid)
        )


def pack_context_fact_evidence(
    pack: dict[str, Any],
    facts: dict[str, list[str]],
) -> list[str]:
    evidence: list[str] = []
    mapping = pack.get("context_facts", {})
    for field, values in facts.items():
        accepted = {
            normalize_context_fact_value(value)
            for value in mapping.get(field, [])
            if normalize_context_fact_value(value)
        }
        for value in values:
            if value in accepted:
                evidence.append(f"context-fact:{field}={value}")
    return evidence


def discover_area_roots(root: Path, files: list[str], config: dict[str, Any]) -> tuple[str, ...]:
    """Use entry manifests/plugin headers; infer their sibling container roots."""
    roots: set[str] = set(config.get("project_area_roots", []))
    manifests = {"package.json", "composer.json", "pyproject.toml", "Cargo.toml", "go.mod"}
    for rel in files:
        path = Path(rel)
        parent = path.parent.as_posix()
        if parent == ".":
            continue
        if path.name in manifests or path.suffix == ".csproj":
            roots.add(parent)
        elif path.suffix == ".php" and "Plugin Name:" in safe_text(root / rel, 8192):
            roots.add(parent)
    containers = {str(value) for value in config.get("project_area_containers", [])}
    containers.update(str(Path(value).parent.as_posix()) for value in roots if len(Path(value).parts) >= 2)
    for rel in files:
        parts = Path(rel).parts
        for container in containers:
            prefix = Path(container).parts
            if parts[:len(prefix)] == prefix and len(parts) > len(prefix) + 1:
                roots.add("/".join(parts[:len(prefix) + 1]))
    return tuple(sorted(roots, key=lambda value: (-len(Path(value).parts), value)))


def project_area(rel: str, area_roots: tuple[str, ...] = (), *, fallback: str = "__project__") -> str:
    parts = Path(normalize_rel(rel)).parts
    for area in area_roots:
        prefix = Path(area).parts
        if parts[:len(prefix)] == prefix:
            return area
    if len(parts) >= 3 and tuple(parts[:2]) in WORDPRESS_SCOPED_CONTAINERS:
        return "/".join(parts[:3])
    if len(parts) >= 2 and parts[0] in MONOREPO_CONTAINERS:
        return "/".join(parts[:2])
    return fallback


def capability_area(rel: str, area_roots: tuple[str, ...] = ()) -> str:
    return project_area(rel, area_roots)


def scope_area(rel: str, area_roots: tuple[str, ...] = ()) -> str:
    parts = Path(normalize_rel(rel)).parts
    if not parts:
        return "__root__"
    return project_area(rel, area_roots, fallback=parts[0] if len(parts) > 1 else "__root__")


def scan_area(rel: str, area_roots: tuple[str, ...] = ()) -> str:
    return scope_area(rel, area_roots)


def scan_candidate_files(
    files: list[str],
    paths: list[str],
    area_roots: tuple[str, ...] = (),
) -> tuple[list[str], str]:
    if not paths:
        return files, "fallback-project-scan"

    areas = {scan_area(raw, area_roots) for raw in paths if normalize_rel(raw)}
    selected = []
    for rel in files:
        parts = Path(rel).parts
        if len(parts) == 1 or scan_area(rel, area_roots) in areas:
            selected.append(rel)
    return selected, "path-scoped"


def safe_text(path: Path, max_bytes: int = 262_144) -> str:
    try:
        if not path.is_file() or path.stat().st_size > max_bytes:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def candidate_texts(
    root: Path,
    files: list[str],
    limit: int = 600,
    max_file_bytes: int = 65_536,
    max_total_bytes: int = 8_388_608,
) -> list[tuple[str, str]]:
    candidates: list[str] = []
    for rel in files:
        path = Path(rel)
        if path.suffix.lower() in TEXT_SUFFIXES:
            candidates.append(rel)
    candidates.sort(
        key=lambda rel: (
            len(Path(rel).parts),
            0 if Path(rel).suffix.lower() == ".php" else 1,
            rel,
        )
    )
    result: list[tuple[str, str]] = []
    total = 0
    for rel in candidates[:limit]:
        text = safe_text(root / rel, max_file_bytes)
        size = len(text.encode("utf-8", "ignore"))
        if total + size > max_total_bytes:
            break
        result.append((rel, text))
        total += size
    return result


def touched_texts(
    root: Path,
    paths: list[str],
    files: list[str],
    limit: int = 120,
    max_total_bytes: int = 1_048_576,
) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    seen: set[str] = set()
    total = 0
    for raw in paths:
        rel = normalize_rel(raw)
        if not rel:
            continue
        path = root / rel
        candidates: list[str] = []
        if path.exists() and path.is_file():
            candidates = [rel]
        elif path.exists() and path.is_dir():
            prefix = rel + "/"
            candidates = [
                item
                for item in files
                if item.startswith(prefix)
                and Path(item).suffix.lower() in TEXT_SUFFIXES
            ]
            candidates.sort(
                key=lambda item: (
                    len(Path(item).parts),
                    0 if Path(item).suffix.lower() == ".php" else 1,
                    item,
                )
            )
        for item in candidates:
            if item in seen or len(result) >= limit:
                continue
            text = safe_text(root / item, 65_536)
            size = len(text.encode("utf-8", "ignore"))
            if total + size > max_total_bytes:
                return result
            result.append((item, text))
            seen.add(item)
            total += size
    return result


def contains_any(text: str, values: list[str]) -> list[str]:
    lowered = text.lower()
    return [value for value in values if value.lower() in lowered]


def pack_project_evidence(
    pack: dict[str, Any],
    files: list[str],
    texts: list[tuple[str, str]],
) -> list[str]:
    evidence: list[str] = []

    for name in pack.get("files", []):
        seen_areas: set[str] = set()
        for rel in files:
            if Path(rel).name != name:
                continue
            area = capability_area(rel)
            if area in seen_areas:
                continue
            evidence.append(f"file:{rel}")
            seen_areas.add(area)
            if len(seen_areas) >= 8:
                break
    for suffix in pack.get("extensions", []):
        seen_areas: set[str] = set()
        for rel in files:
            if Path(rel).suffix.lower() != suffix.lower():
                continue
            area = capability_area(rel)
            if area in seen_areas:
                continue
            evidence.append(f"extension:{suffix}@{rel}")
            seen_areas.add(area)
            if len(seen_areas) >= 8:
                break
    markers = pack.get("project_markers", [])
    if markers:
        for rel, text in texts:
            if Path(rel).suffix.lower() not in SOURCE_MARKER_SUFFIXES:
                continue
            hits = contains_any(text, markers)
            if hits:
                evidence.append(f"marker:{hits[0]}@{rel}")
                if len(evidence) >= 4:
                    break
    return evidence


def pack_task_evidence(
    pack: dict[str, Any],
    task: str,
    paths: list[str],
    touched: list[tuple[str, str]],
    context_facts: dict[str, list[str]] | None = None,
) -> list[str]:
    evidence: list[str] = []
    task_lower = task.lower()
    for keyword in pack.get("task_keywords", []):
        if keyword.lower() in task_lower:
            evidence.append(f"task:{keyword}")
    path_text = " ".join(paths).lower()
    for keyword in pack.get("path_keywords", []):
        if keyword.lower() in path_text:
            evidence.append(f"path:{keyword}")
    markers = pack.get("project_markers", [])
    for rel, text in touched:
        hits = contains_any(text, markers)
        if hits:
            evidence.append(f"touched-marker:{hits[0]}@{rel}")
    evidence.extend(
        pack_context_fact_evidence(pack, context_facts or {})
    )
    return list(dict.fromkeys(evidence))


def project_complexity(
    files: list[str],
    config: dict[str, Any],
    override: str,
) -> dict[str, Any]:
    if override != "auto":
        return {
            "level": override,
            "confidence": "high",
            "evidence": ["explicit override"],
            "file_count": len(files),
        }

    analysis_files = [
        rel
        for rel in files
        if not any(part in EXCLUDED_DIRS for part in Path(rel).parts)
    ]
    manifests = [
        rel
        for rel in analysis_files
        if Path(rel).name
        in {
            "composer.json",
            "package.json",
            "pyproject.toml",
            "Cargo.toml",
            "go.mod",
        }
    ]
    top_roots = {
        Path(rel).parts[0]
        for rel in analysis_files
        if len(Path(rel).parts) > 1
        and Path(rel).parts[0] not in EXCLUDED_DIRS
        and not Path(rel).parts[0].startswith(".")
    }
    rules = config["complexity"]
    evidence = [
        f"relevant project files:{len(analysis_files)}",
        f"manifests:{len(manifests)}",
        f"top-level roots:{len(top_roots)}",
    ]
    if (
        len(analysis_files) > rules["medium_max_files"]
        or len(manifests) >= rules["large_manifest_threshold"]
        or len(top_roots) >= rules["large_source_root_threshold"]
    ):
        level = "large"
    elif len(analysis_files) > rules["small_max_files"] or len(manifests) > 1:
        level = "medium"
    else:
        level = "small"
    return {
        "level": level,
        "confidence": "medium",
        "evidence": evidence,
        "file_count": len(analysis_files),
        "raw_file_count": len(files),
        "manifest_count": len(manifests),
        "top_level_root_count": len(top_roots),
    }


def evidence_location_areas(evidence: list[str], area_roots: tuple[str, ...] = ()) -> set[str]:
    areas: set[str] = set()
    for item in evidence:
        rel = ""
        if item.startswith("file:"):
            rel = item.split(":", 1)[1]
        elif item.startswith(("marker:", "extension:")) and "@" in item:
            rel = item.rsplit("@", 1)[1]
        if rel:
            areas.add(capability_area(rel, area_roots))
    return areas


def task_path_roots(paths: list[str]) -> set[str]:
    roots: set[str] = set()
    for raw in paths:
        rel = raw.replace("\\", "/").lstrip("./")
        if not rel:
            continue
        parts = Path(rel).parts
        roots.add(parts[0] if len(parts) > 1 else "__root__")
    return roots


def task_scope_areas(paths: list[str], area_roots: tuple[str, ...] = ()) -> set[str]:
    return {
        scope_area(raw, area_roots)
        for raw in paths
        if normalize_rel(raw)
    }


def task_capability_areas(paths: list[str], area_roots: tuple[str, ...] = ()) -> set[str]:
    return {
        capability_area(raw, area_roots)
        for raw in paths
        if normalize_rel(raw)
    }


def change_scope(paths: list[str], risk: dict[str, Any], area_roots: tuple[str, ...] = ()) -> dict[str, Any]:
    normalized_paths = list(
        dict.fromkeys(
            raw.replace("\\", "/").lstrip("./")
            for raw in paths
            if raw.strip()
        )
    )
    roots = task_path_roots(normalized_paths)
    areas = task_scope_areas(normalized_paths, area_roots)
    matched = {str(value) for value in risk.get("matched_rules", [])}
    structured = risk.get("structured_facts") or {}
    boundary = str(structured.get("change_boundary") or "").strip().lower()

    reasons: list[str] = []
    if (
        "graph-cross-module" in matched
        or "fact:cross-module" in matched
        or boundary in {"cross-module", "multi-module", "system", "application-wide"}
    ):
        level = "cross-boundary"
        reasons.append("explicit cross-module/system impact")
    elif len(areas) > 1:
        level = "cross-boundary"
        reasons.append("affected paths span multiple project areas")
    elif not normalized_paths:
        level = "unknown"
        reasons.append("affected paths are not known yet")
    elif len(normalized_paths) == 1:
        level = "local"
        reasons.append("single known affected path")
    else:
        level = "bounded"
        reasons.append("multiple known paths within one project area")

    return {
        "level": level,
        "path_count": len(normalized_paths),
        "top_level_root_count": len(roots),
        "top_level_roots": sorted(roots),
        "project_area_count": len(areas),
        "project_areas": sorted(areas),
        "reasons": reasons,
    }


def project_pack_relevant(
    project_evidence: list[str],
    task_evidence: list[str],
    paths: list[str],
    complexity_level: str,
    area_roots: tuple[str, ...] = (),
) -> bool:
    if task_evidence:
        return True
    if not project_evidence:
        return False
    if not paths:
        return True
    evidence_areas = evidence_location_areas(project_evidence, area_roots)
    if "__project__" in evidence_areas:
        return True
    if not evidence_areas:
        return False
    return bool(evidence_areas & task_capability_areas(paths, area_roots))


def activation_requirements_met(
    name: str,
    pack: dict[str, Any],
    packs: dict[str, Any],
    project_evidence: dict[str, list[str]],
    task_evidence: dict[str, list[str]],
    paths: list[str],
    complexity_level: str,
    area_roots: tuple[str, ...] = (),
) -> bool:
    requirements = [
        str(value)
        for value in pack.get("activation_requires", [])
        if str(value).strip()
    ]
    if not requirements:
        return True
    if "explicit-include" in task_evidence.get(name, []):
        return True

    for required in requirements:
        required_pack = packs.get(required)
        if not isinstance(required_pack, dict):
            return False
        if required_pack.get("scope", "task") == "project":
            if not project_pack_relevant(
                project_evidence.get(required, []),
                task_evidence.get(required, []),
                paths,
                complexity_level,
                area_roots,
            ):
                return False
        elif not task_evidence.get(required):
            return False
    return True


def confidence(evidence: list[str], explicit: bool = False) -> str:
    if explicit or len(evidence) >= 2:
        return "high"
    if evidence:
        return "medium"
    return "low"


def selected_core_mode(tier: int) -> str:
    if tier == 0:
        return "light"
    if tier == 1:
        return "standard"
    return "significant"


def interaction_skipped(
    rule: dict[str, Any],
    task: str,
    base_tier: int,
) -> bool:
    if base_tier != 0:
        return False
    task_lower = task.lower()
    return any(
        marker.lower() in task_lower
        for marker in rule.get("skip_if_task_matches", [])
    )


def resolve_selection(
    config: dict[str, Any],
    project_evidence: dict[str, list[str]],
    task_evidence: dict[str, list[str]],
    task: str,
    base_tier: int,
    paths: list[str],
    complexity_level: str,
    area_roots: tuple[str, ...] = (),
) -> tuple[set[str], int, list[dict[str, Any]]]:
    packs = config["packs"]
    selected: set[str] = set()

    for name, pack in packs.items():
        scope = pack.get("scope", "task")
        candidate = False
        if scope == "project":
            candidate = project_pack_relevant(
                project_evidence[name],
                task_evidence[name],
                paths,
                complexity_level,
                area_roots,
            )
        elif task_evidence[name]:
            candidate = True

        if candidate and activation_requirements_met(
            name,
            pack,
            packs,
            project_evidence,
            task_evidence,
            paths,
            complexity_level,
            area_roots,
        ):
            selected.add(name)

    changed = True
    interaction_hits: list[dict[str, Any]] = []
    tier = base_tier
    while changed:
        changed = False
        for name in list(selected):
            for required in packs[name].get("requires", []):
                if required not in selected:
                    selected.add(required)
                    changed = True

        for rule in config.get("interaction_rules", []):
            required = set(rule.get("when_all", []))
            if not required.issubset(selected):
                continue
            if interaction_skipped(rule, task, base_tier):
                continue
            for extra in rule.get("add_packs", []):
                if extra not in selected:
                    selected.add(extra)
                    changed = True
            floor = int(rule.get("minimum_tier", tier))
            if floor > tier:
                tier = floor
            hit = {
                "when_all": sorted(required),
                "minimum_tier": floor,
                "reason": rule.get("reason"),
            }
            if hit not in interaction_hits:
                interaction_hits.append(hit)
    return selected, tier, interaction_hits


INVARIANT_HEADINGS = {
    "invariants",
    "project invariants",
    "constraints",
    "non-negotiable",
    "non-negotiables",
    "non-negotiable rules",
    "critical constraints",
    "guardrails",
}


def extract_invariants(text: str) -> list[str]:
    values: list[str] = []
    active = False
    active_level = 0
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            heading = line[level:].strip().lower()
            if heading in INVARIANT_HEADINGS:
                active = True
                active_level = level
            elif active and level <= active_level:
                active = False
            continue
        if active and line.startswith(("- ", "* ")):
            value = line[2:].strip()
            if value:
                values.append(value)
    return list(dict.fromkeys(values))


def applicable_agent_docs(
    root: Path,
    files: list[str],
    paths: list[str],
) -> list[str]:
    candidates = [
        rel for rel in files if Path(rel).name == "AGENTS.md"
    ]
    selected: list[str] = []
    if (root / "AGENTS.md").exists():
        selected.append("AGENTS.md")
    if not paths:
        return selected

    normalized_paths = [normalize_rel(raw) for raw in paths if normalize_rel(raw)]
    for rel in candidates:
        if rel == "AGENTS.md":
            continue
        parent = Path(rel).parent.as_posix()
        if any(
            path == parent or path.startswith(parent + "/")
            for path in normalized_paths
        ):
            selected.append(rel)
    return list(
        dict.fromkeys(
            sorted(selected, key=lambda rel: (len(Path(rel).parts), rel))
        )
    )


def detected_project_invariants(
    root: Path,
    agent_docs: list[str] | None = None,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    sources = list(agent_docs or [])
    sources.extend(["PROJECT.md", "ARCHITECTURE.md", "STATUS.md"])
    for name in dict.fromkeys(sources):
        path = root / name
        if not path.exists():
            continue
        for value in extract_invariants(safe_text(path)):
            rows.append({"source": name, "text": value})
    return rows


def persistent_context(
    root: Path,
    files: list[str],
    paths: list[str],
    complexity: str,
    tier: int,
) -> list[dict[str, str]]:
    present = [name for name in PROJECT_DOCS if (root / name).exists()]
    agent_docs = applicable_agent_docs(root, files, paths)
    selected: list[str] = list(agent_docs)
    if complexity in {"medium", "large"} or tier >= 2:
        for name in ("STATUS.md", "PROJECT.md"):
            if name in present:
                selected.append(name)
    if complexity in {"medium", "large"}:
        for name in ("ARCHITECTURE.md", "PROJECT_GRAPH.md"):
            if name in present:
                selected.append(name)
    if tier >= 2 and "ROADMAP.md" in present:
        selected.append("ROADMAP.md")
    if (
        tier >= 1
        and "README.md" in present
        and not any(Path(name).name != "AGENTS.md" for name in selected)
    ):
        selected.append("README.md")
    return [
        {
            "path": name,
            "mode": "full" if Path(name).name == "AGENTS.md" else "relevant-sections",
            "reason": (
                "applicable agent instructions"
                if Path(name).name == "AGENTS.md"
                else (
                    "project invariant/current-state source"
                    if Path(name).name in {"STATUS.md", "PROJECT.md"}
                    else "architecture/impact source"
                )
            ),
        }
        for name in dict.fromkeys(selected)
    ]


def project_file_bytes(root: Path, paths: list[str]) -> int:
    total = 0
    for rel in paths:
        path = root / rel
        try:
            if path.is_file():
                total += path.stat().st_size
        except OSError:
            pass
    return total


def file_bytes(paths: list[str]) -> int:
    total = 0
    for rel in paths:
        path = ROOT / rel
        try:
            if path.is_file():
                total += path.stat().st_size
        except OSError:
            pass
    return total


def plan(
    root: Path,
    task: str,
    paths: list[str] | None = None,
    complexity_override: str = "auto",
    invariants: list[str] | None = None,
    include_packs: list[str] | None = None,
    risk_facts: dict[str, Any] | None = None,
    context_facts: dict[str, Any] | None = None,
    stage: str = "discover",
) -> dict[str, Any]:
    root = root.resolve()
    paths = paths or []
    invariants = invariants or []
    include_packs = include_packs or []
    config = load_config()
    normalized_context_facts = normalize_context_facts(context_facts)
    validate_context_facts(config, normalized_context_facts)
    unknown_includes = sorted(
        set(include_packs) - set(config["packs"])
    )
    if unknown_includes:
        raise ValueError(
            "unknown capability pack(s): " + ", ".join(unknown_includes)
        )
    files = project_files(root)
    area_roots = discover_area_roots(root, files, config)
    scan_files, scan_strategy = scan_candidate_files(files, paths, area_roots)
    texts = candidate_texts(root, scan_files)
    touched = touched_texts(root, paths, files)

    project_ev: dict[str, list[str]] = {}
    task_ev: dict[str, list[str]] = {}
    for name, pack in config["packs"].items():
        project_ev[name] = pack_project_evidence(pack, scan_files, texts)
        task_ev[name] = pack_task_evidence(
            pack,
            task,
            paths,
            touched,
            normalized_context_facts,
        )
        if name in include_packs:
            task_ev[name] = list(
                dict.fromkeys(task_ev[name] + ["explicit-include"])
            )

    risk_module = load_risk_classifier()
    risk = risk_module.classify(task, paths, risk_facts)
    complexity = project_complexity(files, config, complexity_override)
    selected, effective_tier, interactions = resolve_selection(
        config,
        project_ev,
        task_ev,
        task,
        int(risk["tier"]),
        paths,
        str(complexity["level"]),
        area_roots,
    )
    risk = dict(risk)
    scope = change_scope(paths, risk, area_roots)
    if effective_tier > int(risk["tier"]):
        previous_tier = int(risk["tier"])
        policy = risk_module.policy_for_tier(
            effective_tier,
            approval_required=bool(risk.get("approval_required")),
        )
        risk.update(policy)
        risk["router_floor_from"] = previous_tier
        prior_reasons = (
            list(risk.get("reasons") or [])
            if risk.get("matched_rules")
            else []
        )
        risk["reasons"] = list(
            dict.fromkeys(
                prior_reasons
                + ["routing interaction raised the workflow floor"]
            )
        )

    agent_docs = applicable_agent_docs(root, files, paths)
    detected_invariants = detected_project_invariants(root, agent_docs)
    core_mode = selected_core_mode(int(risk["tier"]))
    core_refs = list(config["core_context"][core_mode])
    if (
        complexity["level"] == "large"
        and "references/project-intelligence.md" not in core_refs
    ):
        core_refs.append("references/project-intelligence.md")

    selected_rows: list[dict[str, Any]] = []
    integrations: list[str] = []
    specialists: list[str] = []
    for name in sorted(selected):
        pack = config["packs"][name]
        ev = (
            list(dict.fromkeys(project_ev[name] + task_ev[name]))
            if pack.get("scope") == "project"
            else task_ev[name]
        )
        if not ev:
            parents = sorted(
                parent
                for parent in selected
                if name in config["packs"][parent].get("requires", [])
            )
            ev = [
                "required-by:" + ",".join(parents or ["interaction-rule"])
            ]
        row = {
            "name": name,
            "category": pack["category"],
            "path": pack["path"],
            "confidence": confidence(
                ev,
                explicit=any(
                    value == "explicit-include"
                    or value.startswith("context-fact:")
                    for value in ev
                ),
            ),
            "evidence": ev,
        }
        selected_rows.append(row)
        integrations.extend(pack.get("integration_points", []))
        specialists.extend(pack.get("optional_specialists", []))

    persistent = persistent_context(
        root,
        files,
        paths,
        str(complexity["level"]),
        int(risk["tier"]),
    )
    pack_paths = [row["path"] for row in selected_rows]
    load_paths = list(
        dict.fromkeys(
            [entry["path"] for entry in persistent]
            + core_refs
            + pack_paths
        )
    )
    all_pack_paths = [
        pack["path"] for pack in config["packs"].values()
    ]
    skipped = sorted(set(all_pack_paths) - set(pack_paths))
    selected_reference_bytes = file_bytes(core_refs)
    selected_pack_bytes = file_bytes(pack_paths)
    persistent_context_upper_bound_bytes = project_file_bytes(
        root,
        [entry["path"] for entry in persistent],
    )
    skill_core_bytes = file_bytes(["SKILL.md"])

    return {
        "schema_version": 1,
        "project": {
            "root": str(root),
            "complexity": complexity,
            "invariant_sources": sorted(
                {row["source"] for row in detected_invariants}
            ),
            "detected_invariants": detected_invariants,
            "explicit_invariants": invariants,
        },
        "task": {
            "stage": stage,
            "text": task,
            "paths": paths,
            "explicit_pack_includes": sorted(set(include_packs)),
            "structured_context_facts": normalized_context_facts,
            "risk": risk,
            "scope": scope,
            "routing_note": (
                "Re-run routing when touched paths become known if the task "
                "starts without concrete impact paths. Use structured context "
                "facts when platform/runtime/capability/concern semantics are "
                "known but task wording is language-dependent or ambiguous."
            ),
        },
        "core": {
            "mode": core_mode,
            "references": core_refs,
            "large_project_awareness": complexity["level"] == "large",
        },
        "packs": selected_rows,
        "interactions": interactions,
        "integration_points": sorted(set(integrations)),
        "optional_specialists": sorted(set(specialists)),
        "required_specialists": load_specialist_manager().select_specialists(
            task, paths, normalized_context_facts, stage=stage, risk_facts=risk_facts),
        "lifecycle": {"stage_owner": "vibe-coding-skill", "stages": load_specialist_manager().registry()["lifecycle"],
                      "rule": "Stage selects the assignment boundary, not all specialists. Reuse settled work; apply only relevant stage controls."},
        "context_plan": {
            "load": load_paths,
            "skip_packs": skipped,
            "guidance": (
                "Load only task-relevant sections from persistent project "
                "documents; capability packs supplement rather than replace "
                "project intelligence and Vibe Core controls."
            ),
            "metrics": {
                "candidate_packs": len(config["packs"]),
                "packs_loaded": len(selected_rows),
                "references_selected": len(core_refs),
                "persistent_sources": len(persistent),
                "context_files_selected": len(load_paths),
                "estimated_skill_context_bytes": (
                    selected_reference_bytes + selected_pack_bytes
                ),
                "skill_core_bytes": skill_core_bytes,
                "selected_reference_bytes": selected_reference_bytes,
                "selected_pack_bytes": selected_pack_bytes,
                "persistent_context_upper_bound_bytes": (
                    persistent_context_upper_bound_bytes
                ),
                "estimated_context_upper_bound_bytes": (
                    skill_core_bytes
                    + selected_reference_bytes
                    + selected_pack_bytes
                    + persistent_context_upper_bound_bytes
                ),
                "scan_strategy": scan_strategy,
                "scan_areas": sorted(
                    {scan_area(raw) for raw in paths if normalize_rel(raw)}
                ),
                "integration_points": len(set(integrations)),
                "project_files_considered": len(files),
                "project_text_files_scanned": len(texts),
                "project_text_bytes_scanned": sum(
                    len(text.encode("utf-8", "ignore"))
                    for _, text in texts
                ),
            },
            "coverage": {
                "project_invariants_preserved": bool(
                    invariants or detected_invariants
                ),
                "risk_controls_preserved": set(
                    risk_module.policy_for_tier(
                        int(risk["tier"]),
                        approval_required=bool(risk.get("approval_required")),
                    )["required_controls"]
                ).issubset(set(risk.get("required_controls") or [])),
                "project_intelligence_preserved": (
                    complexity["level"] == "large"
                    or int(risk["tier"]) >= 2
                ),
            },
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--task", required=True)
    ap.add_argument("--path", action="append", default=[])
    ap.add_argument(
        "--complexity",
        choices=["auto", "small", "medium", "large"],
        default="auto",
    )
    ap.add_argument("--invariant", action="append", default=[])
    ap.add_argument("--include-pack", action="append", default=[])
    ap.add_argument("--risk-operation")
    ap.add_argument("--risk-environment")
    ap.add_argument("--risk-data-sensitivity")
    ap.add_argument("--risk-change-boundary")
    ap.add_argument("--context-runtime", action="append", default=[])
    ap.add_argument("--context-platform", action="append", default=[])
    ap.add_argument("--context-capability", action="append", default=[])
    ap.add_argument("--context-concern", action="append", default=[])
    ap.add_argument("--stage", choices=load_specialist_manager().registry()["lifecycle"], default="discover")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    risk_facts = {
        "operation": ns.risk_operation,
        "environment": ns.risk_environment,
        "data_sensitivity": ns.risk_data_sensitivity,
        "change_boundary": ns.risk_change_boundary,
    }
    risk_facts = {
        key: value for key, value in risk_facts.items()
        if value is not None
    }
    context_facts = {
        field: getattr(ns, f"context_{field}")
        for field in CONTEXT_FACT_FIELDS
        if getattr(ns, f"context_{field}")
    }

    result = plan(
        Path(ns.root),
        ns.task,
        ns.path,
        ns.complexity,
        ns.invariant,
        ns.include_pack,
        risk_facts or None,
        context_facts or None,
        ns.stage,
    )
    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        names = ", ".join(row["name"] for row in result["packs"]) or "none"
        print(
            f"Context Router: {result['project']['complexity']['level']} "
            f"project / Tier {result['task']['risk']['tier']} / packs: {names}"
        )
        for path in result["context_plan"]["load"]:
            print(f"LOAD: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
