#!/usr/bin/env python3
"""Run pinned real-repository validations, including v0.10 context routing."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "validation" / "real-world-projects.json"
COMPLEXITY_RANK = {"small": 0, "medium": 1, "large": 2}


def run(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, env=env)


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], root)


def clone_pinned(url: str, sha: str, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    init = git(target, "init", "-q")
    if init.returncode:
        raise RuntimeError(init.stderr)
    git(target, "remote", "add", "origin", url)
    fetched = git(target, "fetch", "--depth", "1", "origin", sha)
    if fetched.returncode:
        raise RuntimeError(f"cannot fetch pinned commit {sha}: {fetched.stderr}")
    checked = git(target, "checkout", "--detach", "FETCH_HEAD")
    if checked.returncode:
        raise RuntimeError(checked.stderr)
    head = git(target, "rev-parse", "HEAD").stdout.strip()
    if head != sha:
        raise RuntimeError(
            f"pinned checkout mismatch: expected {sha}, got {head}"
        )


def json_cmd(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str],
) -> tuple[int, dict[str, Any]]:
    result = run(cmd, cwd, env)
    if not result.stdout.strip():
        raise RuntimeError(
            f"no JSON output from {' '.join(cmd)}: {result.stderr}"
        )
    return result.returncode, json.loads(result.stdout)


def path_args(paths: list[str]) -> list[str]:
    args: list[str] = []
    for path in paths:
        args.extend(["--path", path])
    return args


def validate_routing_expectations(
    route: dict[str, Any],
    plan: dict[str, Any],
    case: dict[str, Any],
) -> tuple[dict[str, bool], dict[str, Any]]:
    checks: dict[str, bool] = {}
    packs = [str(row.get("name")) for row in route.get("packs", [])]
    pack_set = set(packs)
    integrations = [str(value) for value in route.get("integration_points", [])]
    metrics = route.get("context_plan", {}).get("metrics", {})
    coverage = route.get("context_plan", {}).get("coverage", {})
    complexity = str(
        route.get("project", {}).get("complexity", {}).get("level", "")
    )
    tier = int(route.get("task", {}).get("risk", {}).get("tier", -1))
    candidate_packs = int(metrics.get("candidate_packs", 0))
    loaded_packs = int(metrics.get("packs_loaded", len(packs)))
    reduction_ratio = (
        (candidate_packs - loaded_packs) / candidate_packs
        if candidate_packs > 0
        else 0.0
    )

    if "expected_complexity_at_least" in case:
        floor = str(case["expected_complexity_at_least"])
        checks["complexity_floor"] = (
            complexity in COMPLEXITY_RANK
            and floor in COMPLEXITY_RANK
            and COMPLEXITY_RANK[complexity] >= COMPLEXITY_RANK[floor]
        )
    if "expected_min_tier" in case:
        checks["tier_floor"] = tier >= int(case["expected_min_tier"])
    if "expected_max_tier" in case:
        checks["tier_ceiling"] = tier <= int(case["expected_max_tier"])

    required = set(case.get("required_packs", []))
    forbidden = set(case.get("forbidden_packs", []))
    checks["required_packs"] = required.issubset(pack_set)
    checks["forbidden_packs"] = not bool(forbidden & pack_set)
    checks["pack_names_unique"] = len(packs) == len(pack_set)
    checks["integration_points_unique"] = (
        len(integrations) == len(set(integrations))
    )

    if "max_loaded_packs" in case:
        checks["pack_budget"] = loaded_packs <= int(case["max_loaded_packs"])
    if case.get("require_context_reduction"):
        checks["context_reduction"] = candidate_packs > loaded_packs
    if "min_pack_reduction_ratio" in case:
        checks["pack_reduction_ratio"] = (
            reduction_ratio >= float(case["min_pack_reduction_ratio"])
        )
    if case.get("require_project_intelligence"):
        checks["project_intelligence"] = bool(
            coverage.get("project_intelligence_preserved")
        )
    if "require_execution_plan" in case:
        checks["execution_plan_required"] = bool(
            plan.get("execution_plan_required")
        ) is bool(case["require_execution_plan"])
    if "min_integration_points" in case:
        checks["integration_point_floor"] = (
            len(integrations) >= int(case["min_integration_points"])
        )

    detail = {
        "complexity": complexity,
        "tier": tier,
        "packs": packs,
        "candidate_packs": candidate_packs,
        "packs_loaded": loaded_packs,
        "pack_reduction_ratio": round(reduction_ratio, 4),
        "context_files_selected": metrics.get("context_files_selected"),
        "estimated_skill_context_bytes": metrics.get(
            "estimated_skill_context_bytes"
        ),
        "integration_points": integrations,
        "integration_point_count": len(integrations),
        "project_files_considered": metrics.get("project_files_considered"),
        "project_text_files_scanned": metrics.get(
            "project_text_files_scanned"
        ),
        "project_text_bytes_scanned": metrics.get(
            "project_text_bytes_scanned"
        ),
        "project_intelligence_preserved": coverage.get(
            "project_intelligence_preserved"
        ),
        "execution_plan_required": plan.get("execution_plan_required"),
        "execution_plan_mode": plan.get("mode"),
        "execution_workstreams": len(plan.get("workstreams", [])),
    }
    return checks, detail


def run_routing_check(
    project: Path,
    env: dict[str, str],
    case: dict[str, Any],
) -> tuple[dict[str, bool], dict[str, Any]]:
    common = [
        "--root",
        str(project),
        "--task",
        str(case["task"]),
        *path_args([str(value) for value in case.get("paths", [])]),
        "--json",
    ]
    route_rc, route = json_cmd(
        [sys.executable, str(ROOT / "scripts" / "context_router.py"), *common],
        ROOT,
        env,
    )
    plan_rc, plan = json_cmd(
        [
            sys.executable,
            str(ROOT / "scripts" / "execution_plan.py"),
            "draft",
            *common,
        ],
        ROOT,
        env,
    )
    checks, detail = validate_routing_expectations(route, plan, case)
    checks = {
        "router_exit": route_rc == 0,
        "execution_plan_exit": plan_rc == 0,
        **checks,
    }
    return checks, detail


def main() -> int:
    catalog = json.loads(CASES.read_text(encoding="utf-8"))
    results: list[dict[str, object]] = []
    failures: list[str] = []

    for case in catalog["projects"]:
        with (
            tempfile.TemporaryDirectory(
                prefix=f"vibe-real-{case['id']}-"
            ) as td,
            tempfile.TemporaryDirectory(prefix="vibe-real-home-") as hd,
        ):
            project = Path(td) / "project"
            env = os.environ.copy()
            env["VIBE_CODING_HOME"] = hd
            env["PYTHONDONTWRITEBYTECODE"] = "1"

            checks: dict[str, bool] = {}
            details: dict[str, object] = {}
            routing_results: list[dict[str, object]] = []
            try:
                clone_pinned(case["repository"], case["commit"], project)
                before = git(project, "status", "--porcelain").stdout

                rc, workspace = json_cmd(
                    [
                        sys.executable,
                        str(ROOT / "scripts" / "local_workspace.py"),
                        "init",
                        "--root",
                        str(project),
                        "--json",
                    ],
                    ROOT,
                    env,
                )
                checks["workspace_init"] = rc == 0

                rc, purity = json_cmd(
                    [
                        sys.executable,
                        str(ROOT / "scripts" / "repository_purity.py"),
                        "--root",
                        str(project),
                        "--strict-excludes",
                        "--json",
                    ],
                    ROOT,
                    env,
                )
                checks["repository_purity"] = (
                    rc == 0 and purity.get("status") == "PASS"
                )

                rc, resume = json_cmd(
                    [
                        sys.executable,
                        str(ROOT / "scripts" / "resume_context.py"),
                        "--root",
                        str(project),
                        "--json",
                    ],
                    ROOT,
                    env,
                )
                checks["resume_context"] = (
                    rc == 0 and resume.get("readiness") in {"PASS", "WARN"}
                )

                rc, bootstrap = json_cmd(
                    [
                        sys.executable,
                        str(ROOT / "scripts" / "bootstrap_project.py"),
                        "--root",
                        str(project),
                        "--profile",
                        "standard",
                        "--objective",
                        "Validate safe brownfield inspection",
                        "--dry-run",
                        "--json",
                    ],
                    ROOT,
                    env,
                )
                checks["bootstrap_dry_run"] = (
                    rc == 0 and bootstrap.get("destructive") is False
                )

                rc, risk = json_cmd(
                    [
                        sys.executable,
                        str(ROOT / "scripts" / "risk_classifier.py"),
                        case["task"],
                        *path_args(case.get("paths", [])),
                        "--json",
                    ],
                    ROOT,
                    env,
                )
                checks["risk_floor"] = (
                    rc == 0
                    and int(risk.get("tier", -1))
                    >= int(case["expected_min_tier"])
                )

                for routing_case in case.get("routing_checks", []):
                    route_checks, route_details = run_routing_check(
                        project,
                        env,
                        routing_case,
                    )
                    routing_id = str(routing_case["id"])
                    for name, ok in route_checks.items():
                        checks[f"routing:{routing_id}:{name}"] = ok
                    routing_results.append(
                        {
                            "id": routing_id,
                            "checks": route_checks,
                            "details": route_details,
                        }
                    )

                after = git(project, "status", "--porcelain").stdout
                checks["working_tree_clean"] = before == after
                checks["no_project_vibe_state"] = (
                    not (project / ".vibe").exists()
                    and not (project / ".vibe-coding").exists()
                )

                details = {
                    "workspace": workspace.get("workspace"),
                    "purity": purity.get("status"),
                    "resume": resume.get("readiness"),
                    "risk_tier": risk.get("tier"),
                    "routing": routing_results,
                }
            except Exception as exc:
                checks["exception_free"] = False
                details = {
                    "error": str(exc),
                    "routing": routing_results,
                }

            failed = [name for name, ok in checks.items() if not ok]
            if failed:
                failures.append(f"{case['id']}: {', '.join(failed)}")
            results.append(
                {
                    "id": case["id"],
                    "repository": case["repository"],
                    "commit": case["commit"],
                    "checks": checks,
                    "details": details,
                }
            )

    print(json.dumps({"results": results, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
