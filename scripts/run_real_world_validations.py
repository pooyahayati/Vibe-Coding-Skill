#!/usr/bin/env python3
"""Run repository-purity and resume checks against pinned real public projects."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "validation" / "real-world-projects.json"


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
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
        raise RuntimeError(f"pinned checkout mismatch: expected {sha}, got {head}")


def json_cmd(cmd: list[str], cwd: Path, env: dict[str, str]) -> tuple[int, dict]:
    result = run(cmd, cwd, env)
    if not result.stdout.strip():
        raise RuntimeError(f"no JSON output from {' '.join(cmd)}: {result.stderr}")
    return result.returncode, json.loads(result.stdout)


def main() -> int:
    catalog = json.loads(CASES.read_text(encoding="utf-8"))
    results: list[dict[str, object]] = []
    failures: list[str] = []

    for case in catalog["projects"]:
        with tempfile.TemporaryDirectory(prefix=f"vibe-real-{case['id']}-") as td, tempfile.TemporaryDirectory(prefix="vibe-real-home-") as hd:
            project = Path(td) / "project"
            env = os.environ.copy()
            env["VIBE_CODING_HOME"] = hd
            env["PYTHONDONTWRITEBYTECODE"] = "1"

            checks: dict[str, bool] = {}
            details: dict[str, object] = {}
            try:
                clone_pinned(case["repository"], case["commit"], project)
                before = git(project, "status", "--porcelain").stdout

                rc, workspace = json_cmd(
                    [sys.executable, str(ROOT / "scripts" / "local_workspace.py"),
                     "init", "--root", str(project), "--json"],
                    ROOT, env,
                )
                checks["workspace_init"] = rc == 0

                rc, purity = json_cmd(
                    [sys.executable, str(ROOT / "scripts" / "repository_purity.py"),
                     "--root", str(project), "--strict-excludes", "--json"],
                    ROOT, env,
                )
                checks["repository_purity"] = rc == 0 and purity.get("status") == "PASS"

                rc, resume = json_cmd(
                    [sys.executable, str(ROOT / "scripts" / "resume_context.py"),
                     "--root", str(project), "--json"],
                    ROOT, env,
                )
                checks["resume_context"] = rc == 0 and resume.get("readiness") in {"PASS", "WARN"}

                rc, bootstrap = json_cmd(
                    [sys.executable, str(ROOT / "scripts" / "bootstrap_project.py"),
                     "--root", str(project), "--profile", "standard",
                     "--objective", "Validate safe brownfield inspection",
                     "--dry-run", "--json"],
                    ROOT, env,
                )
                checks["bootstrap_dry_run"] = rc == 0 and bootstrap.get("destructive") is False

                rc, risk = json_cmd(
                    [sys.executable, str(ROOT / "scripts" / "risk_classifier.py"),
                     case["task"],
                     *sum((["--path", p] for p in case.get("paths", [])), []),
                     "--json"],
                    ROOT, env,
                )
                checks["risk_floor"] = rc == 0 and int(risk.get("tier", -1)) >= int(case["expected_min_tier"])

                after = git(project, "status", "--porcelain").stdout
                checks["working_tree_clean"] = before == after
                checks["no_project_vibe_state"] = not (project / ".vibe").exists() and not (project / ".vibe-coding").exists()

                details = {
                    "workspace": workspace.get("workspace"),
                    "purity": purity.get("status"),
                    "resume": resume.get("readiness"),
                    "risk_tier": risk.get("tier"),
                }
            except Exception as exc:
                checks["exception_free"] = False
                details = {"error": str(exc)}

            failed = [name for name, ok in checks.items() if not ok]
            if failed:
                failures.append(f"{case['id']}: {', '.join(failed)}")
            results.append({
                "id": case["id"],
                "repository": case["repository"],
                "commit": case["commit"],
                "checks": checks,
                "details": details,
            })

    print(json.dumps({"results": results, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
