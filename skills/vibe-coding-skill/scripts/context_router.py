#!/usr/bin/env python3
"""Evidence-based context routing for Vibe Coding Skill."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
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
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        result.append(rel.as_posix())
    return sorted(result)


def project_files(root: Path) -> list[str]:
    files = git_files(root)
    return files if files else fallback_files(root)


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
    limit: int = 1200,
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
    return [
        (rel, safe_text(root / rel))
        for rel in candidates[:limit]
    ]


def touched_texts(root: Path, paths: list[str]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for raw in paths:
        rel = raw.replace("\\", "/").lstrip("./")
        path = root / rel
        if path.exists() and path.is_file():
            result.append((rel, safe_text(path)))
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
    basenames = {Path(rel).name for rel in files}
    suffixes = {Path(rel).suffix.lower() for rel in files}

    for name in pack.get("files", []):
        if name in basenames:
            evidence.append(f"file:{name}")
    for suffix in pack.get("extensions", []):
        if suffix.lower() in suffixes:
            evidence.append(f"extension:{suffix}")
    markers = pack.get("project_markers", [])
    if markers:
        for rel, text in texts:
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

    manifests = [
        rel
        for rel in files
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
        for rel in files
        if len(Path(rel).parts) > 1
        and Path(rel).parts[0] not in EXCLUDED_DIRS
        and not Path(rel).parts[0].startswith(".")
    }
    rules = config["complexity"]
    evidence = [
        f"tracked/project files:{len(files)}",
        f"manifests:{len(manifests)}",
        f"top-level roots:{len(top_roots)}",
    ]
    if (
        len(files) > rules["medium_max_files"]
        or len(manifests) >= rules["large_manifest_threshold"]
        or len(top_roots) >= rules["large_source_root_threshold"]
    ):
        level = "large"
    elif len(files) > rules["small_max_files"] or len(manifests) > 1:
        level = "medium"
    else:
        level = "small"
    return {
        "level": level,
        "confidence": "medium",
        "evidence": evidence,
        "file_count": len(files),
        "manifest_count": len(manifests),
        "top_level_root_count": len(top_roots),
    }


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


def interaction_skipped(rule: dict[str, Any], task: str) -> bool:
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
) -> tuple[set[str], int, list[dict[str, Any]]]:
    packs = config["packs"]
    selected: set[str] = set()

    for name, pack in packs.items():
        scope = pack.get("scope", "task")
        evidence = (
            project_evidence[name]
            if scope == "project"
            else task_evidence[name]
        )
        if evidence:
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
            if interaction_skipped(rule, task):
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


def persistent_context(
    root: Path,
    complexity: str,
    tier: int,
) -> list[dict[str, str]]:
    present = [name for name in PROJECT_DOCS if (root / name).exists()]
    selected: list[str] = []
    for name in ("AGENTS.md", "STATUS.md", "PROJECT.md"):
        if name in present:
            selected.append(name)
    if complexity in {"medium", "large"}:
        for name in ("ARCHITECTURE.md", "PROJECT_GRAPH.md"):
            if name in present:
                selected.append(name)
    if tier >= 2 and "ROADMAP.md" in present:
        selected.append("ROADMAP.md")
    if not selected and "README.md" in present:
        selected.append("README.md")
    return [
        {
            "path": name,
            "mode": "relevant-sections",
            "reason": (
                "project invariant/current-state source"
                if name in {"AGENTS.md", "STATUS.md", "PROJECT.md"}
                else "architecture/impact source"
            ),
        }
        for name in dict.fromkeys(selected)
    ]


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
) -> dict[str, Any]:
    root = root.resolve()
    paths = paths or []
    invariants = invariants or []
    config = load_config()
    files = project_files(root)
    texts = candidate_texts(root, files)
    touched = touched_texts(root, paths)

    project_ev: dict[str, list[str]] = {}
    task_ev: dict[str, list[str]] = {}
    for name, pack in config["packs"].items():
        project_ev[name] = pack_project_evidence(pack, files, texts)
        task_ev[name] = pack_task_evidence(pack, task, paths, touched)

    risk = load_risk_classifier().classify(task, paths)
    selected, effective_tier, interactions = resolve_selection(
        config,
        project_ev,
        task_ev,
        task,
        int(risk["tier"]),
    )
    risk = dict(risk)
    if effective_tier > int(risk["tier"]):
        risk["router_floor_from"] = risk["tier"]
        risk["tier"] = effective_tier
        risk["label"] = ["tiny", "standard", "significant", "critical"][
            effective_tier
        ]
        risk["approval_required"] = (
            bool(risk.get("approval_required")) or effective_tier >= 3
        )

    complexity = project_complexity(files, config, complexity_override)
    core_mode = selected_core_mode(int(risk["tier"]))
    core_refs = list(config["core_context"][core_mode])

    selected_rows: list[dict[str, Any]] = []
    integrations: list[str] = []
    specialists: list[str] = []
    for name in sorted(selected):
        pack = config["packs"][name]
        ev = (
            project_ev[name]
            if pack.get("scope") == "project"
            else task_ev[name]
        )
        if not ev:
            ev = [f"required-by:{','.join(pack.get('requires', [])) or 'interaction'}"]
        row = {
            "name": name,
            "category": pack["category"],
            "path": pack["path"],
            "confidence": confidence(ev),
            "evidence": ev,
        }
        selected_rows.append(row)
        integrations.extend(pack.get("integration_points", []))
        specialists.extend(pack.get("optional_specialists", []))

    persistent = persistent_context(
        root,
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

    return {
        "schema_version": 1,
        "project": {
            "root": str(root),
            "complexity": complexity,
            "invariant_sources": [
                name
                for name in ("AGENTS.md", "PROJECT.md", "ARCHITECTURE.md")
                if (root / name).exists()
            ],
            "explicit_invariants": invariants,
        },
        "task": {
            "text": task,
            "paths": paths,
            "risk": risk,
            "routing_note": (
                "Re-run routing when touched paths become known if the task "
                "starts without concrete impact paths."
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
                "estimated_skill_context_bytes": file_bytes(
                    core_refs + pack_paths
                ),
                "integration_points": len(set(integrations)),
            },
            "coverage": {
                "project_invariants_preserved": bool(
                    invariants
                    or any(
                        (root / name).exists()
                        for name in ("AGENTS.md", "PROJECT.md")
                    )
                ),
                "risk_controls_preserved": True,
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
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    result = plan(
        Path(ns.root),
        ns.task,
        ns.path,
        ns.complexity,
        ns.invariant,
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
