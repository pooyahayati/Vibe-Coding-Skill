#!/usr/bin/env python3
"""E2: resolve local receipts against independently supplied task/delivery context."""
from __future__ import annotations
import copy
import argparse
import json
import math
import re
from datetime import datetime
from pathlib import Path

import behavior_contract as behavior
import evidence_capture as capture

DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def timestamp(value):
    require(behavior._gate.valid_timestamp(value), "invalid receipt timestamp")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def read_receipt(root: Path, reference: str) -> dict:
    relative = capture.relative(reference)
    require(relative != ".", "receipt reference must be a file")
    path = capture.checked_path(root, root / relative)
    require(path.is_file() and path.stat().st_size <= 8 * 1024 * 1024, "missing/oversized receipt")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "receipt must be an object")
    if "log" in value:
        log = value["log"]
        require(isinstance(log, dict) and type(log.get("truncated")) is bool and type(log.get("redacted")) is bool, "invalid bounded log metadata")
        log_path = capture.checked_path(root, root / capture.relative(log.get("path")))
        require(log_path.is_file() and log_path.stat().st_size <= 8 * 1024 * 1024, "log unavailable/oversized")
        require(capture.hashlib.sha256(log_path.read_bytes()).hexdigest() == log.get("sha256"), "log digest mismatch")
    return value


def validate(receipt: dict, entry: dict, contract: dict, obligation: dict, root: Path, context: dict) -> dict:
    require(not set(obligation) - capture.REQUIREMENT_FIELDS, "unsupported evidence requirement fields; reconcile before completion")
    require(not set(receipt) - {"format", "schema_version", "id", "task_id", "contract_sha256", "requirement_id", "criterion_ids", "kind", "origin", "source", "result", "started_at", "finished_at", "recorded_at", "reason", "context", "command", "inputs", "artifacts", "artifacts_before", "observation", "provenance", "log", "process_started", "termination_confirmed", "collection_errors"}, "unsupported receipt fields")
    require(receipt.get("format") == "vibe-execution-receipt" and type(receipt.get("schema_version")) is int and receipt["schema_version"] == 1, "unsupported receipt format/version")
    require(DIGEST.fullmatch(str(entry.get("receipt_sha256") or "")) and entry["receipt_sha256"] == behavior.digest(receipt), "receipt digest mismatch/missing")
    for key, expected in (("id", entry.get("id")), ("task_id", contract["task_id"]),
                          ("contract_sha256", behavior.digest(contract)), ("requirement_id", obligation["id"]),
                          ("criterion_ids", obligation["criterion_ids"]), ("kind", obligation["kind"]),
                          ("origin", obligation["origin"]), ("result", entry.get("result"))):
        require(receipt.get(key) == expected, "receipt binding mismatch: " + key)
    require(entry.get("kind") == obligation["kind"] and entry.get("origin") == obligation["origin"] and entry.get("required") is obligation["required"], "report changed obligation kind/origin/required")
    require(receipt.get("result") in {"pass", "fail", "timeout", "error", "unavailable"}, "invalid receipt result")
    source = receipt.get("source")
    require(isinstance(source, dict) and source.get("root") == str(root) and source.get("project_id") == capture.local_workspace.project_id(root), "receipt belongs to another source")
    if receipt["result"] != "pass":
        require(behavior.text(receipt.get("reason")), "non-pass receipt needs reason")
        if receipt["result"] == "unavailable":
            timestamp(receipt.get("recorded_at"))
        return {"qualified": False, "reason": "receipt did not pass"}
    require(not receipt.get("collection_errors"), "receipt has collection errors")
    require(isinstance(receipt.get("context"), dict) and receipt["context"] == context, "relevant runtime/dataset context changed or unavailable")
    if receipt["origin"] == "reported":
        # A claimed resolution flag cannot authorize or stand in for a trusted resolver.
        raise ValueError("reported receipt requires an authorized external resolver; no resolver is configured")
    started, finished = timestamp(receipt.get("started_at")), timestamp(receipt.get("finished_at"))
    require(finished >= started, "receipt timestamps reversed")
    if receipt["origin"] == "collected":
        command = receipt.get("command")
        require(isinstance(command, dict) and behavior.strings(command.get("argv"), True), "collected receipt needs explicit command")
        require(not set(command) - {"argv", "cwd", "timeout_seconds", "exit_code"}, "unsupported command fields")
        require(receipt.get("process_started") is True and type(command.get("exit_code")) is int and command["exit_code"] == 0, "collected pass was not executed successfully")
        timeout = command.get("timeout_seconds")
        require(type(timeout) in {int, float} and math.isfinite(timeout) and 0 < timeout <= 86400, "invalid command timeout")
        cwd = command.get("cwd")
        require(behavior.text(cwd) and Path(cwd).is_absolute(), "missing explicit cwd")
        require(capture.checked_path(root, Path(cwd)).is_dir(), "command cwd unavailable")
    elif receipt["origin"] == "manual":
        observation = receipt.get("observation")
        require(isinstance(observation, dict) and all(behavior.text(observation.get(k)) for k in ("description", "method", "environment")), "manual receipt needs a concrete observation/method/environment")
        require("command" not in receipt, "manual receipt cannot claim a command exit")
    else:
        raise ValueError("unsupported evidence origin")
    inputs = receipt.get("inputs")
    paths = obligation.get("input_paths") or (contract["scope"] if receipt["origin"] == "manual" else [])
    excludes = obligation.get("input_excludes", [])
    require(isinstance(inputs, dict) and inputs.get("paths") == paths and inputs.get("excludes") == excludes, "receipt narrowed input scope")
    before, after = inputs.get("before"), inputs.get("after")
    require(isinstance(before, list) and before == after and inputs.get("before_sha256") == behavior.digest(before) and inputs.get("after_sha256") == behavior.digest(after), "input manifest changed/invalid")
    require(capture.snapshot(root, paths, excludes) == after, "tested inputs are stale")
    artifacts = receipt.get("artifacts", [])
    require(isinstance(artifacts, list), "artifact manifest invalid")
    expected = capture.artifact_snapshot(root, obligation.get("artifact_paths", []), any("version" in a for a in artifacts if isinstance(a, dict)))
    require(artifacts == expected, "checked artifacts are stale/mismatched")
    require(receipt.get("artifacts_before", artifacts) == artifacts, "artifact changed during check")
    rc, commit = capture.local_workspace.run_git(root, "rev-parse", "HEAD")
    return {"qualified": True, "tested_commit": source.get("commit"), "provenance": {
            "source": receipt["origin"] + " local receipt, scoped inputs verified at delivery", "reference": entry["receipt_ref"],
            **({"commit": commit} if rc == 0 else {}), "captured_at": receipt["finished_at"]}}


