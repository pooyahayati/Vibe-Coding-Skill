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
from datetime import datetime, timezone

import behavior_contract as behavior
import evidence_capture as capture
import receipt_validation as receipts
import specialist_manager as manager
import assignment_runtime as runtime


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
                            "domain": manager.domain_contract(entry)})


def markers(operation, remove=False):
    state = Path(operation["specialist_state"])
    key = behavior.digest({"root": operation["root"], "assignment": operation["assignment"]})[:16]
    for name in ("vibe-coding-skill", operation["assignment"]["specialist_id"]):
        path = state / "active-assignments" / name / (key + ".json")
        require(path.resolve().is_relative_to(state.resolve()), "active assignment marker escapes state")
        if remove:
            path.unlink(missing_ok=True)
        else:
            value = {"task_id": operation["assignment"]["task_id"], "assignment_id": operation["assignment"]["assignment_id"], "root": operation["root"]}
            if operation.get("runtime_binding"):
                value.update(runtime_binding=operation["runtime_binding"], operation_path=str(directory(Path(operation["root"]), value["task_id"], value["assignment_id"]) / "operation.json"))
            manager.write_record(path, value)


def retain_runtime(operation, path):
    operation.pop("runtime_binding", None)
    operation.pop("runtime_limitation", None)
    try:
        operation["runtime_binding"] = runtime.retain(operation, path)
    except runtime.UnsupportedBinding as exc:
        operation["runtime_limitation"] = str(exc)
    return operation


def assignment_inputs(root, contract, specification, skills_dir, state):
    root, skills_dir, state = root.resolve(), skills_dir.resolve(), state.resolve()
    require(not any(p.is_relative_to(root) for p in (skills_dir, state)) and not skills_dir.is_relative_to(state) and not state.is_relative_to(skills_dir), "host skills/state must remain separate and outside product")
    assignment = copy.deepcopy(specification)
    assignment.setdefault("completion_binding", "current-delivery" if assignment.get("stage") in ("verify", "review", "ship") else "stage-handoff")
    entry = validate_assignment(assignment, contract)
    require(not (directory(root, contract["task_id"], assignment["assignment_id"]) / "operation.json").exists(),
            "assignment ID already retained; create a new stage assignment")
    return root, skills_dir, state, assignment, entry


def preparation_path(root, assignment, state):
    key = behavior.digest({"root": str(root), "task_id": assignment["task_id"], "assignment_id": assignment["assignment_id"]})
    return capture.checked_path(state, state / "preparations" / (key + ".json"))


def preparation_binding(root, contract, assignment, entry, skills_dir, state):
    """Local validity only; never claims a new upstream observation."""
    rows = []
    for selected in (manager.registry()["head"], entry):
        target = skills_dir / selected["skill_name"]
        record = manager.read_local_json(state / (selected["id"] + ".json"))
        files = manager.installed_hashes(target)
        require(record.get("status") == "current" and bool(files) and record.get("files") == files
                and record.get("installation") == str(target)
                and record.get("source", {}).get("repository") == selected["repository"]
                and record["source"].get("skill_path") == selected["skill_path"], "prepared installation changed")
        rows.append(record)
    compatible = manager.compatibility(entry, skills_dir, state, rows[-1])
    require(compatible.get("status") == "accepted", "prepared compatibility no longer accepted")
    rows[-1] = {**rows[-1], "compatibility": compatible}
    rc, commit = capture.local_workspace.run_git(root, "rev-parse", "HEAD")
    require(rc == 0 and re.fullmatch(r"[0-9a-f]{40}", commit), "assignment needs an existing Git baseline commit")
    binding = {"root": str(root), "contract_sha256": behavior.digest(contract), "assignment": assignment,
               "skills_dir": str(skills_dir), "state": str(state), "installations": rows,
               "assessment": manager.read_local_json(Path(compatible["assessment_path"])),
               "registry": manager.registry(), "controls": control_fingerprint(entry),
               "implementation": {p: hashlib.sha256((manager.ROOT / "scripts" / p).read_bytes()).hexdigest()
                                  for p in ("specialist_manager.py", "specialist_handoff.py")},
               "commit": commit, "inputs": scope_snapshot(root, assignment)}
    return behavior.digest(binding), rows


