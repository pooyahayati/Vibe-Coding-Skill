#!/usr/bin/env python3
"""Deterministic core contract for the Real Delivery Benchmark.

Phase 9A deliberately has no real Codex/Claude adapter. It proves the
workspace-write, control/treatment, hidden-grader, and provenance contracts
with an injected executor and a deterministic self-test.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "evals" / "delivery" / "scenarios.json"
RESULT_SCHEMA_PATH = ROOT / "evals" / "delivery-result.schema.json"
DELIVERY_ROOT = ROOT / "evals" / "delivery"
AGENTS_PATH = ROOT / "config" / "agent-benchmarks.json"
PORTABLE_SKILL = ROOT / "skills" / "vibe-coding-skill"
ARMS = {"control", "treatment"}
GRADER_CATEGORIES = {
    "functional", "regression", "artifact", "security",
    "forbidden-mutation", "delivery",
}
Executor = Callable[
    [Path, str, str, dict[str, Any], int, dict[str, str]],
    dict[str, Any],
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hash(root: Path, excluded_roots: set[str] | None = None) -> str:
    excluded_roots = excluded_roots or set()
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root)
        if ".git" in rel.parts or (rel.parts and rel.parts[0] in excluded_roots):
            continue
        digest.update(rel.as_posix().encode("utf-8") + b"\0")
        digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def _require_under(path: Path, root: Path) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{path} must stay under {root}") from exc


def scenario_paths(
    scenario: dict[str, Any],
    delivery_root: Path = DELIVERY_ROOT,
) -> tuple[Path, Path]:
    fixture_rel = str(scenario.get("fixture") or "").strip()
    grader_rel = str(scenario.get("grader") or "").strip()
    if not fixture_rel or not grader_rel:
        raise ValueError("delivery scenario requires fixture and grader")
    fixture = (delivery_root / fixture_rel).resolve()
    grader = (delivery_root / grader_rel).resolve()
    _require_under(fixture, delivery_root / "fixtures")
    _require_under(grader, delivery_root / "graders")
    return fixture, grader


def validate_catalog(
    catalog: dict[str, Any],
    *,
    delivery_root: Path = DELIVERY_ROOT,
    require_files: bool = True,
) -> list[str]:
    failures: list[str] = []
    if catalog.get("schema_version") != 1:
        failures.append("delivery catalog schema_version must be 1")
    if catalog.get("benchmark") != "real-delivery":
        failures.append("delivery catalog benchmark must be 'real-delivery'")
    repetitions = catalog.get("default_repetitions")
    if not isinstance(repetitions, int) or isinstance(repetitions, bool) or repetitions < 1:
        failures.append("default_repetitions must be a positive integer")

    scenarios = catalog.get("scenarios")
    if not isinstance(scenarios, list):
        return failures + ["delivery catalog scenarios must be an array"]

    seen: set[str] = set()
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            failures.append(f"scenario {index} must be an object")
            continue
        sid = str(scenario.get("id") or "").strip()
        if not sid:
            failures.append(f"scenario {index} requires id")
        elif sid in seen:
            failures.append(f"duplicate delivery scenario id: {sid}")
        else:
            seen.add(sid)
        if not str(scenario.get("prompt") or "").strip():
            failures.append(f"scenario {sid or index} requires prompt")
        if str(scenario.get("network_policy") or "") not in {
            "disabled", "scenario-required"
        }:
            failures.append(
                f"scenario {sid or index} network_policy must be "
                "disabled or scenario-required"
            )
        forbidden = scenario.get("forbidden_paths", [])
        if not isinstance(forbidden, list) or not all(
            isinstance(value, str) and value.strip() for value in forbidden
        ):
            failures.append(
                f"scenario {sid or index} forbidden_paths must be an array of strings"
            )
        try:
            fixture, grader = scenario_paths(scenario, delivery_root)
        except ValueError as exc:
            failures.append(f"scenario {sid or index}: {exc}")
            continue
        if require_files and not fixture.is_dir():
            failures.append(f"scenario {sid or index} fixture is missing: {fixture}")
        if require_files and not grader.is_file():
            failures.append(f"scenario {sid or index} grader is missing: {grader}")
    return failures


def git(workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=workspace, text=True, capture_output=True
    )


def _copy_fixture(fixture: Path, workspace: Path) -> None:
    for source in fixture.iterdir():
        target = workspace / source.name
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copyfile(source, target)


def skill_dir_for_agent(agent: str) -> str:
    try:
        spec = (load_json(AGENTS_PATH).get("agents") or {}).get(agent)
        if isinstance(spec, dict) and str(spec.get("skill_dir") or "").strip():
            return str(spec["skill_dir"])
    except Exception:
        pass
    return ".benchmark/skills/vibe-coding-skill"


def prepare_workspace(
    fixture: Path,
    workspace: Path,
    *,
    arm: str,
    agent: str,
    portable_skill: Path = PORTABLE_SKILL,
) -> dict[str, Any]:
    if arm not in ARMS:
        raise ValueError(f"unknown delivery benchmark arm: {arm}")
    workspace.mkdir(parents=True)
    _copy_fixture(fixture, workspace)
    if git(workspace, "init", "-q").returncode != 0:
        raise RuntimeError("git init failed")
    git(workspace, "config", "user.email", "benchmark@example.invalid")
    git(workspace, "config", "user.name", "Vibe Delivery Benchmark")
    git(workspace, "add", "-A")
    commit = git(workspace, "commit", "-qm", "delivery benchmark baseline")
    if commit.returncode != 0:
        raise RuntimeError(commit.stderr or "baseline commit failed")
    baseline = git(workspace, "rev-parse", "HEAD").stdout.strip()

    skill_dir = operational_root = None
    if arm == "treatment":
        skill_dir = skill_dir_for_agent(agent)
        target = workspace / skill_dir
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(portable_skill, target)
        operational_root = Path(skill_dir).parts[0]
        exclude = git(workspace, "rev-parse", "--git-path", "info/exclude")
        if exclude.returncode != 0:
            raise RuntimeError("cannot locate git exclude file")
        exclude_path = Path(exclude.stdout.strip())
        if not exclude_path.is_absolute():
            exclude_path = (workspace / exclude_path).resolve()
        with exclude_path.open("a", encoding="utf-8") as handle:
            handle.write(f"\n/{operational_root}/\n")

    return {
        "baseline_commit": baseline,
        "skill_dir": skill_dir,
        "operational_root": operational_root,
    }


def build_prompt(scenario: dict[str, Any], *, arm: str, skill_dir: str | None) -> str:
    text = (
        "Implement the requested change in the current repository. "
        "You may edit project files and run relevant local checks. "
        "Do not deploy, push Git changes, read unrelated host files, expose "
        "credentials, or perform external side effects."
    )
    if arm == "treatment":
        text += " Use the installed Vibe Coding Skill"
        text += f" from {skill_dir}." if skill_dir else "."
    else:
        text += " Do not assume the Vibe Coding Skill is installed."
    if scenario.get("network_policy", "disabled") == "disabled":
        text += " Network access is not part of this benchmark scenario."
    return f"{text}\n\nTask:\n{scenario['prompt']}\n"


def changed_paths(workspace: Path) -> list[str]:
    result = git(workspace, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "git status failed")
    rows: list[str] = []
    parts = [value for value in result.stdout.split("\0") if value]
    index = 0
    while index < len(parts):
        row = parts[index]
        if len(row) >= 4:
            status, path = row[:2], row[3:]
            if status[0] in {"R", "C"} and index + 1 < len(parts):
                index += 1
                path = parts[index]
            rows.append(path.replace("\\", "/"))
        index += 1
    return sorted(dict.fromkeys(rows))


def diff_hash(workspace: Path, paths: list[str]) -> str:
    digest = hashlib.sha256()
    tracked = git(workspace, "diff", "--binary", "HEAD")
    if tracked.returncode != 0:
        raise RuntimeError(tracked.stderr or "git diff failed")
    digest.update(tracked.stdout.encode("utf-8", "surrogateescape"))
    tracked_names = set(git(workspace, "diff", "--name-only", "HEAD").stdout.splitlines())
    for rel in paths:
        if rel in tracked_names:
            continue
        path = workspace / rel
        digest.update(rel.encode("utf-8") + b"\0")
        if path.is_file():
            digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def dependency_files_changed(paths: list[str]) -> list[str]:
    names = {
        "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
        "composer.json", "composer.lock", "pyproject.toml", "poetry.lock",
        "requirements.txt", "Cargo.toml", "Cargo.lock", "go.mod", "go.sum",
    }
    return sorted(
        rel for rel in paths
        if Path(rel).name in names or Path(rel).name.startswith("requirements")
    )


def forbidden_path_hits(paths: list[str], patterns: list[str]) -> list[str]:
    return sorted({
        rel for rel in paths
        if any(
            fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch("/" + rel, pattern)
            for pattern in patterns
        )
    })


def sanitized_env(base: Path) -> dict[str, str]:
    env = {
        key: value for key, value in os.environ.items()
        if key in {
            "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC",
            "LANG", "LC_ALL", "TERM",
        }
    }
    home, temp = base / "home", base / "tmp"
    home.mkdir()
    temp.mkdir()
    env.update({
        "HOME": str(home), "USERPROFILE": str(home),
        "TMPDIR": str(temp), "TMP": str(temp), "TEMP": str(temp),
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    return env


def validate_grader_output(raw: Any) -> tuple[dict[str, Any], list[str]]:
    if not isinstance(raw, dict):
        return {"checks": [], "metrics": {}}, ["grader output must be a JSON object"]
    failures: list[str] = []
    if raw.get("schema_version") != 1:
        failures.append("grader schema_version must be 1")
    checks = raw.get("checks")
    if not isinstance(checks, list) or not checks:
        failures.append("grader checks must be a non-empty array")
        checks = []

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            failures.append(f"grader check {index} must be an object")
            continue
        cid = str(check.get("id") or "").strip()
        category = str(check.get("category") or "").strip()
        if not cid:
            failures.append(f"grader check {index} requires id")
        elif cid in seen:
            failures.append(f"duplicate grader check id: {cid}")
        else:
            seen.add(cid)
        if category not in GRADER_CATEGORIES:
            failures.append(f"grader check {cid or index} has unsupported category")
        if not isinstance(check.get("required"), bool):
            failures.append(f"grader check {cid or index} requires boolean required")
        if not isinstance(check.get("passed"), bool):
            failures.append(f"grader check {cid or index} requires boolean passed")
        normalized.append({
            "id": cid,
            "category": category,
            "required": check.get("required") is True,
            "passed": check.get("passed") is True,
            "details": str(check.get("details") or ""),
        })
    return {
        "checks": normalized,
        "metrics": raw.get("metrics") if isinstance(raw.get("metrics"), dict) else {},
    }, failures


def run_hidden_grader(
    grader: Path,
    workspace: Path,
    *,
    timeout: int,
    env: dict[str, str],
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [sys.executable, str(grader), "--workspace", str(workspace), "--json"],
            cwd=grader.parent,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "exit_code": 124,
            "timed_out": True,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "grader timeout",
            "parsed": {"checks": [], "metrics": {}},
            "failures": ["grader_timeout"],
        }

    failures: list[str] = []
    parsed: Any = None
    if completed.returncode == 0:
        try:
            parsed = json.loads(completed.stdout)
        except Exception as exc:
            failures.append(f"grader_json_error:{exc}")
    else:
        failures.append(f"grader_exit_code:{completed.returncode}")
    normalized, shape_failures = validate_grader_output(parsed)
    return {
        "exit_code": completed.returncode,
        "timed_out": False,
        "stdout": completed.stdout or "",
        "stderr": completed.stderr or "",
        "parsed": normalized,
        "failures": failures + shape_failures,
    }


def run_one(
    *,
    agent: str,
    scenario: dict[str, Any],
    arm: str,
    repetition: int,
    result_dir: Path,
    executor: Executor,
    model: str | None = None,
    timeout: int = 600,
    grader_timeout: int = 120,
    delivery_root: Path = DELIVERY_ROOT,
    portable_skill: Path = PORTABLE_SKILL,
    catalog_path: Path = CATALOG_PATH,
    result_schema_path: Path = RESULT_SCHEMA_PATH,
) -> dict[str, Any]:
    fixture, grader_path = scenario_paths(scenario, delivery_root)
    started_at, started = utc_now(), time.monotonic()
    result_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="vibe-delivery-benchmark-") as td:
        base, workspace = Path(td), Path(td) / "workspace"
        info = prepare_workspace(
            fixture, workspace, arm=arm, agent=agent, portable_skill=portable_skill
        )
        prompt = build_prompt(scenario, arm=arm, skill_dir=info["skill_dir"])
        env = sanitized_env(base)
        raw = executor(workspace, prompt, arm, scenario, timeout, env)
        if not isinstance(raw, dict):
            raise RuntimeError("executor must return an object")
        exit_code = raw.get("exit_code")
        if not isinstance(exit_code, int) or isinstance(exit_code, bool):
            raise RuntimeError("executor requires integer exit_code")

        paths = changed_paths(workspace)
        operational_root = info["operational_root"]
        product_paths = [
            rel for rel in paths
            if not operational_root
            or (rel != operational_root and not rel.startswith(operational_root + "/"))
        ]
        forbidden = forbidden_path_hits(
            product_paths,
            [str(value) for value in scenario.get("forbidden_paths", [])],
        )
        excluded = {operational_root} if operational_root else set()
        final_tree_sha256 = tree_hash(workspace, excluded)
        product_diff_sha256 = diff_hash(workspace, product_paths)
        dependency_changes = dependency_files_changed(product_paths)

        grader_workspace = base / "grader-workspace"
        shutil.copytree(
            workspace,
            grader_workspace,
            ignore=shutil.ignore_patterns(".git"),
        )
        grader = run_hidden_grader(
            grader_path, grader_workspace, timeout=grader_timeout, env=env
        )

        failures = list(grader["failures"])
        if exit_code != 0:
            failures.append(f"executor_exit_code:{exit_code}")
        if forbidden:
            failures.append("forbidden_path_mutation:" + ",".join(forbidden))
        failures.extend(
            f"required_check_failed:{check['id']}"
            for check in grader["parsed"]["checks"]
            if check["required"] and not check["passed"]
        )
        failures = list(dict.fromkeys(failures))

        stem = f"{scenario['id']}.{arm}.r{repetition}"
        raw_files = {
            "stdout": stem + ".stdout.txt",
            "stderr": stem + ".stderr.txt",
            "grader_stdout": stem + ".grader.stdout.txt",
            "grader_stderr": stem + ".grader.stderr.txt",
        }
        raw_values = {
            "stdout": str(raw.get("stdout") or ""),
            "stderr": str(raw.get("stderr") or ""),
            "grader_stdout": grader["stdout"],
            "grader_stderr": grader["stderr"],
        }
        for key, filename in raw_files.items():
            (result_dir / filename).write_text(raw_values[key], encoding="utf-8")

        envelope = {
            "schema_version": 1,
            "benchmark": "real-delivery",
            "agent": agent,
            "agent_version": raw.get("agent_version"),
            "model": raw.get("model") or model,
            "arm": arm,
            "scenario_id": str(scenario["id"]),
            "repetition": repetition,
            "skill_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
            "started_at": started_at,
            "completed_at": utc_now(),
            "runtime": {
                "exit_code": exit_code,
                "duration_ms": int((time.monotonic() - started) * 1000),
                "timed_out": bool(raw.get("timed_out")),
                "usage": raw.get("usage") if isinstance(raw.get("usage"), dict) else {},
            },
            "workspace": {
                "baseline_commit": info["baseline_commit"],
                "final_tree_sha256": final_tree_sha256,
                "diff_sha256": product_diff_sha256,
                "changed_paths": product_paths,
                "changed_file_count": len(product_paths),
                "dependency_files_changed": dependency_changes,
                "forbidden_path_hits": forbidden,
            },
            "grader": {
                "exit_code": grader["exit_code"],
                "timed_out": grader["timed_out"],
                "checks": grader["parsed"]["checks"],
                "metrics": grader["parsed"]["metrics"],
                "failures": failures,
                "delivery_success": not failures,
            },
            "integrity": {
                "fixture_sha256": tree_hash(fixture),
                "grader_sha256": sha256_file(grader_path),
                "catalog_sha256": sha256_file(catalog_path),
                "result_schema_sha256": sha256_file(result_schema_path),
                "skill_tree_sha256": tree_hash(portable_skill),
                "skill_installed": arm == "treatment",
                "hidden_grader_outside_workspace": True,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "executor_id": str(raw.get("executor_id") or "injected-executor"),
            },
            "raw_files": raw_files,
        }
        (result_dir / (stem + ".json")).write_text(
            json.dumps(envelope, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return envelope


def deterministic_fake_executor(
    workspace: Path,
    prompt: str,
    arm: str,
    scenario: dict[str, Any],
    timeout: int,
    env: dict[str, str],
) -> dict[str, Any]:
    (workspace / "message.txt").write_text("implemented\n", encoding="utf-8")
    return {
        "exit_code": 0,
        "stdout": "fake executor completed",
        "stderr": "",
        "agent_version": "fake-1",
        "model": "deterministic",
        "executor_id": "phase-9a-fake",
        "usage": {"turns": 1},
    }


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="vibe-delivery-self-test-") as td:
        base = Path(td)
        delivery_root = base / "delivery"
        fixture = delivery_root / "fixtures" / "framework"
        grader = delivery_root / "graders" / "framework.py"
        fixture.mkdir(parents=True)
        grader.parent.mkdir(parents=True)
        (fixture / "message.txt").write_text("baseline\n", encoding="utf-8")
        grader.write_text(
            "import argparse,json\n"
            "from pathlib import Path\n"
            "ap=argparse.ArgumentParser()\n"
            "ap.add_argument('--workspace',required=True)\n"
            "ap.add_argument('--json',action='store_true')\n"
            "ns=ap.parse_args()\n"
            "ok=(Path(ns.workspace)/'message.txt').read_text()=='implemented\\n'\n"
            "print(json.dumps({'schema_version':1,'checks':["
            "{'id':'message-updated','category':'functional',"
            "'required':True,'passed':ok}],'metrics':{}}))\n",
            encoding="utf-8",
        )
        scenario = {
            "id": "framework",
            "prompt": "Update message.txt.",
            "fixture": "fixtures/framework",
            "grader": "graders/framework.py",
            "network_policy": "disabled",
            "forbidden_paths": [],
        }
        catalog = {
            "schema_version": 1,
            "benchmark": "real-delivery",
            "default_repetitions": 1,
            "scenarios": [scenario],
        }
        catalog_path = base / "scenarios.json"
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        schema_path = base / "schema.json"
        schema_path.write_text(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))
        failures = validate_catalog(catalog, delivery_root=delivery_root)
        if failures:
            return {"passed": False, "failures": failures}

        rows = [
            run_one(
                agent="fake",
                scenario=scenario,
                arm=arm,
                repetition=1,
                result_dir=base / "results" / arm,
                executor=deterministic_fake_executor,
                timeout=5,
                grader_timeout=5,
                delivery_root=delivery_root,
                portable_skill=PORTABLE_SKILL,
                catalog_path=catalog_path,
                result_schema_path=schema_path,
            )
            for arm in ("control", "treatment")
        ]
        return {
            "passed": all(row["grader"]["delivery_success"] for row in rows),
            "arms": {
                row["arm"]: {
                    "delivery_success": row["grader"]["delivery_success"],
                    "changed_paths": row["workspace"]["changed_paths"],
                    "skill_installed": row["integrity"]["skill_installed"],
                }
                for row in rows
            },
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("validate").add_argument("--json", action="store_true")
    sub.add_parser("self-test").add_argument("--json", action="store_true")
    ns = ap.parse_args()

    if ns.command == "validate":
        catalog = load_json(CATALOG_PATH)
        failures = validate_catalog(catalog)
        result = {
            "gate": "BLOCK" if failures else "PASS",
            "scenario_count": len(catalog.get("scenarios") or []),
            "failures": failures,
        }
        exit_code = 2 if failures else 0
    else:
        result = self_test()
        exit_code = 0 if result.get("passed") else 2

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