def evaluate_completion(report, contract, root, receipt_root, context, declared_gate):
    failures, resolved = [], []
    try:
        contract = behavior.validate(contract)
        require(root is not None, "independently supplied project root required")
        root = Path(root).resolve()
        base = capture.receipt_directory(root, contract["task_id"])
        require(receipt_root is None or Path(receipt_root).resolve() == base, "receipt root differs from designated task workspace")
        context = {} if context is None else context
        require(isinstance(context, dict), "delivery context must be an object")
        require(type(report.get("schema_version")) is int and report["schema_version"] == 3, "retained task requires completion schema 3; legacy downgrade rejected")
        require(report.get("task_id") == contract["task_id"] and report.get("contract_sha256") == behavior.digest(contract), "report task/contract binding mismatch")
        require(behavior._gate.valid_risk_tier(report.get("risk_tier")) and report["risk_tier"] >= contract["risk_tier"], "report lowered retained risk floor")
        rc, commit = capture.local_workspace.run_git(root, "rev-parse", "HEAD")
        if report.get("commit"):
            require(rc == 0 and report["commit"] == commit, "report target commit differs from intended delivery HEAD")
        if str(report.get("status", "")).lower() != "done":
            provisional = copy.deepcopy(report)
            provisional["schema_version"] = 2
            result = declared_gate(provisional)
            result.update(schema_version=3, receipt_verified=False, task_contract_checked=True, receipt_resolution=[])
            return result
        criteria = report.get("acceptance_criteria")
        require(isinstance(criteria, list), "report criteria must be an array")
        require(all(isinstance(c, dict) and behavior.text(c.get("id")) and type(c.get("met")) is bool and type(c.get("required")) is bool for c in criteria), "invalid report criterion")
        current = {c.get("id"): c for c in criteria if isinstance(c, dict) and behavior.text(c.get("id"))}
        require(not set(current) - {c["id"] for c in contract["acceptance_criteria"]}, "report invented an unaccepted criterion")
        for row in contract["acceptance_criteria"]:
            if row["required"]:
                actual = current.get(row["id"], {})
                require(all(actual.get(k) == v for k, v in row.items()), "required criterion changed/removed: " + row["id"])
        obligations = {e["id"]: e for e in contract["evidence_requirements"]}
        evidence = report.get("evidence")
        require(isinstance(evidence, list), "report evidence must be an array")
        derived = copy.deepcopy(report)
        derived["schema_version"] = 2
        derived["evidence"] = []
        coverage = set()
        qualified_ids = set()
        receipt_links = {}
        for item in evidence:
            require(isinstance(item, dict), "invalid evidence entry")
            entry = copy.deepcopy(item)
            obligation = obligations.get(entry.get("requirement_id"))
            require(obligation is not None, "unknown evidence requirement")
            try:
                receipt = read_receipt(base, entry.get("receipt_ref"))
                verified = validate(receipt, entry, contract, obligation, root, context)
                if verified["qualified"]:
                    coverage.add(obligation["id"])
                    qualified_ids.add(entry["id"])
                    receipt_links[entry["id"]] = receipt["criterion_ids"]
                    entry["provenance"] = verified["provenance"]
                else:
                    entry["result"] = "unverified"
                resolved.append({"id": entry.get("id"), "qualified": verified["qualified"], "origin": receipt["origin"], "tested_commit": verified.get("tested_commit")})
            except (ValueError, OSError, TypeError, RuntimeError, capture.zipfile.BadZipFile) as exc:
                entry["result"] = "unverified"
                resolved.append({"id": entry.get("id"), "qualified": False, "error": str(exc)})
                if obligation["required"]:
                    failures.append("required receipt invalid: " + obligation["id"] + ": " + str(exc))
                else:
                    entry.setdefault("justification", item.get("justification"))
            derived["evidence"].append(entry)
        for obligation in obligations.values():
            if obligation["required"] and obligation["id"] not in coverage:
                failures.append("required obligation lacks a qualifying receipt: " + obligation["id"])
        for row in criteria:
            if isinstance(row, dict) and row.get("required") is True:
                require(any(e in qualified_ids and row["id"] in receipt_links[e] for e in row.get("evidence_ids", [])), "criterion lacks linked qualifying receipt: " + str(row.get("id")))
        result = declared_gate(derived, contract["acceptance_criteria"])
        import specialist_handoff
        result["failures"].extend(specialist_handoff.completion_failures(root, contract, context))
        result["failures"].extend(failures)
    except (ValueError, OSError, TypeError, RuntimeError, capture.zipfile.BadZipFile) as exc:
        result = {"gate": "BLOCK", "failures": [str(exc)], "warnings": []}
    result.update({"schema_version": 3, "receipt_resolution": resolved, "task_contract_checked": True,
                   "receipt_verified": not result["failures"] and str(report.get("status", "")).lower() == "done"})
    result["gate"] = "BLOCK" if result["failures"] else ("WARN" if result["warnings"] else "PASS")
    return result


