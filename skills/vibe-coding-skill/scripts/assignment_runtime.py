#!/usr/bin/env python3
"""Retain and dispatch assignment resources outside host skill discovery.

Only assignment continuation uses this protocol. New tasks, migration and release
controls always enter through the current default Head. Records are consistency
controls within a trusted local workspace, not a security sandbox.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import specialist_manager as manager
import local_workspace

PROTOCOL = 1
LIMIT = 8 * 1024 * 1024
MAX_BUNDLES = 128
MAX_TOTAL_BYTES = 512 * 1024 * 1024


class UnsupportedBinding(ValueError):
    """An installation cannot prove isolated lookup; keep its old update guard."""


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def files(root, strict=False):
    """Exact bytes, including non-text resources; reject indirect lookup paths."""
    normalized = manager.installed_hashes(root)  # Also rejects symlinks.
    if strict:
        actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
        require(actual == set(normalized), "unexpected cached/executable files in retained runtime")
    require(normalized and len(normalized) <= 10000, "missing/oversized assignment runtime")
    size = 0
    result = {}
    for rel in normalized:
        path = root / rel
        size += path.stat().st_size
        require(size <= manager.MAX_BYTES, "assignment runtime exceeds resource limit")
        result[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def home(operation):
    state = Path(operation["specialist_state"]).resolve()
    skills, product = Path(operation["skills_dir"]).resolve(), Path(operation["root"]).resolve()
    require(not state.is_relative_to(product) and not state.is_relative_to(skills)
            and not skills.is_relative_to(state), "assignment runtime must stay outside discovery and product")
    target = state / "assignment-runtimes"
    require(not target.is_symlink(), "indirect assignment runtime home")
    return target


def resolve(operation):
    binding = operation.get("runtime_binding", {})
    require(isinstance(binding, dict) and type(binding.get("protocol")) is int
            and binding.get("protocol") == PROTOCOL and re.fullmatch(r"[0-9a-f]{64}", str(binding.get("bundle"))),
            "unsupported or missing assignment runtime binding")
    base = home(operation) / binding["bundle"]
    require(not base.is_symlink(), "indirect assignment runtime bundle")
    manifest = manager.read_local_json(base / "manifest.json")
    require(manager.canonical_digest(manifest) == binding["bundle"] and manifest.get("protocol") == PROTOCOL,
            "assignment runtime manifest changed")
    for role in ("head", "specialist"):
        require(files(base / role, strict=True) == manifest[role]["files"], "retained " + role + " resources missing or changed")
    require(manifest["specialist_id"] == operation["assignment"]["specialist_id"]
            and manifest["specialist"]["source"] == operation["source"]
            and manager.installed_hashes(base / "specialist") == operation["specialist_files"],
            "assignment runtime provenance mismatch")
    compatible = manifest["compatibility"]
    require(manager.canonical_digest(compatible["binding"]) == operation["compatibility_binding_sha256"]
            == compatible["assessment"]["binding_sha256"]
            and compatible["assessment"]["decision"] == "accepted", "retained compatibility mismatch")
    return base, manifest


def is_local(base):
    return manager.ROOT.resolve() == (base / "head").resolve()


def describe(operation, base, manifest):
    return {"protocol": PROTOCOL, "assignment_id": operation["assignment"]["assignment_id"],
            "bundle": operation["runtime_binding"]["bundle"], "head_root": str(base / "head"),
            "head_skill": str(base / "head/SKILL.md"), "specialist_skill": str(base / "specialist/SKILL.md"),
            "specialist_contract": str(base / "specialist/vibe-head-contract.md"),
            "head_source": manifest["head"]["source"], "specialist_source": manifest["specialist"]["source"],
            "current_default": False, "upstream_checked": False,
            "instruction": "Continue only this retained assignment with these resources; use the current default for new tasks, migration and release gates."}


def invoke(operation, action, **arguments):
    require(action in ("probe", "resume", "evaluate", "review"), "unsupported assignment runtime action")
    base, manifest = resolve(operation)
    payload = json.dumps({"operation": operation, "action": action, "arguments": arguments}, ensure_ascii=False)
    require(len(payload.encode("utf-8")) <= LIMIT, "assignment dispatch input limit exceeded")
    env = dict(os.environ, PYTHONPATH="", PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(base / "head/scripts/assignment_runtime.py"), "worker"],
                            input=payload, text=True, encoding="utf-8", capture_output=True,
                            cwd=operation["root"], env=env, timeout=60)
    require(len(result.stdout.encode("utf-8")) <= LIMIT, "assignment dispatch output limit exceeded")
    try:
        reply = json.loads(result.stdout)
    except ValueError as exc:
        raise ValueError("retained runtime did not return a valid response") from exc
    require(result.returncode == 0 and reply.get("ok") is True, "retained runtime failed: " + str(reply.get("error", result.stderr[:500])))
    require(reply.get("runtime") == describe(operation, base, manifest), "retained runtime lookup mismatch")
    if action in ("review", "evaluate"):
        return {**reply["result"], "runtime": reply["runtime"]}
    return reply["result"]


def retain(operation, record_path):
    """Called under the existing installation lock, before publishing markers."""
    skills, state = Path(operation["skills_dir"]), Path(operation["specialist_state"])
    entry = next(e for e in manager.registry()["specialists"] if e["id"] == operation["assignment"]["specialist_id"])
    head = manager.registry()["head"]
    sources = {}
    for role, selected in (("head", head), ("specialist", entry)):
        target = skills / selected["skill_name"]
        if role == "head" and not (target / "scripts/assignment_runtime.py").is_file():
            raise UnsupportedBinding("installed Head lacks isolated assignment dispatch; active update guard retained")
        record = manager.read_local_json(state / (selected["id"] + ".json"))
        require(record.get("status") == "current" and record.get("installation") == str(target)
                and record.get("files") == manager.installed_hashes(target)
                and record.get("source", {}).get("repository") == selected["repository"]
                and record["source"].get("skill_path") == selected["skill_path"], "runtime retention needs verified managed resources")
        if role == "head":
            # A newer source script cannot claim an older installed runtime as itself.
            for rel, expected in record["files"].items():
                source = manager.ROOT / rel
                if not source.is_file() or manager.digest(rel, source.read_bytes()) != expected:
                    raise UnsupportedBinding("running Head differs from the managed default; reload before binding")
        sources[role] = {"source": record["source"], "files": files(target)}
    compatible = manager.compatibility(entry, skills, state, manager.read_local_json(state / (entry["id"] + ".json")))
    require(compatible.get("status") == "accepted", "runtime retention requires accepted compatibility")
    packet = manager.compatibility_packet(entry, skills, state, manager.read_local_json(state / (entry["id"] + ".json")))
    require(packet["binding_sha256"] == operation["compatibility_binding_sha256"], "assignment compatibility changed before retention")
    manifest = {"protocol": PROTOCOL, **sources, "specialist_id": entry["id"],
                "compatibility": {"binding": packet["binding"], "assessment": manager.read_local_json(Path(compatible["assessment_path"]))}}
    identity = manager.canonical_digest(manifest)
    target = home(operation) / identity
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        bundles = list(target.parent.iterdir())
        require(len(bundles) < MAX_BUNDLES, "retained runtime limit reached; inspect references and prune only unreferenced bundles")
        retained_size = sum(p.stat().st_size for p in target.parent.rglob("*") if p.is_file())
        incoming_size = sum((skills / selected["skill_name"] / rel).stat().st_size
                            for role, selected in (("head", head), ("specialist", entry)) for rel in sources[role]["files"])
        require(retained_size + incoming_size <= MAX_TOTAL_BYTES, "retained runtime byte limit reached; preserve referenced history")
        with tempfile.TemporaryDirectory(prefix=".assignment-stage-", dir=state) as temporary:
            staging = Path(temporary) / "bundle"
            staging.mkdir()
            for role, selected in (("head", head), ("specialist", entry)):
                for rel in sources[role]["files"]:
                    destination = staging / role / rel
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(skills / selected["skill_name"] / rel, destination)
                require(files(staging / role) == sources[role]["files"], "resources changed while retaining assignment")
            manager.write_record(staging / "manifest.json", manifest)
            os.replace(staging, target)
    candidate = {**operation, "runtime_binding": {"protocol": PROTOCOL, "bundle": identity}}
    resolve(candidate)
    invoke(candidate, "probe")  # Prove imports and actual lookup before unlocking any update.
    owner = {"operation_path": str(record_path.resolve()), "root": operation["root"]}
    require(len(list((target / "owners").glob("*.json"))) < 1000, "runtime owner limit reached; preserve referenced history")
    manager.write_record(target / "owners" / (manager.canonical_digest(owner) + ".json"), owner)
    return candidate["runtime_binding"]


def update_blocker(entry, skills, state):
    """Legacy, corrupt or partially written transitions remain protected."""
    for marker_path in sorted((state / "active-assignments" / entry["id"]).glob("*.json")):
        try:
            marker = manager.read_local_json(marker_path)
            if not marker.get("runtime_binding") or not marker.get("operation_path"):
                return "legacy active assignment has no verified runtime binding"
            path = Path(marker["operation_path"]).resolve()
            require(path.is_relative_to(local_workspace.project_workspace(Path(marker["root"])) / "state/specialist-handoffs"), "marker operation path escapes project ledger")
            operation = manager.read_local_json(path)
            require(operation["root"] == marker["root"] and operation["assignment"]["task_id"] == marker["task_id"]
                    and operation["assignment"]["assignment_id"] == marker["assignment_id"]
                    and operation.get("runtime_binding") == marker["runtime_binding"]
                    and Path(operation["skills_dir"]).resolve() == skills.resolve()
                    and Path(operation["specialist_state"]).resolve() == state.resolve(), "active runtime transition is incomplete or misbound")
            resolve(operation)
        except (ValueError, OSError, KeyError, TypeError) as exc:
            return "active assignment runtime unverified: " + str(exc)
    return None


def prune(skills, state, apply=False):
    """Only remove bundles disproved by readable current AND revision records."""
    result = {"removed": [], "eligible": [], "retained": []}
    require(not state.resolve().is_relative_to(skills.resolve()) and not skills.resolve().is_relative_to(state.resolve()),
            "runtime cleanup state must remain separate from discovery")
    with manager.installation_lock(skills):
        directory = state / "assignment-runtimes"
        require(not directory.is_symlink(), "indirect runtime storage")
        markers = list((state / "active-assignments").glob("*/*.json"))
        require(len(markers) <= 2000, "active runtime marker limit exceeded")
        active = set()
        for marker in markers:
            # An unreadable marker is not permission to clean up possible work.
            active.add(manager.read_local_json(marker).get("runtime_binding", {}).get("bundle"))
        for bundle in sorted(directory.glob("*")):
            require(bundle.is_dir() and not bundle.is_symlink() and re.fullmatch(r"[0-9a-f]{64}", bundle.name), "unexpected retained runtime entry")
            require(manager.canonical_digest(manager.read_local_json(bundle / "manifest.json")) == bundle.name, "runtime cleanup requires an intact manifest")
            owners = list((bundle / "owners").glob("*.json"))
            require(len(owners) <= 1000, "runtime owner limit exceeded")
            retained = bundle.name in active or ((bundle / "owners").exists() and not owners)
            for owner_path in owners:
                try:
                    owner = manager.read_local_json(owner_path)
                    require(owner_path.stem == manager.canonical_digest(owner), "runtime owner record changed")
                    path = Path(owner["operation_path"]).resolve()
                    require(path.is_relative_to(local_workspace.project_workspace(Path(owner["root"])) / "state/specialist-handoffs"), "invalid retained owner")
                    revisions = list((path.parent / "revisions").glob("*.json"))
                    require(len(revisions) <= 1000, "revision limit exceeded")
                    records = [manager.read_local_json(path), *(manager.read_local_json(p)["operation"] for p in revisions)]
                    retained |= any(r.get("runtime_binding", {}).get("bundle") == bundle.name for r in records)
                except (ValueError, OSError, KeyError, TypeError):
                    retained = True  # Missing history is not proof of an orphan.
            if retained:
                result["retained"].append(bundle.name)
            else:
                result["eligible"].append(bundle.name)
                if apply:
                    require(bundle.resolve().parent == directory.resolve(), "cleanup escaped runtime storage")
                    shutil.rmtree(bundle)
                    result["removed"].append(bundle.name)
    return result


def worker():
    raw = sys.stdin.buffer.read(LIMIT + 1)
    require(len(raw) <= LIMIT, "assignment dispatch input limit exceeded")
    payload = json.loads(raw)
    operation, action, args = payload["operation"], payload["action"], payload["arguments"]
    base, manifest = resolve(operation)
    require(is_local(base), "worker loaded the default instead of retained Head")
    import specialist_handoff as handoff
    for module in (manager, handoff, handoff.capture, handoff.receipts, handoff.behavior, local_workspace):
        require(Path(module.__file__).resolve().is_relative_to(base / "head/scripts"), "mixed assignment runtime imports")
    root, contract = Path(operation["root"]), operation["contract"]
    if action in ("probe", "resume"):
        entry = handoff.validate_assignment(operation["assignment"], contract)
        require(handoff.control_fingerprint(entry) == operation["control_sha256"], "retained controls mismatch")
        result = describe(operation, base, manifest)
    elif action == "evaluate":
        result = handoff.evaluate(root, contract, operation, **args)
    elif action == "review":
        result = handoff.review(root, contract, operation["assignment"]["assignment_id"], **args)
    else:
        raise ValueError("unsupported retained runtime action")
    return {"ok": True, "runtime": describe(operation, base, manifest), "result": result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("worker", "prune"))
    parser.add_argument("--skills-dir", type=Path)
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        if args.mode == "worker":
            result = worker()
        else:
            require(args.skills_dir and args.state_dir, "prune requires explicit host skills and state paths")
            result = prune(args.skills_dir.resolve(), args.state_dir.resolve(), args.apply)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
