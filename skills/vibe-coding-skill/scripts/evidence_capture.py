#!/usr/bin/env python3
"""E1: bounded local execution receipts; no completion or remote verification."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import signal
import stat
import subprocess
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import behavior_contract as behavior
import local_workspace

MAX_FILES = 10000
MAX_BYTES = 1024 * 1024 * 1024
REQUIREMENT_FIELDS = {"id", "criterion_ids", "kind", "origin", "required", "input_paths", "input_excludes", "artifact_paths", "description"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def relative(value: str) -> str:
    if not behavior.text(value) or "\\" in value or ":" in value or any(c in value for c in "*?[]\x00"):
        raise ValueError("use concrete project-relative forward-slash paths")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("path escapes project root")
    return path.as_posix()


def checked_path(root: Path, path: Path) -> Path:
    """Reject link/reparse traversal, including missing children beneath links."""
    path = Path(os.path.abspath(path))
    path.relative_to(root)
    current = root
    for part in path.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("symlink input/artifact is unsupported")
        if current.exists():
            info = current.lstat()
            if getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
                raise ValueError("reparse input/artifact is unsupported")
    path.resolve().relative_to(root)
    return path


def snapshot(root: Path, paths: list[str], excludes: list[str], max_files=MAX_FILES, max_bytes=MAX_BYTES, *, require_file=True) -> list[dict]:
    """Hash scoped files and directory membership, without consulting Git ignore."""
    root = root.resolve()
    selected = [relative(p) for p in paths]
    excluded = [relative(p) for p in excludes]
    if not selected or max_files < 1 or max_bytes < 1:
        raise ValueError("input scope and positive collection limits are required")
    if any(p == "." for p in excluded) or any(any(p == e or p.startswith(e + "/") for e in excluded) for p in selected):
        raise ValueError("exclusions cannot erase a selected input root")
    rows: dict[str, dict] = {}
    total = 0

    def visit(path: Path):
        nonlocal total
        path = checked_path(root, path)
        name = path.relative_to(root).as_posix()
        if any(name == e or name.startswith(e + "/") for e in excluded) or name in rows:
            return
        if len(rows) >= max_files:
            raise ValueError("input manifest entry limit exceeded")
        if not path.exists():
            rows[name] = {"path": name, "missing": True}
        elif path.is_dir():
            rows[name] = {"path": name, "directory": True}
            for child in sorted(path.iterdir()):
                visit(child)
        elif path.is_file():
            if not stat.S_ISREG(path.stat().st_mode):
                raise ValueError("unsupported input file")
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                while block := stream.read(1024 * 1024):
                    total += len(block)
                    if total > max_bytes:
                        raise ValueError("input hashing byte limit exceeded")
                    digest.update(block)
            rows[name] = {"path": name, "sha256": digest.hexdigest()}
        else:
            raise ValueError("unsupported input type")
    for name in selected:
        visit(root / name)
    if require_file and not any("sha256" in row for row in rows.values()):
        raise ValueError("input scope must contain at least one meaningful regular file")
    return [rows[key] for key in sorted(rows)]


def artifact_snapshot(root: Path, names: list[str], wordpress: bool = False) -> list[dict]:
    result = []
    total = 0
    if len(names) > MAX_FILES:
        raise ValueError("artifact entry limit exceeded")
    for name in names:
        path = Path(name)
        if not path.is_absolute():
            path = root / relative(name)
            checked_path(root, path)
        else:
            # An exact external file is allowed by the accepted requirement.
            checked_path(Path(path.anchor), path)
        path = path.resolve()
        if not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
            raise ValueError("required artifact is not a regular file")
        if path.stat().st_size > MAX_BYTES:
            raise ValueError("artifact hashing byte limit exceeded")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while block := stream.read(1024 * 1024):
                total += len(block)
                if total > MAX_BYTES:
                    raise ValueError("artifact hashing byte limit exceeded")
                digest.update(block)
        row = {"path": str(path), "sha256": digest.hexdigest()}
        if wordpress:
            import wordpress_artifact
            with zipfile.ZipFile(path) as archive:
                infos = archive.infolist()
                if len(infos) > MAX_FILES or sum(i.file_size for i in infos) > MAX_BYTES or any(i.file_size > 8 * 1024 * 1024 for i in infos if i.filename.lower().endswith(".php")):
                    raise ValueError("WordPress artifact inspection limit exceeded")
            identity = wordpress_artifact.verify_artifact(path)
            if identity["artifact_sha256"] != row["sha256"]:
                raise ValueError("WordPress artifact changed during inspection")
            row["version"] = identity["version"]
        result.append(row)
    return result


def requirement(contract: dict, requirement_id: str) -> dict:
    for row in contract["evidence_requirements"]:
        if row["id"] == requirement_id:
            if set(row) - REQUIREMENT_FIELDS:
                raise ValueError("unsupported evidence requirement fields; reconcile before execution")
            if row["origin"] != "collected":
                raise ValueError("runner cannot relabel manual/reported obligations as collected")
            return row
    raise ValueError("unknown evidence requirement")


def receipt_directory(root: Path, task_id: str) -> Path:
    workspace = local_workspace.project_workspace(root, create=False)
    if workspace.is_relative_to(root):
        raise ValueError("receipt workspace must stay outside product source")
    task = hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:16]
    destination = workspace / "test-artifacts" / "receipts" / task
    checked_path(local_workspace.workspace_home(), destination)
    return destination


def storage(root: Path, task_id: str) -> Path:
    destination = receipt_directory(root, task_id)
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def envelope(root: Path, contract: dict, obligation: dict) -> dict:
    rc, commit = local_workspace.run_git(root, "rev-parse", "HEAD")
    return {"format": "vibe-execution-receipt", "schema_version": 1,
            "id": "execution-" + uuid.uuid4().hex, "task_id": contract["task_id"],
            "contract_sha256": behavior.digest(contract), "requirement_id": obligation["id"],
            "criterion_ids": list(obligation["criterion_ids"]), "kind": obligation["kind"], "origin": "collected",
            "source": {"project_id": local_workspace.project_id(root), "root": str(root),
                       **({"commit": commit} if rc == 0 else {})}}


def persist(directory: Path, receipt: dict) -> dict:
    path = directory / (receipt["id"] + ".json")
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    return {"receipt": receipt, "receipt_path": str(path), "receipt_ref": path.name,
            "receipt_root": str(directory), "receipt_sha256": behavior.digest(receipt),
            "completion_verified": False}


def terminate(process: subprocess.Popen) -> bool:
    """Stop the launched group/tree on timeout; never claim pass after timeout."""
    tree_stopped = False
    try:
        if os.name == "nt":
            executable = Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32" / "taskkill.exe"
            result = subprocess.run([str(executable), "/PID", str(process.pid), "/T", "/F"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False)
            tree_stopped = result.returncode == 0
        else:
            os.killpg(process.pid, signal.SIGKILL)
            tree_stopped = True
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        process.kill()
        process.wait(timeout=5)
        return tree_stopped
    except (OSError, subprocess.TimeoutExpired):
        return False


def capture(root: Path, contract: dict, requirement_id: str, argv: list[str], cwd: Path | None = None,
            timeout_seconds: float = 60, context: dict | None = None, wordpress_artifacts: bool = False) -> dict:
    root = root.resolve()
    contract = behavior.validate(contract)
    obligation = requirement(contract, requirement_id)
    if not behavior.strings(argv, True) or any("\x00" in item for item in argv):
        raise ValueError("explicit nonempty argv required")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 86400:
        raise ValueError("timeout_seconds must be positive, finite and at most 86400")
    cwd = checked_path(root, cwd if cwd is not None else root)
    if not cwd.is_dir():
        raise ValueError("command cwd must be an existing directory inside project")
    context = {} if context is None else context
    if not isinstance(context, dict):
        raise ValueError("context must be an object without secrets")
    behavior.digest(context)
    directory = storage(root, contract["task_id"])
    receipt = envelope(root, contract, obligation)
    receipt.update({"result": "error", "started_at": now(), "context": context, "process_started": False,
                    "command": {"argv": list(argv), "cwd": str(cwd), "timeout_seconds": timeout_seconds, "exit_code": None}})
    paths = obligation["input_paths"]
    excludes = obligation.get("input_excludes", [])
    artifacts = obligation.get("artifact_paths", [])
    try:
        before = snapshot(root, paths, excludes)
        receipt["inputs"] = {"paths": list(paths), "excludes": list(excludes),
                             "before": before, "before_sha256": behavior.digest(before)}
        artifacts_before = artifact_snapshot(root, artifacts, wordpress_artifacts)
        if artifacts:
            receipt["artifacts_before"] = artifacts_before
        options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
        try:
            process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL, shell=False, **options)
            receipt["process_started"] = True
            try:
                receipt["command"]["exit_code"] = process.wait(timeout=timeout_seconds)
                receipt["result"] = "pass" if process.returncode == 0 else "fail"
                if process.returncode != 0:
                    receipt["reason"] = "command exited with code " + str(process.returncode)
            except subprocess.TimeoutExpired:
                stopped = terminate(process)
                receipt.update({"result": "timeout", "reason": "command exceeded its timeout",
                                "termination_confirmed": stopped})
                receipt["command"]["exit_code"] = process.returncode
        except OSError:
            receipt.update({"result": "error", "reason": "process could not start; check executable/cwd and host permissions"})
        after = snapshot(root, paths, excludes)
        receipt["inputs"].update({"after": after, "after_sha256": behavior.digest(after)})
        receipt["artifacts"] = artifact_snapshot(root, artifacts, wordpress_artifacts)
        if before != after or artifacts_before != receipt["artifacts"]:
            receipt.setdefault("collection_errors", []).append("scoped inputs or checked artifacts changed during execution")
            if receipt["result"] == "pass":
                receipt.update({"result": "error", "reason": "scoped inputs or checked artifacts changed during execution"})
    except (ValueError, OSError, RuntimeError, zipfile.BadZipFile) as exc:
        # Do not persist arbitrary exception text: it may contain sensitive paths/output.
        receipt.setdefault("collection_errors", []).append(type(exc).__name__ + ": input/artifact collection incomplete")
        if receipt["result"] not in {"fail", "timeout"}:
            receipt.update({"result": "error", "reason": "input/artifact collection incomplete; inspect the accepted scope and local access"})
    receipt["finished_at"] = now()
    return persist(directory, receipt)


def unavailable(root: Path, contract: dict, requirement_id: str, reason: str) -> dict:
    root = root.resolve()
    contract = behavior.validate(contract)
    obligation = requirement(contract, requirement_id)
    if not behavior.text(reason):
        raise ValueError("unavailable check needs a concrete reason without secrets")
    directory = storage(root, contract["task_id"])
    receipt = envelope(root, contract, obligation)
    receipt.update({"result": "unavailable", "recorded_at": now(), "reason": reason})
    return persist(directory, receipt)


def main() -> int:
    behavior.configure_output()
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="mode", required=True)
    for mode in ("run", "unavailable"):
        p = sub.add_parser(mode)
        p.add_argument("--root", default=".")
        p.add_argument("--task-contract", required=True)
        p.add_argument("--requirement", required=True)
        if mode == "run":
            p.add_argument("--cwd", help="project-relative directory; default project root")
            p.add_argument("--timeout", type=float, default=60)
            p.add_argument("--context", help="explicit JSON object with relevant runtime/dataset identity; no environment dump")
            p.add_argument("--wordpress-artifacts", action="store_true", help="reuse WordPress ZIP identity/version verification")
            p.add_argument("argv", nargs=argparse.REMAINDER, help="explicit already-authorized command after --")
        else:
            p.add_argument("--reason", required=True)
    ns = ap.parse_args()
    try:
        root = Path(ns.root).resolve()
        contract = behavior.read(ns.task_contract)
        if ns.mode == "run":
            argv = ns.argv[1:] if ns.argv[:1] == ["--"] else ns.argv
            cwd = root / relative(ns.cwd) if ns.cwd else root
            result = capture(root, contract, ns.requirement, argv, cwd, ns.timeout,
                             json.loads(ns.context) if ns.context else None, ns.wordpress_artifacts)
        else:
            result = unavailable(root, contract, ns.requirement, ns.reason)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["receipt"]["result"] == "pass" else 2
    except (ValueError, OSError, RuntimeError):
        print(json.dumps({"gate": "BLOCK", "error": "invalid capture configuration or inaccessible local workspace; no execution success claimed"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
