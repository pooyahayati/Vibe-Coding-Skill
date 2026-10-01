#!/usr/bin/env python3
"""Local project-state capture, drift detection, and handoff summary."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import graph_provider
import github_traceability
import local_workspace
import behavior_contract

DOCS = [
    "STATUS.md",
    "PROJECT.md",
    "ROADMAP.md",
    "ARCHITECTURE.md",
    "PROJECT_GRAPH.md",
    "AGENTS.md",
    "README.md",
]


def run_git(root: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    return p.returncode, (p.stdout or p.stderr).strip()


def file_hash(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_state(root: Path, task_contract=None, completion_report=None, delivery_notes=None,
                  new_task: bool = False, accept_contract_change: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    local_workspace.ensure_git_repo(root)
    _, head = run_git(root, "rev-parse", "HEAD")
    _, branch = run_git(root, "branch", "--show-current")
    _, status = run_git(root, "status", "--porcelain")
    _, origin = run_git(root, "remote", "get-url", "origin")

    project_meta_path = local_workspace.state_path(root, "project.json", create=False)
    project_meta = None
    if project_meta_path.exists():
        try:
            project_meta = json.loads(project_meta_path.read_text(encoding="utf-8"))
        except Exception:
            project_meta = None

    current = {
        "schema_version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "project_id": local_workspace.project_id(root),
        "root": str(root),
        "git": {
            "head": head or None,
            "branch": branch or None,
            "dirty": bool(status),
            "origin": origin or None,
            "working_tree_fingerprint": graph_provider.working_tree_fingerprint(root),
        },
        "graph": graph_provider.status(root),
        "github": github_traceability.detect(root),
        "project": project_meta,
        "documents": {
            name: {"present": (root / name).exists(), "sha256": file_hash(root / name)}
            for name in DOCS
        },
    }
    previous = load_previous(root) or {}
    retained = previous.get("task_contract")
    if retained is not None:
        retained = behavior_contract.validate(retained)
        if previous.get("task_contract_sha256") != behavior_contract.digest(retained):
            raise ValueError("retained task contract fingerprint mismatch")
    contract = behavior_contract.validate(task_contract) if task_contract is not None else retained
    if new_task and accept_contract_change is not None:
        raise ValueError("choose a new task or a reconciled contract change, not both")
    if new_task and (task_contract is None or (retained and contract["task_id"] == retained["task_id"])):
        raise ValueError("--new-task needs an explicit contract with a different task_id")
    if retained and contract and not new_task and accept_contract_change is None:
        failures = behavior_contract.compare(retained, contract)
        if failures:
            raise ValueError("; ".join(failures))
    if retained and contract and not new_task and contract["risk_tier"] < retained["risk_tier"]:
        raise ValueError("contract reconciliation cannot lower the retained risk floor")
    if new_task:
        previous = {}
    elif accept_contract_change is not None:
        if not behavior_contract.text(accept_contract_change) or task_contract is None or retained is None:
            raise ValueError("contract reconciliation needs a retained and explicit replacement contract plus reason")
        if contract["task_id"] != retained["task_id"]:
            raise ValueError("a different task_id requires --new-task")
        current["contract_reconciliation"] = {"reason": accept_contract_change,
            "previous_contract": retained, "previous_sha256": behavior_contract.digest(retained),
            "authorization_verified": False}
    elif previous.get("contract_reconciliation"):
        current["contract_reconciliation"] = previous["contract_reconciliation"]
    notes = dict(previous.get("delivery") or {})
    if delivery_notes:
        notes.update(delivery_notes)
    for field in ("how_to_use", "how_to_check", "next_action"):
        if field in notes and not behavior_contract.text(notes[field]):
            raise ValueError("delivery " + field + " must be a nonempty string")
    if "limitations" in notes and not behavior_contract.strings(notes["limitations"]):
        raise ValueError("delivery limitations must be a string array")
    if notes:
        current["delivery"] = notes
    if contract is not None:
        current["task_contract"] = contract
        current["task_contract_sha256"] = behavior_contract.digest(contract)
        context = {"head": current["git"]["head"], "working_tree_fingerprint": current["git"]["working_tree_fingerprint"],
                   "contract_sha256": current["task_contract_sha256"]}
        report = completion_report if completion_report is not None else previous.get("completion_report")
        report_context = context if completion_report is not None else previous.get("completion_context")
        current["acceptance"] = behavior_contract.completion(contract, report, report is not None and context != report_context)
        if report is not None:
            current["completion_report"] = report
            current["completion_context"] = report_context
    elif completion_report is not None:
        raise ValueError("completion report needs a task contract")
    return current


def state_path(root: Path, create: bool = False) -> Path:
    return local_workspace.state_path(root, "project-state.json", create=create)


def load_previous(root: Path) -> dict[str, Any] | None:
    path = state_path(root, create=False)
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("state must be an object")
        return value
    except (ValueError, OSError) as exc:
        raise RuntimeError("local project state is unreadable; repair before replacing it") from exc


def compare(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    if not previous:
        return {"baseline_exists": False, "changes": ["no previous local state snapshot"]}
    changes: list[str] = []
    if previous.get("task_contract_sha256") != current.get("task_contract_sha256"):
        changes.append("task acceptance contract changed")
    if previous.get("git", {}).get("head") != current.get("git", {}).get("head"):
        changes.append("git head changed")
    if previous.get("git", {}).get("branch") != current.get("git", {}).get("branch"):
        changes.append("git branch changed")
    if previous.get("git", {}).get("working_tree_fingerprint") != current.get("git", {}).get("working_tree_fingerprint"):
        changes.append("working tree changed")
    if previous.get("graph", {}).get("fresh") != current.get("graph", {}).get("fresh"):
        changes.append("graph freshness changed")
    if previous.get("github", {}).get("repository") != current.get("github", {}).get("repository"):
        changes.append("GitHub repository identity changed")
    previous_docs = previous.get("documents", {})
    current_docs = current.get("documents", {})
    for name in DOCS:
        if previous_docs.get(name, {}).get("sha256") != current_docs.get(name, {}).get("sha256"):
            changes.append(f"{name} changed")
    return {"baseline_exists": True, "changes": changes}


def capture(root: Path, **task_options) -> dict[str, Any]:
    previous = load_previous(root)
    current = current_state(root, **task_options)
    local_workspace.initialize(root)
    current["drift_from_previous"] = compare(previous, current)
    path = state_path(root, create=True)
    path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    current["state_path"] = str(path)
    return current


def drift(root: Path, **task_options) -> dict[str, Any]:
    previous = load_previous(root)
    current = current_state(root, **task_options)
    comparison = compare(previous, current)
    status = "WARN" if comparison["changes"] else "PASS"
    if not comparison["baseline_exists"]:
        status = "WARN"
    return {"status": status, "comparison": comparison, "current": current}


def handoff_markdown(state: dict[str, Any]) -> str:
    project = state.get("project") or {}
    objective = project.get("current_objective") or "Read STATUS.md / PROJECT.md if present."
    graph = state.get("graph") or {}
    github = state.get("github") or {}
    git_state = state.get("git") or {}
    lines = [
        "# Local Handoff Snapshot",
        "",
        f"- Objective: {objective}",
        f"- Branch: {git_state.get('branch')}",
        f"- HEAD: {git_state.get('head')}",
        f"- Working tree dirty: {git_state.get('dirty')}",
        f"- Graph fresh: {graph.get('fresh')}",
        f"- Graph path: {graph.get('graph_path')}",
        f"- GitHub repository: {github.get('repository')}",
        "",
        "Resume order:",
        "STATUS.md -> PROJECT.md -> ROADMAP.md -> ARCHITECTURE.md -> PROJECT_GRAPH.md -> AGENTS.md -> GitHub -> source/tests",
        "",
        "This file is local operational state. Do not commit it to the project repository.",
        "",
    ]
    lines.extend(behavior_contract.handoff_lines(state))
    return "\n".join(lines)


def handoff(root: Path, write_local: bool, **task_options) -> dict[str, Any]:
    state = capture(root, **task_options)
    markdown = handoff_markdown(state)
    result = {"state": state, "markdown": markdown}
    if write_local:
        path = local_workspace.state_path(root, "handoff.md", create=True)
        path.write_text(markdown, encoding="utf-8")
        result["handoff_path"] = str(path)
    return result


def main() -> int:
    behavior_contract.configure_output()
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    for command in ("capture", "drift", "handoff"):
        p = sub.add_parser(command)
        p.add_argument("--root", default=".")
        p.add_argument("--json", action="store_true")
        p.add_argument("--task-contract", help="optional retained behavior contract JSON")
        p.add_argument("--completion-report", help="schema-2 reported outcome JSON; not execution proof")
        p.add_argument("--new-task", action="store_true", help="begin a different explicitly supplied task, within existing authorization")
        p.add_argument("--accept-contract-change", metavar="REASON", help="record a Head-reconciled material change; does not grant authorization")
        for field in ("how-to-use", "how-to-check", "next-action"):
            p.add_argument("--" + field)
        p.add_argument("--limitation", action="append", default=None)
        if command == "handoff":
            p.add_argument("--write-local", action="store_true")

    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    try:
        options = {
            "task_contract": behavior_contract.read(ns.task_contract) if ns.task_contract else None,
            "completion_report": json.loads(Path(ns.completion_report).read_text(encoding="utf-8")) if ns.completion_report else None,
            "new_task": ns.new_task,
            "accept_contract_change": ns.accept_contract_change,
            "delivery_notes": {k: v for k, v in {
                "how_to_use": ns.how_to_use, "how_to_check": ns.how_to_check,
                "next_action": ns.next_action, "limitations": ns.limitation,
            }.items() if v is not None},
        }
        if ns.command == "capture":
            result = capture(root, **options)
        elif ns.command == "drift":
            result = drift(root, **options)
        else:
            result = handoff(root, ns.write_local, **options)
    except (RuntimeError, ValueError, OSError) as exc:
        if ns.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}")
        return 2

    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif ns.command == "handoff":
        print(result["markdown"])
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    state = result.get("state", result.get("current", result))
    return 2 if state.get("acceptance", {}).get("gate") == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
