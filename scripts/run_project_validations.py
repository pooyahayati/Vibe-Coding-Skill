#!/usr/bin/env python3
"""Run representative project validations against deterministic skill policies."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "validation" / "project-cases.json"
FIXTURES = ROOT / "validation" / "projects"


def load(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)


def init_repo(root: Path) -> None:
    git(root, "init", "-q")
    git(root, "config", "user.email", "validation@example.invalid")
    git(root, "config", "user.name", "Validation")
    git(root, "add", ".")
    git(root, "commit", "-qm", "fixture baseline")


def run_json(cmd: list[str], cwd: Path) -> tuple[int, dict]:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if not p.stdout.strip():
        raise RuntimeError(f"no JSON output from {' '.join(cmd)}: {p.stderr}")
    return p.returncode, json.loads(p.stdout)


def main() -> int:
    risk = load("risk_classifier.py")
    data = json.loads(CASES.read_text(encoding="utf-8"))
    failures: list[str] = []
    rows: list[dict[str, object]] = []

    for case in data["cases"]:
        with tempfile.TemporaryDirectory(prefix=f"vibe-{case['id']}-") as td:
            root = Path(td)
            shutil.copytree(FIXTURES / case["fixture"], root, dirs_exist_ok=True)
            init_repo(root)
            before = git(root, "status", "--porcelain").stdout

            result = risk.classify(case["task"], case.get("paths", []))
            tier_ok = result["tier"] == case["expected_tier"]
            approval_ok = bool(result["approval_required"]) == bool(case["approval_required"])

            bootstrap_cmd = [
                sys.executable, str(ROOT / "scripts" / "bootstrap_project.py"),
                "--root", str(root),
                "--profile", case["bootstrap_profile"],
                "--objective", case["objective"],
                "--dry-run", "--json",
            ]
            _, bootstrap = run_json(bootstrap_cmd, root)

            gate_cmd = [
                sys.executable, str(ROOT / "scripts" / "integration_guard.py"),
                "--root", str(root),
                "--tier", str(case["expected_tier"]),
                "--json",
            ]
            gate_rc, gate = run_json(gate_cmd, root)
            after = git(root, "status", "--porcelain").stdout

            read_only_ok = before == after
            gate_status_ok = gate["status"] == case["expected_integration_status"]
            gate_rc_ok = gate_rc == (2 if case["expected_integration_status"] == "FAIL" else 0)

            checks = {
                "tier": tier_ok,
                "approval": approval_ok,
                "bootstrap_profile": bootstrap["profile"] == case["bootstrap_profile"],
                "integration_status": gate_status_ok,
                "integration_exit": gate_rc_ok,
                "read_only": read_only_ok,
            }
            failed = [name for name, ok in checks.items() if not ok]
            if failed:
                failures.append(f"{case['id']}: {', '.join(failed)}")

            rows.append({
                "id": case["id"],
                "fixture": case["fixture"],
                "tier": result["tier"],
                "approval_required": result["approval_required"],
                "integration_status": gate["status"],
                "checks": checks,
            })

    print(json.dumps({"results": rows, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