def prepared_preflight(root, contract, assignment, entry, skills_dir, state):
    path = preparation_path(root, assignment, state)
    if not path.exists() or manager.inventory_due(state):
        return None
    try:
        prepared = manager.read_local_json(path)
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(prepared["checked_at"])).total_seconds()
        if prepared.get("schema_version") != 1 or not 0 <= age < manager.registry()["policy"]["inventory_interval_hours"] * 3600:
            return None
        binding, rows = preparation_binding(root, contract, assignment, entry, skills_dir, state)
        if prepared["binding_sha256"] != binding:
            return None
        return {"gate": "PASS", "skills": rows,
                "preflight_reuse": {"reused": True, "upstream_checked": False, "checked_at": prepared["checked_at"],
                                    "basis": "same prepared assignment; local inputs and compatibility revalidated"}}
    except (OSError, ValueError, KeyError, TypeError):
        return None  # Invalid local evidence requires the normal fresh preflight.


def prepare(root, contract, specification, skills_dir, state):
    root, skills_dir, state, assignment, entry = assignment_inputs(root, contract, specification, skills_dir, state)
    path = preparation_path(root, assignment, state)
    # A failed fresh attempt must not resurrect an earlier successful check.
    with manager.installation_lock(skills_dir):
        path.unlink(missing_ok=True)
    result = manager.run("prepare", skills_dir, state, [{**entry, "active_in_stage": True}], False)
    result["preflight_reuse"] = {"reused": False, "upstream_checked": True}
    if result["gate"] == "PASS":
        with manager.installation_lock(skills_dir):
            binding, rows = preparation_binding(root, contract, assignment, entry, skills_dir, state)
            require(all(next(s for s in result["skills"] if s["id"] == row["id"])["source"] == row["source"] for row in rows),
                    "prepared source changed during preflight")
            manager.write_record(path, {"schema_version": 1, "binding_sha256": binding, "checked_at": capture.now()})
        result["preparation_path"] = str(path)
    return result


def assign(root, contract, specification, skills_dir, state):
    root, skills_dir, state, assignment, entry = assignment_inputs(root, contract, specification, skills_dir, state)
    with manager.installation_lock(skills_dir):
        preflight = prepared_preflight(root, contract, assignment, entry, skills_dir, state)
    reused = preflight is not None
    if not reused:
        with manager.installation_lock(skills_dir):
            preparation_path(root, assignment, state).unlink(missing_ok=True)
        preflight = manager.run("prepare", skills_dir, state, [{**entry, "active_in_stage": True}], False)
    require(preflight["gate"] in ("PASS", "WARN"), "current Head and accepted specialist compatibility required before assignment")
    installed = next(s for s in preflight["skills"] if s["id"] == entry["id"])
    require(installed.get("compatibility", {}).get("status") == "accepted", "assigned specialist lacks Head instruction compatibility")
    capture.local_workspace.project_workspace(root, create=True)
    base = directory(root, contract["task_id"], assignment["assignment_id"])
    require(not (base / "operation.json").exists(), "assignment ID already retained; create a new stage assignment")
    rc, commit = capture.local_workspace.run_git(root, "rev-parse", "HEAD")
    require(rc == 0 and re.fullmatch(r"[0-9a-f]{40}", commit), "assignment needs an existing Git baseline commit")
    with manager.installation_lock(skills_dir):
        require(not reused or prepared_preflight(root, contract, assignment, entry, skills_dir, state) is not None,
                "prepared inputs changed during assignment; prepare again")
        packet = manager.compatibility_packet(entry, skills_dir, state, installed)
        require(packet["binding_sha256"] == installed["compatibility"]["binding_sha256"], "specialist changed during assignment preparation")
        operation = {"assignment": assignment, "contract": behavior.validate(contract), "root": str(root),
                     "skills_dir": str(skills_dir), "specialist_state": str(state), "source": installed["source"],
                     "specialist_files": packet["binding"]["files"], "control_sha256": control_fingerprint(entry),
                     "compatibility_binding_sha256": packet["binding_sha256"], "baseline_commit": commit,
                     "baseline_tracked": git_names(root, "ls-tree", "-r", "--name-only", "-z", commit),
                     "baseline": observation(root, assignment, commit), "created_at": capture.now(), "closed": False}
        base.mkdir(parents=True, exist_ok=True)
        retain_runtime(operation, base / "operation.json")
        # Publish guards first: an interrupted binding may not unlock replacement.
        markers(operation)
        manager.write_record(base / "operation.json", operation)
        preparation_path(root, assignment, state).unlink(missing_ok=True)
    return {"assignment": assignment, "upstream_revision": operation["source"]["commit"], "head_contract_sha256": operation["source"]["package_policy"], "record_path": str(base / "operation.json"), "accepted": False,
            "preflight_reuse": preflight.get("preflight_reuse", {"reused": False, "upstream_checked": True}),
            "runtime_binding": operation.get("runtime_binding"), "runtime_limitation": operation.get("runtime_limitation")}


