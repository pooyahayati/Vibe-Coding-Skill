#!/usr/bin/env python3
"""Offline installation and portability validation for Vibe Coding Skill."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

MIN_PYTHON = (3, 10)

RUNTIME_SCRIPTS = [
    "doctor.py",
    "change_budget.py",
    "bootstrap_project.py",
    "dependency_guard.py",
    "risk_classifier.py",
    "integration_guard.py",
    "completion_gate.py",
    "local_workspace.py",
    "repository_purity.py",
    "graph_provider.py",
    "github_traceability.py",
    "project_state.py",
    "resume_context.py",
    "state_recovery.py",
    "skill_lifecycle.py",
]

REQUIRED_REFS = [
    "operating-model.md",
    "risk-and-autonomy.md",
    "project-intelligence.md",
    "project-state-and-traceability.md",
    "local-workspace-and-repository-purity.md",
    "graph-provider-contract.md",
    "github-traceability-automation.md",
    "project-state-automation.md",
    "recovery-and-resume.md",
    "installation-and-lifecycle.md",
]


def skill_metadata(root: Path) -> dict[str, str]:
    skill = root / "SKILL.md"
    if not skill.exists():
        return {}
    text = skill.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3:
        return {}
    fields: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"')
    version_match = re.search(r'(?m)^  version:\s*"([^"]+)"\s*$', parts[1])
    if version_match:
        fields["version"] = version_match.group(1)
    return fields


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, env=env)
    return p.returncode, ((p.stdout or "") + "\n" + (p.stderr or "")).strip()


def validate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    failures: list[str] = []
    warnings: list[str] = []

    python_ok = sys.version_info >= MIN_PYTHON
    if not python_ok:
        failures.append(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required")
    if not shutil.which("git"):
        failures.append("Git is required")

    metadata = skill_metadata(root)
    if metadata.get("name") != "vibe-coding-skill":
        failures.append("SKILL.md name must be vibe-coding-skill")
    if not metadata.get("version"):
        failures.append("SKILL.md version metadata is missing")

    for name in RUNTIME_SCRIPTS:
        path = root / "scripts" / name
        if not path.exists():
            failures.append(f"missing runtime script: scripts/{name}")
            continue
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except Exception as exc:
            failures.append(f"cannot compile scripts/{name}: {exc}")

    for name in REQUIRED_REFS:
        if not (root / "references" / name).exists():
            failures.append(f"missing reference: references/{name}")

    for name in RUNTIME_SCRIPTS:
        path = root / "scripts" / name
        if not path.exists():
            continue
        rc, out = run([sys.executable, str(path), "--help"], root)
        if rc != 0:
            failures.append(f"runtime import/help smoke failed: {name}: {out[-300:]}")

    workspace_smoke: dict[str, Any] = {"ok": False}
    if shutil.which("git") and (root / "scripts" / "local_workspace.py").exists():
        with tempfile.TemporaryDirectory(prefix="vibe-install-project-") as td, tempfile.TemporaryDirectory(prefix="vibe-install-home-") as hd:
            project = Path(td)
            env = os.environ.copy()
            env["VIBE_CODING_HOME"] = hd
            rc, out = run(["git", "init", "-q"], project)
            if rc == 0:
                rc1, out1 = run(
                    [sys.executable, str(root / "scripts" / "local_workspace.py"), "init", "--root", str(project), "--json"],
                    root,
                    env,
                )
                rc2, out2 = run(
                    [sys.executable, str(root / "scripts" / "repository_purity.py"), "--root", str(project), "--strict-excludes", "--json"],
                    root,
                    env,
                )
                workspace_smoke = {
                    "ok": rc1 == 0 and rc2 == 0 and not (project / ".gitignore").exists(),
                    "workspace_output": out1[-1000:],
                    "purity_output": out2[-1000:],
                }
                if not workspace_smoke["ok"]:
                    failures.append("local workspace/purity smoke test failed")
            else:
                failures.append(f"temporary Git repository initialization failed: {out}")

    optional_tools = {
        "graphify": bool(shutil.which("graphify")),
        "trivy": bool(shutil.which("trivy")),
        "gh": bool(shutil.which("gh")),
    }
    for tool, present in optional_tools.items():
        if not present:
            warnings.append(f"optional tool not installed: {tool}")

    return {
        "status": "BLOCK" if failures else ("WARN" if warnings else "PASS"),
        "offline": True,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "skill": metadata,
        "python_supported": python_ok,
        "git_installed": bool(shutil.which("git")),
        "optional_tools": optional_tools,
        "workspace_smoke": workspace_smoke,
        "failures": failures,
        "warnings": warnings,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    result = validate(Path(ns.skill_root))
    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Installation Check: {result['status']}")
        for failure in result["failures"]:
            print(f"ERROR: {failure}")
        for warning in result["warnings"]:
            print(f"WARN: {warning}")
    return 2 if result["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