def observe(root: Path, contract: dict, requirement_id: str, observation: dict, context=None, result="pass") -> dict:
    """Persist a supplied actual observation; never synthesize or execute a check."""
    root = root.resolve()
    contract = behavior.validate(contract)
    obligation = next((e for e in contract["evidence_requirements"] if e["id"] == requirement_id), None)
    require(obligation is not None and obligation["origin"] == "manual", "observation needs an accepted manual obligation")
    require(not set(obligation) - capture.REQUIREMENT_FIELDS, "unsupported evidence requirement fields; reconcile before observation")
    require(result in {"pass", "fail"} and isinstance(observation, dict) and all(behavior.text(observation.get(k)) for k in ("description", "method", "environment")), "concrete actual observation required")
    context = {} if context is None else context
    require(isinstance(context, dict), "context must be an object")
    directory = capture.storage(root, contract["task_id"])
    record = capture.envelope(root, contract, obligation)
    paths, excludes = obligation.get("input_paths") or contract["scope"], obligation.get("input_excludes", [])
    manifest = capture.snapshot(root, paths, excludes)
    artifacts = capture.artifact_snapshot(root, obligation.get("artifact_paths", []))
    record.update({"origin": "manual", "result": result, "started_at": capture.now(), "finished_at": capture.now(),
                   "context": context, "observation": observation,
                   "inputs": {"paths": paths, "excludes": excludes, "before": manifest, "after": manifest,
                              "before_sha256": behavior.digest(manifest), "after_sha256": behavior.digest(manifest)},
                   "artifacts": artifacts})
    if result != "pass":
        record["reason"] = observation["description"]
    return capture.persist(directory, record)


def main():
    behavior.configure_output()
    ap = argparse.ArgumentParser(description="Record an actual manual observation; no command is run")
    ap.add_argument("--root", required=True)
    ap.add_argument("--task-contract", required=True)
    ap.add_argument("--requirement", required=True)
    ap.add_argument("--observation", required=True, help="JSON object with description, method and environment; no secrets")
    ap.add_argument("--context", help="explicit relevant runtime/dataset JSON")
    ap.add_argument("--result", choices=("pass", "fail"), default="pass")
    ns = ap.parse_args()
    try:
        result = observe(Path(ns.root), behavior.read(ns.task_contract), ns.requirement,
                         json.loads(ns.observation), json.loads(ns.context) if ns.context else None, ns.result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if ns.result == "pass" else 2
    except (ValueError, OSError, TypeError, RuntimeError):
        print(json.dumps({"gate": "BLOCK", "error": "invalid or inaccessible manual observation context"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