def load_operation(root, contract, assignment_id, allow_transition=False):
    base = directory(root, contract["task_id"], assignment_id)
    operation = manager.read_local_json(base / "operation.json")
    require(operation["root"] == str(root.resolve()) and operation["contract"] == behavior.validate(contract), "operation belongs to another root/contract")
    require(operation["assignment"]["assignment_id"] == assignment_id, "retained assignment identity mismatch")
    require(type(operation.get("closed")) is bool and re.fullmatch(r"[0-9a-f]{40}", str(operation.get("baseline_commit"))), "invalid retained operation baseline")
    if operation.get("runtime_binding"):
        runtime.resolve(operation)
        if not operation["closed"] and not allow_transition:
            key = behavior.digest({"root": operation["root"], "assignment": operation["assignment"]})[:16]
            for name in ("vibe-coding-skill", operation["assignment"]["specialist_id"]):
                marker = manager.read_local_json(Path(operation["specialist_state"]) / "active-assignments" / name / (key + ".json"))
                require(marker.get("runtime_binding") == operation["runtime_binding"]
                        and marker.get("operation_path") == str(base / "operation.json"),
                        "incomplete runtime transition; inspect and retry the explicit migration")
    else:
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
        retained = None
        if operation.get("runtime_binding"):
            retained, _ = runtime.resolve(operation)
            if not runtime.is_local(retained):
                return runtime.invoke(operation, "evaluate", returned=returned, evidence=evidence, decision=decision, context=context, current=current)
        declared = validate_return(returned, operation)
        entry = validate_assignment(assignment, contract)
        require(control_fingerprint(entry) == operation["control_sha256"], "Head/domain controls changed; reassess assignment")
        if not operation["closed"]:
            target = retained / "specialist" if retained else Path(operation["skills_dir"]) / entry["skill_name"]
            require(manager.installed_hashes(target) == operation["specialist_files"], "assigned specialist instructions changed during operation")
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
                if "reassessment" in operation:
                    require(receipts.timestamp(receipt.get("started_at")) >= receipts.timestamp(operation["reassessment"]["started_at"]),
                            "receipt predates explicit specialist reassessment")
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
        binding = {"assignment": assignment, "inputs": inputs, "context": context or {}, "evidence": evidence}
        if "reassessment" in operation:
            binding["reassessment"] = operation["reassessment"]
        delivery = behavior.digest(binding)
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
    if operation.get("runtime_binding"):
        retained, _ = runtime.resolve(operation)
        if not runtime.is_local(retained):
            return runtime.invoke(operation, "review", returned=returned, evidence=evidence, decision=decision, context=context)
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


def accepted_record(base, operation):
    record = manager.read_local_json(base / "review.json")
    returned = manager.read_local_json(base / "returns" / (record["return_sha256"][:16] + ".json"))
    require(behavior.digest(returned) == record["return_sha256"] == operation.get("latest_return"), "retained specialist return digest mismatch")
    return record, returned


def reopened_operation(old, contract, assignment, entry):
    skills, state = Path(old["skills_dir"]), Path(old["specialist_state"])
    preflight = manager.run("prepare", skills, state, [{**entry, "active_in_stage": True}], False)
    require(preflight["gate"] in ("PASS", "WARN"), "current compatible specialist required for reopening")
    installed = next(s for s in preflight["skills"] if s["id"] == entry["id"])
    require(installed.get("compatibility", {}).get("status") == "accepted", "specialist compatibility requires Head acceptance")
    packet = manager.compatibility_packet(entry, skills, state, installed)
    require(packet["binding_sha256"] == installed["compatibility"]["binding_sha256"], "specialist changed during reconciliation")
    replacement = {k: v for k, v in old.items() if not k.startswith("accepted_")
                   and k not in ("latest_return", "retirement", "abandoned_reason", "reassessment")}
    replacement.update(assignment=assignment, contract=contract, closed=False, source=installed["source"],
                       specialist_files=packet["binding"]["files"], control_sha256=control_fingerprint(entry),
                       compatibility_binding_sha256=packet["binding_sha256"])
    return replacement


