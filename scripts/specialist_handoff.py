#!/usr/bin/env python3
"""S2: retain scoped specialist assignments and independently gate Head acceptance."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import behavior_contract as behavior
import evidence_capture as capture
import receipt_validation as receipts
import specialist_manager as manager


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def fields(value, allowed, required):
    require(isinstance(value, dict) and not set(value) - set(allowed) and set(required) <= set(value), "unsupported/missing handoff fields")


def paths(value, nonempty=False):
    require(behavior.strings(value, nonempty) and len(set(value)) == len(value), "invalid/duplicate handoff paths")
    for p in value:
        require(capture.relative(p) == p and p != ".git" and not p.startswith(".git/"), "unsafe handoff scope")


def covered(path, scopes):
    return any(s == "." or path == s or path.startswith(s + "/") for s in scopes)


def identity(value, kind):
    require(value.get("format") == kind and type(value.get("schema_version")) is int and value["schema_version"] == 1, "unsupported handoff format/version")
    require(all(behavior.text(value.get(k)) for k in ("task_id", "assignment_id", "specialist_id", "stage")), "handoff identity required")


def validate_assignment(value, contract):
    contract = behavior.validate(contract)
    base = {"format", "schema_version", "task_id", "assignment_id", "specialist_id", "stage", "contract_sha256",
            "criterion_ids", "scope", "settled_decisions", "protected_invariants", "authorized_actions", "evidence_requirement_ids", "platform"}
    fields(value, base | {"shared_contracts", "input_excludes", "completion_binding"}, base)
    identity(value, "vibe-specialist-assignment")
    require(value["task_id"] == contract["task_id"] and value["contract_sha256"] == behavior.digest(contract), "assignment changed retained task contract")
    entry = next((e for e in manager.registry()["specialists"] if e["id"] == value["specialist_id"]), None)
    require(entry is not None and value["stage"] in entry["stages"], "specialist is not active in assigned stage")
    paths(value["scope"], True)
    paths(value.get("input_excludes", []))
    require(all(covered(p, contract["scope"]) for p in value["scope"]), "assignment exceeds retained task scope")
    criteria = {c["id"]: c for c in contract["acceptance_criteria"]}
    obligations = {e["id"]: e for e in contract["evidence_requirements"]}
    require(behavior.strings(value["criterion_ids"], True) and len(set(value["criterion_ids"])) == len(value["criterion_ids"]) and not set(value["criterion_ids"]) - criteria.keys(), "assignment has unknown/duplicate criterion links")
    require(behavior.strings(value["evidence_requirement_ids"]) and len(set(value["evidence_requirement_ids"])) == len(value["evidence_requirement_ids"]) and not set(value["evidence_requirement_ids"]) - obligations.keys(), "assignment has unknown evidence obligations")
    require(all(set(obligations[e]["criterion_ids"]) & set(value["criterion_ids"]) for e in value["evidence_requirement_ids"]), "assignment evidence is unrelated to its criteria")
    for k in ("settled_decisions", "protected_invariants", "authorized_actions"):
        require(behavior.strings(value[k]) and len(set(value[k])) == len(value[k]), "invalid assignment constraints")
    inherited = {i for c in value["criterion_ids"] for i in criteria[c].get("behavior", {}).get("protected_invariants", [])}
    require(inherited <= set(value["protected_invariants"]), "assignment lost retained protected invariant")
    require(isinstance(value["platform"], dict) and all(behavior.text(value["platform"].get(k)) for k in ("stack", "runtime")), "actual assignment stack/runtime required")
    shared = value.get("shared_contracts", [])
    require(isinstance(shared, list), "shared contracts must be an array")
    ids = []
    for row in shared:
        fields(row, {"id", "description"}, {"id", "description"})
        require(behavior.text(row["id"]) and behavior.text(row["description"]), "concrete shared contract required")
        ids.append(row["id"])
    require(len(set(ids)) == len(ids), "duplicate shared contract")
    require(value.get("completion_binding", "stage-handoff") in ("stage-handoff", "current-delivery"), "invalid stage acceptance lifetime")
    behavior.digest(value)
    return entry


def directory(root, task_id, assignment_id=None):
    root = root.resolve()
    base = capture.local_workspace.project_workspace(root) / "state" / "specialist-handoffs" / hashlib.sha256(task_id.encode()).hexdigest()[:16]
    require(not base.is_relative_to(root), "handoff records must stay outside product source")
    if assignment_id is not None:
        base /= hashlib.sha256(assignment_id.encode()).hexdigest()[:16]
    return capture.checked_path(capture.local_workspace.workspace_home(), base)


def git_names(root, *args):
    # Use fixed read-only Git operations; never execute command text from a return.
    with tempfile.TemporaryFile() as output:
        result = subprocess.run(["git", *args], cwd=root, stdout=output, stderr=subprocess.DEVNULL, timeout=30)
        require(result.returncode == 0 and output.tell() <= 8 * 1024 * 1024, "Git surface observation unavailable/oversized")
        output.seek(0)
        names = [p for p in output.read().decode("utf-8").split("\0") if p]
    paths(names)
    require(len(names) <= capture.MAX_FILES, "surface observation path limit exceeded")
    return names


def observation(root, assignment, commit, prior=None):
    names = set(git_names(root, "diff", "--no-ext-diff", "--no-textconv", "--no-renames", "--name-only", "-z", commit, "--"))
    names.update(git_names(root, "ls-files", "--others", "--exclude-standard", "-z"))
    names.update((prior or {}).keys())
    rows = scope_snapshot(root, assignment)
    names.difference_update(r["path"] for r in rows)
    if names:
        rows += capture.snapshot(root, sorted(names), [], require_file=False)
    result = {r["path"]: r for r in rows if not r.get("directory")}
    require(len(result) <= capture.MAX_FILES, "surface observation manifest limit exceeded")
    return result


def scope_snapshot(root, assignment):
    return capture.snapshot(root, assignment["scope"], [*assignment.get("input_excludes", []), ".git"], require_file=False)


def control_fingerprint(entry):
    return behavior.digest({"authority": hashlib.sha256((manager.ROOT / "references/specialist-authority.md").read_bytes()).hexdigest(),
                            "adapter": manager.PACKAGE_ADAPTER, "permissions": manager.registry()["permissions"],
                            "domain": {k: entry.get(k) for k in ("mode", "capability", "assignment", "stages", "primary_stages")}})


def markers(operation, remove=False):
    state = Path(operation["specialist_state"])
    key = behavior.digest({"root": operation["root"], "assignment": operation["assignment"]})[:16]
    for name in ("vibe-coding-skill", operation["assignment"]["specialist_id"]):
        path = state / "active-assignments" / name / (key + ".json")
        require(path.resolve().is_relative_to(state.resolve()), "active assignment marker escapes state")
        if remove:
            path.unlink(missing_ok=True)
        else:
            manager.write_record(path, {"task_id": operation["assignment"]["task_id"], "assignment_id": operation["assignment"]["assignment_id"], "root": operation["root"]})


def assign(root, contract, specification, skills_dir, state):
    root, skills_dir, state = root.resolve(), skills_dir.resolve(), state.resolve()
    require(not any(p.is_relative_to(root) for p in (skills_dir, state)) and not skills_dir.is_relative_to(state) and not state.is_relative_to(skills_dir), "host skills/state must remain separate and outside product")
    assignment = copy.deepcopy(specification)
    assignment.setdefault("completion_binding", "current-delivery" if assignment.get("stage") in ("verify", "review", "ship") else "stage-handoff")
    entry = validate_assignment(assignment, contract)
    preflight = manager.run("prepare", skills_dir, state, [{**entry, "active_in_stage": True}], False)
    require(preflight["gate"] in ("PASS", "WARN"), "current Head and accepted specialist compatibility required before assignment")
    installed = next(s for s in preflight["skills"] if s["id"] == entry["id"])
    require(installed.get("compatibility", {}).get("status") == "accepted", "assigned specialist lacks Head instruction compatibility")
    base = directory(root, contract["task_id"], assignment["assignment_id"])
    require(not (base / "operation.json").exists(), "assignment ID already retained; create a new stage assignment")
    rc, commit = capture.local_workspace.run_git(root, "rev-parse", "HEAD")
    require(rc == 0 and re.fullmatch(r"[0-9a-f]{40}", commit), "assignment needs an existing Git baseline commit")
    with manager.installation_lock(skills_dir):
        packet = manager.compatibility_packet(entry, skills_dir, state, installed)
        require(packet["binding_sha256"] == installed["compatibility"]["binding_sha256"], "specialist changed during assignment preparation")
        operation = {"assignment": assignment, "contract": behavior.validate(contract), "root": str(root),
                     "skills_dir": str(skills_dir), "specialist_state": str(state), "source": installed["source"],
                     "specialist_files": packet["binding"]["files"], "control_sha256": control_fingerprint(entry),
                     "compatibility_binding_sha256": packet["binding_sha256"], "baseline_commit": commit,
                     "baseline_tracked": git_names(root, "ls-tree", "-r", "--name-only", "-z", commit),
                     "baseline": observation(root, assignment, commit), "created_at": capture.now(), "closed": False}
        base.mkdir(parents=True, exist_ok=True)
        manager.write_record(base / "operation.json", operation)
        markers(operation)
    return {"assignment": assignment, "upstream_revision": operation["source"]["commit"], "head_contract_sha256": operation["source"]["package_policy"], "record_path": str(base / "operation.json"), "accepted": False}


def load_operation(root, contract, assignment_id):
    base = directory(root, contract["task_id"], assignment_id)
    operation = manager.read_local_json(base / "operation.json")
    require(operation["root"] == str(root.resolve()) and operation["contract"] == behavior.validate(contract), "operation belongs to another root/contract")
    require(operation["assignment"]["assignment_id"] == assignment_id, "retained assignment identity mismatch")
    require(type(operation.get("closed")) is bool and re.fullmatch(r"[0-9a-f]{40}", str(operation.get("baseline_commit"))), "invalid retained operation baseline")
    validate_assignment(operation["assignment"], contract)
    return base, operation


def validate_return(returned, operation):
    keys = {"format", "schema_version", "task_id", "assignment_id", "specialist_id", "stage", "contract_sha256", "upstream_revision", "head_contract_sha256",
            "changed_surfaces", "decisions", "invariants", "evidence_ids", "findings", "unperformed_checks", "conflicts", "next_action"}
    fields(returned, keys, keys)
    identity(returned, "vibe-specialist-return")
    assignment = operation["assignment"]
    for k in ("task_id", "assignment_id", "specialist_id", "stage", "contract_sha256"):
        require(returned[k] == assignment[k], "return binding mismatch: " + k)
    require(returned["upstream_revision"] == operation["source"]["commit"] and returned["head_contract_sha256"] == operation["source"]["package_policy"], "return changed assigned specialist provenance")
    require(behavior.text(returned["next_action"]), "return needs a next action")
    for k in ("evidence_ids", "unperformed_checks", "conflicts"):
        require(behavior.strings(returned[k]) and len(set(returned[k])) == len(returned[k]), "invalid return " + k)
    for k in ("changed_surfaces", "decisions", "invariants", "findings"):
        require(isinstance(returned[k], list), "invalid return " + k)
    surfaces = {}
    for row in returned["changed_surfaces"]:
        fields(row, {"path", "action", "previous_path"}, {"path", "action"})
        paths([row["path"]], True)
        require(row["path"] != "." and row["action"] in ("add", "modify", "delete", "rename"), "invalid changed surface")
        if row["action"] == "rename":
            paths([row.get("previous_path")], True)
            require(row["previous_path"] != row["path"] and row["previous_path"] != ".", "invalid rename")
            changes = [(row["previous_path"], "delete"), (row["path"], "add")]
        else:
            require("previous_path" not in row, "previous_path belongs to rename only")
            changes = [(row["path"], row["action"])]
        for path, action in changes:
            require(path not in surfaces, "duplicate returned surface")
            surfaces[path] = action
    contracts = {c["id"] for c in assignment.get("shared_contracts", [])}
    linked = set()
    for row in returned["decisions"]:
        fields(row, {"description", "criterion_ids", "contract_refs", "rationale"}, {"description", "criterion_ids", "contract_refs", "rationale"})
        require(behavior.text(row["description"]) and behavior.text(row["rationale"]), "concrete domain decision required")
        require(behavior.strings(row["criterion_ids"], True) and set(row["criterion_ids"]) <= set(assignment["criterion_ids"]), "decision has unrelated criteria")
        require(behavior.strings(row["contract_refs"]) and set(row["contract_refs"]) <= contracts, "unknown producer/consumer contract")
        linked.update(row["contract_refs"])
    require(contracts <= linked, "return omitted assigned shared contract decisions")
    invariant_ids = set()
    for row in returned["invariants"]:
        fields(row, {"description", "status", "explanation", "evidence_ids"}, {"description", "status", "explanation", "evidence_ids"})
        require(row["description"] in assignment["protected_invariants"] and row["description"] not in invariant_ids, "unknown/duplicate invariant")
        invariant_ids.add(row["description"])
        require(row["status"] in ("preserved", "violated", "unverified") and behavior.text(row["explanation"]) and behavior.strings(row["evidence_ids"]), "invalid invariant observation")
    require(invariant_ids == set(assignment["protected_invariants"]), "return omitted protected invariants")
    ids = set()
    for row in returned["findings"]:
        fields(row, {"id", "required", "description", "status", "resolution_evidence_ids"}, {"id", "required", "description", "status"})
        require(behavior.text(row["id"]) and row["id"] not in ids and type(row["required"]) is bool and behavior.text(row["description"]), "invalid/duplicate finding")
        ids.add(row["id"])
        require(row["status"] in ("open", "resolved") and behavior.strings(row.get("resolution_evidence_ids", [])), "invalid finding resolution")
    return surfaces


def evaluate(root, contract, operation, returned, evidence, decision=None, context=None, current=True):
    failures, qualified = [], set()
    assignment = operation["assignment"]
    try:
        declared = validate_return(returned, operation)
        entry = validate_assignment(assignment, contract)
        require(control_fingerprint(entry) == operation["control_sha256"], "Head/domain controls changed; reassess assignment")
        if not operation["closed"]:
            require(manager.installed_hashes(Path(operation["skills_dir"]) / entry["skill_name"]) == operation["specialist_files"], "assigned specialist instructions changed during operation")
        context = {} if context is None else context
        require(isinstance(context, dict) and isinstance(evidence, list), "independent evidence/context required")
        obligations = {e["id"]: e for e in contract["evidence_requirements"]}
        ids, coverage = set(), set()
        for row in evidence:
            require(isinstance(row, dict) and behavior.text(row.get("id")) and row["id"] not in ids, "invalid/duplicate evidence catalog")
            ids.add(row["id"])
            if row["id"] not in returned["evidence_ids"]:
                continue
            obligation = obligations.get(row.get("requirement_id"))
            require(obligation is not None and obligation["id"] in assignment["evidence_requirement_ids"], "return references an unassigned evidence obligation")
            try:
                receipt = receipts.read_receipt(capture.receipt_directory(root, contract["task_id"]), row.get("receipt_ref"))
                if current:
                    verified = receipts.validate(receipt, row, contract, obligation, root, context or {})
                else:
                    require(behavior.digest(receipt) == row.get("receipt_sha256"), "historical receipt changed")
                    verified = {"qualified": row["id"] in operation["accepted_qualified_ids"]}
                if verified["qualified"]:
                    qualified.add(row["id"])
                    coverage.add(obligation["id"])
            except (ValueError, OSError, TypeError, RuntimeError, capture.zipfile.BadZipFile):
                if obligation["required"]:
                    failures.append("required receipt invalid: " + obligation["id"])
        require(set(returned["evidence_ids"]) <= ids, "return references missing evidence")
        for eid in assignment["evidence_requirement_ids"]:
            if obligations[eid]["required"] and eid not in coverage:
                failures.append("assigned required evidence lacks a qualifying receipt: " + eid)
        for row in returned["invariants"]:
            if row["status"] != "preserved" or not row["evidence_ids"] or not set(row["evidence_ids"]) <= qualified:
                failures.append("protected invariant lacks preserved qualifying evidence: " + row["description"])
        unresolved = []
        for row in returned["findings"]:
            refs = row.get("resolution_evidence_ids", [])
            if row["required"] and (row["status"] != "resolved" or not refs or not set(refs) <= qualified):
                unresolved.append(row["id"])
        if unresolved or returned["conflicts"]:
            failures.append("unresolved required findings or conflicts")
        observed = observation(root, assignment, operation["baseline_commit"], operation["baseline"]) if current and not operation["closed"] else operation["accepted_observation"]
        actual = {}
        for p in operation["baseline"].keys() | observed.keys():
            before = operation["baseline"].get(p)
            after = observed.get(p, {"path": p, "missing": True})
            if before == after or (before is None and after.get("missing")):
                continue
            existed = not before.get("missing", False) if before else p in operation["baseline_tracked"]
            actual[p] = "delete" if after.get("missing") else "modify" if existed else "add"
        require(declared == actual, "returned changed surfaces differ from observed project changes")
        for p in actual:
            require(covered(p, contract["scope"]), "actual change exceeds retained task scope: " + p)
        inputs = {r["path"]: r for r in scope_snapshot(root, assignment)} if current else operation["accepted_inputs"]
        if current and actual:
            inputs.update({r["path"]: r for r in capture.snapshot(root, sorted(actual), [], require_file=False)})
        delivery = behavior.digest({"assignment": assignment, "inputs": inputs, "context": context or {}, "evidence": evidence})
        outside = sorted(p for p in actual if not covered(p, assignment["scope"]))
        review = {"return_sha256": behavior.digest(returned), "delivery_sha256": delivery, "actual_changes": actual,
                  "scope_reconciliation_paths": outside, "unresolved_required_finding_ids": unresolved, "qualified_evidence_ids": sorted(qualified)}
        if decision is not None:
            base = {"format", "schema_version", "task_id", "assignment_id", "contract_sha256", "return_sha256", "upstream_revision", "head_contract_sha256",
                    "delivery_sha256", "decision", "assessed_by", "assessed_at", "reason", "unresolved_required_finding_ids", "scope_reconciliations", "contract_decisions"}
            fields(decision, base, base)
            require(decision["format"] == "vibe-head-acceptance" and type(decision["schema_version"]) is int and decision["schema_version"] == 1, "unsupported Head acceptance format")
            for k in ("task_id", "assignment_id", "contract_sha256", "upstream_revision", "head_contract_sha256"):
                require(decision[k] == returned[k], "Head decision binding mismatch: " + k)
            require(decision["return_sha256"] == review["return_sha256"] and decision["delivery_sha256"] == delivery, "Head decision is stale/misbound")
            require(decision["decision"] in ("accepted", "changes-required", "blocked") and all(behavior.text(decision[k]) for k in ("assessed_by", "reason")), "concrete Head decision required")
            receipts.timestamp(decision["assessed_at"])
            require(decision["unresolved_required_finding_ids"] == unresolved, "Head decision hid required findings")
            reconciled = {}
            require(isinstance(decision["scope_reconciliations"], list), "scope reconciliation must be an array")
            for row in decision["scope_reconciliations"]:
                fields(row, {"path", "reason"}, {"path", "reason"})
                require(row["path"] in outside and row["path"] not in reconciled and behavior.text(row["reason"]), "invalid Head scope reconciliation")
                reconciled[row["path"]] = row["reason"]
            shared = {r["id"] for r in assignment.get("shared_contracts", [])}
            decisions = decision["contract_decisions"]
            require(isinstance(decisions, list), "shared contract decisions must be an array")
            seen = set()
            for row in decisions:
                fields(row, {"id", "status", "reason"}, {"id", "status", "reason"})
                require(row["id"] in shared and row["id"] not in seen and row["status"] in ("compatible", "blocked") and behavior.text(row["reason"]), "invalid shared contract assessment")
                seen.add(row["id"])
            if decision["decision"] == "accepted":
                require(set(reconciled) == set(outside) and seen == shared and all(r["status"] == "compatible" for r in decisions), "Head acceptance omitted scope/producer-consumer reconciliation")
            else:
                failures.append("Head requires changes or blocks acceptance")
        return {"gate": "BLOCK" if failures else "PASS" if decision is not None else "UNVERIFIED", "accepted": not failures and decision is not None,
                "failures": failures, "review": review, "observation": observed, "inputs": inputs}
    except (ValueError, OSError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as exc:
        return {"gate": "BLOCK", "accepted": False, "failures": [str(exc)]}


def review(root, contract, assignment_id, returned, evidence, decision=None, context=None):
    root = root.resolve()
    base, operation = load_operation(root, contract, assignment_id)
    validate_return(returned, operation)
    sha = behavior.digest(returned)
    require(not operation["closed"] or operation.get("latest_return") == sha, "closed assignment cannot silently change its return")
    history = sorted((base / "returns").glob("*.json"))
    require(len(history) < 1000, "return history limit exceeded")
    current_findings = {f["id"]: f for f in returned["findings"]}
    for path in history:
        old = manager.read_local_json(path)
        require(path.stem == behavior.digest(old)[:16], "retained return history changed")
        for f in old["findings"]:
            if f["required"]:
                replacement = current_findings.get(f["id"], {})
                require(replacement.get("required") is True and replacement.get("description") == f["description"], "required finding removed/weakened from retained history")
    result = evaluate(root, contract, operation, returned, evidence, decision, context)
    manager.write_record(base / "returns" / (sha[:16] + ".json"), returned)
    manager.write_record(base / "review.json", {"return_sha256": sha, "evidence": evidence, "context": context or {}, "decision": decision,
                                               "result": {k: v for k, v in result.items() if k not in ("observation", "inputs")}})
    operation["latest_return"] = sha
    if result["accepted"]:
        operation.update(closed=True, accepted_observation=result["observation"], accepted_inputs=result["inputs"],
                         accepted_qualified_ids=result["review"]["qualified_evidence_ids"])
        with manager.installation_lock(Path(operation["skills_dir"])):
            manager.write_record(base / "operation.json", operation)
            markers(operation, remove=True)
    else:
        manager.write_record(base / "operation.json", operation)
    return {k: v for k, v in result.items() if k not in ("observation", "inputs")}


def completion_failures(root, contract, context=None):
    """A declared Done cannot bypass retained required specialist decisions."""
    base = directory(root, contract["task_id"])
    operations = sorted(base.glob("*/operation.json"))
    require(len(operations) <= 1000, "assignment ledger limit exceeded")
    expected = contract.get("specialist_assignment_ids", [])
    require(behavior.strings(expected) and len(set(expected)) == len(expected), "invalid retained specialist assignment IDs")
    seen, failures = set(), []
    for path in operations:
        operation = manager.read_local_json(path)
        assignment_id = operation["assignment"]["assignment_id"]
        seen.add(assignment_id)
        folder, operation = load_operation(root, contract, assignment_id)
        record = manager.read_local_json(folder / "review.json")
        returned = manager.read_local_json(folder / "returns" / (record["return_sha256"][:16] + ".json"))
        require(behavior.digest(returned) == record["return_sha256"] == operation.get("latest_return"), "retained specialist return digest mismatch")
        if not record["result"].get("accepted") or not operation["closed"]:
            failures.append("specialist assignment lacks Head acceptance: " + assignment_id)
            continue
        current = operation["assignment"]["completion_binding"] == "current-delivery"
        result = evaluate(root, contract, operation, returned, record["evidence"], record["decision"], context if current else record["context"], current=current)
        if not result["accepted"]:
            failures.append("specialist acceptance stale/invalid: " + assignment_id)
    failures.extend("required specialist assignment missing: " + aid for aid in set(expected) - seen)
    return failures


def main():
    behavior.configure_output()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("assign", "review", "close"))
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--task-contract", required=True)
    ap.add_argument("--assignment", help="Head-owned assignment JSON for assign")
    ap.add_argument("--assignment-id")
    ap.add_argument("--return", dest="returned")
    ap.add_argument("--evidence", help="independent Head receipt catalog JSON array")
    ap.add_argument("--decision", help="separate Head acceptance JSON")
    ap.add_argument("--context", help="independent delivery runtime/dataset JSON object")
    ap.add_argument("--reason", help="Head reason for abandoning an operation; never completion")
    ap.add_argument("--skills-dir", type=Path, default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "skills")
    ap.add_argument("--state-dir", type=Path, default=capture.local_workspace.workspace_home() / "specialists")
    ns = ap.parse_args()
    try:
        root, contract = ns.root.resolve(), behavior.read(ns.task_contract)
        read = lambda path: json.loads(Path(path).read_text(encoding="utf-8"))
        if ns.mode == "assign":
            require(ns.assignment is not None, "assign requires a Head assignment")
            result = assign(root, contract, read(ns.assignment), ns.skills_dir, ns.state_dir)
        elif ns.mode == "review":
            require(behavior.text(ns.assignment_id) and ns.returned is not None and ns.evidence is not None, "review requires retained assignment, return and evidence")
            result = review(root, contract, ns.assignment_id, read(ns.returned), read(ns.evidence), read(ns.decision) if ns.decision else None, read(ns.context) if ns.context else None)
        else:
            require(behavior.text(ns.assignment_id) and behavior.text(ns.reason), "close requires assignment ID and concrete Head reason")
            base, operation = load_operation(root, contract, ns.assignment_id)
            require(not operation["closed"], "operation already closed")
            with manager.installation_lock(Path(operation["skills_dir"])):
                operation.update(closed=True, abandoned_reason=ns.reason)
                manager.write_record(base / "operation.json", operation)
                markers(operation, remove=True)
            result = {"gate": "UNVERIFIED", "accepted": False, "reason": "assignment abandoned; task completion remains unverified"}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 2 if result.get("gate") in ("BLOCK", "UNVERIFIED") else 0
    except (ValueError, OSError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"gate": "BLOCK", "accepted": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