def store_transition(base, old, replacement, archive):
    with manager.installation_lock(Path(old["skills_dir"])):
        require(manager.read_local_json(base / "operation.json") == old, "operation changed during transition; inspect again")
        if not replacement["closed"]:
            entry = validate_assignment(replacement["assignment"], replacement["contract"])
            require(manager.installed_hashes(Path(old["skills_dir"]) / entry["skill_name"]) == replacement["specialist_files"],
                    "specialist changed before reconciliation")
            retain_runtime(replacement, base / "operation.json")
            require(not old.get("runtime_binding") or replacement.get("runtime_binding"),
                    "migration cannot lose verified runtime isolation; reload the managed default Head")
        manager.write_record(base / "revisions" / (behavior.digest(archive)[:16] + ".json"), archive)
        # Guard first; a failed operation write must not expose active instructions.
        if not replacement["closed"]:
            markers(replacement)
        manager.write_record(base / "operation.json", replacement)
        # Same-contract reassessment uses the same marker key: do not remove it.
        if replacement["closed"] or replacement["assignment"] != old["assignment"]:
            markers(old, remove=True)


def reassess(root, contract, assignment_id, reason, migrate=False):
    """Reopen the unchanged assignment explicitly; retain findings and prior review."""
    require(behavior.text(reason), "reassessment requires a concrete Head reason")
    root = root.resolve()
    base, old = load_operation(root, contract, assignment_id, allow_transition=True)
    require(old["closed"] or migrate, "assignment already active; continue its review")
    if old.get("runtime_binding"):
        require(not runtime.is_local(runtime.resolve(old)[0]), "reassessment/migration must run through the current default Head")
    require("retirement" not in old, "retired assignment requires contract reconciliation")
    # When a task snapshot exists, an old supplied contract cannot bypass revision.
    import project_state
    retained = project_state.load_previous(root) or {}
    require(retained.get("task_contract", contract) == contract, "task contract changed; use contract reconciliation")
    entry = validate_assignment(old["assignment"], contract)
    replacement = reopened_operation(old, contract, old["assignment"], entry)
    replacement["reassessment"] = {"started_at": capture.now(), "reason": reason, "previous_operation_sha256": behavior.digest(old)}
    archive = {"operation": old, "reassessment": replacement["reassessment"]}
    if (base / "review.json").exists():
        archive["review"] = manager.read_local_json(base / "review.json")
    store_transition(base, old, replacement, archive)
    return {"gate": "PASS", "accepted": False, "action": "migrated" if migrate else "reassessed", "assignment": replacement["assignment"],
            "upstream_revision": replacement["source"]["commit"], "head_contract_sha256": replacement["source"]["package_policy"],
            "record_path": str(base / "operation.json")}


def resume_assignment(root, contract, assignment_id):
    base, operation = load_operation(root, contract, assignment_id)
    if operation.get("runtime_binding"):
        result = runtime.invoke(operation, "resume")
        result["status"] = "retained"
    else:
        entry = validate_assignment(operation["assignment"], contract)
        require(control_fingerprint(entry) == operation["control_sha256"]
                and manager.installed_hashes(Path(operation["skills_dir"]) / entry["skill_name"]) == operation["specialist_files"],
                "legacy assignment resources changed; explicit reconciliation required")
        result = {"status": "legacy-guarded", "assignment_id": assignment_id,
                  "specialist_skill": str(Path(operation["skills_dir"]) / entry["skill_name"] / "SKILL.md"),
                  "limitation": operation.get("runtime_limitation", "No verified isolated binding; active update guard retained.")}
    result.update(closed=operation["closed"], contract_sha256=behavior.digest(contract), record_path=str(base / "operation.json"))
    required = {}
    history = sorted((base / "returns").glob("*.json"))
    require(len(history) <= 1000, "return history limit exceeded")
    for path in history:
        returned = manager.read_local_json(path)
        require(path.stem == behavior.digest(returned)[:16], "retained return history changed")
        for row in returned["findings"]:
            if row["required"]:
                require(row["id"] not in required or required[row["id"]] == row["description"], "retained required finding meaning changed")
                required[row["id"]] = row["description"]
    result["required_findings"] = [{"id": key, "description": required[key]} for key in sorted(required)]
    result["finding_status_note"] = "Retained obligations, not current resolution claims; inspect and revalidate the latest return and Head review."
    return result


def runtime_context(root):
    """Discover active assignments even without an optional task-state snapshot."""
    home = capture.local_workspace.project_workspace(root) / "state/specialist-handoffs"
    operations = sorted(home.glob("*/*/operation.json"))
    require(len(operations) <= 1000, "assignment ledger limit exceeded")
    result = []
    for path in operations:
        operation = manager.read_local_json(path)
        if not operation["closed"]:
            result.append(resume_assignment(root, operation["contract"], operation["assignment"]["assignment_id"]))
    return result


def reconcile(root, contract, previous_contract, assignment_id, reason, specification=None, retire=False):
    """Explicitly reopen or retire work after a retained, authorized revision.

    This records the Head's decision; it cannot grant user authorization.
    Reopening preserves the original observation baseline and finding ledger.
    """
    import project_state
    root = root.resolve()
    contract, previous_contract = behavior.validate(contract), behavior.validate(previous_contract)
    require(behavior.text(reason), "contract reconciliation requires a concrete Head reason")
    retained = project_state.load_previous(root) or {}
    require(retained.get("task_contract") == contract, "capture the revised task contract before reconciling assignments")
    require(contract["task_id"] == previous_contract["task_id"], "contract revision cannot change task identity")
    sha, target = behavior.digest(previous_contract), behavior.digest(contract)
    require(sha != target, "reconciliation requires a changed retained contract")
    for revision in retained.get("contract_revisions", []):
        if revision["previous_sha256"] == sha:
            require(behavior.digest(behavior.validate(revision["previous_contract"])) == sha, "invalid retained revision history")
            sha = revision["next_sha256"]
    require(sha == target, "missing retained contract revision chain")
    base, old = load_operation(root, previous_contract, assignment_id, allow_transition=True)
    archive = {"operation": old, "reason": reason, "target_contract_sha256": target}
    if (base / "review.json").exists():
        archive["review"] = manager.read_local_json(base / "review.json")
    if retire:
        require(specification is None and assignment_id not in contract.get("specialist_assignment_ids", []), "required assignments must be reopened, not retired")
        record, returned = accepted_record(base, old)
        require(old["closed"] and record["result"].get("accepted"), "unresolved assignments cannot be retired; reopen and resolve required findings first")
        result = evaluate(root, previous_contract, old, returned, record["evidence"], record["decision"], record["context"],
                          current=old["assignment"]["completion_binding"] == "current-delivery")
        require(result["accepted"], "retirement requires valid prior acceptance; reopen stale or unresolved work")
        replacement = copy.deepcopy(old)
        replacement["retirement"] = {"contract_sha256": target, "reason": reason, "review_sha256": behavior.digest(record)}
    else:
        require(specification is not None, "reopening requires a revised Head assignment")
        assignment = copy.deepcopy(specification)
        assignment.setdefault("completion_binding", old["assignment"]["completion_binding"])
        entry = validate_assignment(assignment, contract)
        require(all(assignment[k] == old["assignment"][k] for k in ("assignment_id", "specialist_id", "stage")), "reopening must preserve assignment identity")
        require(set(old["assignment"]["protected_invariants"]) <= set(assignment["protected_invariants"]), "reopening cannot drop protected invariants")
        require(all(row in assignment.get("shared_contracts", []) for row in old["assignment"].get("shared_contracts", [])), "reopening cannot drop shared contracts")
        require(not (old["assignment"]["completion_binding"] == "current-delivery" and assignment["completion_binding"] != "current-delivery"), "reopening cannot weaken evidence freshness")
        replacement = reopened_operation(old, contract, assignment, entry)
    store_transition(base, old, replacement, archive)
    return {"gate": "PASS", "accepted": False, "action": "retired" if retire else "reopened",
            "assignment": replacement["assignment"], "upstream_revision": replacement["source"]["commit"],
            "head_contract_sha256": replacement["source"]["package_policy"], "record_path": str(base / "operation.json")}


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
        if "retirement" in operation:
            retirement = operation["retirement"]
            require(assignment_id not in expected and retirement["contract_sha256"] == behavior.digest(contract) and behavior.text(retirement["reason"]), "stale or required retired assignment needs reconciliation")
            folder, operation = load_operation(root, operation["contract"], assignment_id)
            record, returned = accepted_record(folder, operation)
            require(operation["closed"] and record["result"].get("accepted") and behavior.digest(record) == retirement["review_sha256"], "retired acceptance changed")
            require(evaluate(root, operation["contract"], operation, returned, record["evidence"], record["decision"], record["context"], current=False)["accepted"], "retired assignment has invalid acceptance")
            continue
        folder, operation = load_operation(root, contract, assignment_id)
        record, returned = accepted_record(folder, operation)
        if not record["result"].get("accepted") or not operation["closed"]:
            failures.append("specialist assignment lacks Head acceptance: " + assignment_id)
            continue
        current = operation["assignment"]["completion_binding"] == "current-delivery"
        if current and operation.get("runtime_binding"):
            entry = validate_assignment(operation["assignment"], contract)
            if control_fingerprint(entry) != operation["control_sha256"]:
                failures.append("current delivery requires migration to changed Head/domain controls: " + assignment_id)
                continue
        result = evaluate(root, contract, operation, returned, record["evidence"], record["decision"], context if current else record["context"], current=current)
        if not result["accepted"]:
            failures.append("specialist acceptance stale/invalid: " + assignment_id)
    failures.extend("required specialist assignment missing: " + aid for aid in set(expected) - seen)
    return failures


def main():
    behavior.configure_output()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("prepare", "assign", "review", "close", "reconcile", "reassess", "migrate", "resume"))
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--task-contract", required=True)
    ap.add_argument("--assignment", help="Head-owned assignment JSON for prepare/assign")
    ap.add_argument("--assignment-id")
    ap.add_argument("--return", dest="returned")
    ap.add_argument("--evidence", help="independent Head receipt catalog JSON array")
    ap.add_argument("--decision", help="separate Head acceptance JSON")
    ap.add_argument("--context", help="independent delivery runtime/dataset JSON object")
    ap.add_argument("--reason", help="Head reason for closing, reconciling or reassessing; never completion")
    ap.add_argument("--previous-task-contract", help="prior retained contract JSON for reconciliation")
    ap.add_argument("--retire", action="store_true", help="retire an accepted assignment removed from the revised contract")
    ap.add_argument("--skills-dir", type=Path, default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "skills")
    ap.add_argument("--state-dir", type=Path, default=capture.local_workspace.workspace_home() / "specialists")
    ns = ap.parse_args()
    try:
        root, contract = ns.root.resolve(), behavior.read(ns.task_contract)
        read = lambda path: json.loads(Path(path).read_text(encoding="utf-8"))
        if ns.mode in ("prepare", "assign"):
            require(ns.assignment is not None, ns.mode + " requires a Head assignment")
            result = (prepare if ns.mode == "prepare" else assign)(root, contract, read(ns.assignment), ns.skills_dir, ns.state_dir)
        elif ns.mode == "resume":
            require(behavior.text(ns.assignment_id), "resume requires assignment ID")
            result = resume_assignment(root, contract, ns.assignment_id)
        elif ns.mode in ("reassess", "migrate"):
            require(behavior.text(ns.assignment_id), "reassess requires assignment ID")
            require(ns.assignment is None and ns.previous_task_contract is None and not ns.retire,
                    "same-contract reassessment cannot revise or retire the assignment")
            result = reassess(root, contract, ns.assignment_id, ns.reason, migrate=ns.mode == "migrate")
        elif ns.mode == "reconcile":
            require(behavior.text(ns.assignment_id) and ns.previous_task_contract is not None, "reconcile requires assignment ID and previous task contract")
            result = reconcile(root, contract, behavior.read(ns.previous_task_contract), ns.assignment_id, ns.reason,
                               read(ns.assignment) if ns.assignment else None, ns.retire)
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
