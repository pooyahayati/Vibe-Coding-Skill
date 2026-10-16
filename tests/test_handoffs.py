"""S2 actual project changes, retained findings, receipt resolution and completion."""
import copy
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import behavior_contract as behavior
import evidence_capture as capture
import specialist_handoff as handoff
import specialist_manager as manager
import completion_gate as gate
import execution_plan
from test_cross_platform import receipt_contract


class HandoffTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / "product"
        (self.root / "src/generated").mkdir(parents=True)
        (self.root / "src/value.txt").write_text("original", encoding="utf-8")
        (self.root / "check.py").write_text("from pathlib import Path\nassert Path('src/value.txt').read_text() == 'changed'\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        for args in (["config", "user.name", "Test"], ["config", "user.email", "test@example.invalid"], ["add", "."], ["commit", "-qm", "baseline"]):
            subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)
        environment = patch.dict(os.environ, {"VIBE_CODING_HOME": str(self.base / "workspace"), "PYTHONDONTWRITEBYTECODE": "1"})
        environment.start()
        self.addCleanup(environment.stop)
        self.skills, self.state = self.base / "skills", self.base / "specialists"
        self.entry = manager.registry()["specialists"][0]
        self.source = {"repository": self.entry["repository"], "skill_path": self.entry["skill_path"], "commit": "a" * 40, "channel": "stable-release", "ref": "v1"}
        self.files = {"SKILL.md": b"---\nname: ui-ux-skill\n---\nUse the assigned product stack.\n", "vibe-head-contract.md": (ROOT / "references/specialist-authority.md").read_bytes()}
        for mocked in (patch.object(manager, "resolve_latest", return_value=self.source), patch.object(manager, "source_package", return_value=self.files)):
            mocked.start()
            self.addCleanup(mocked.stop)
        installed = manager.ensure(self.entry, self.skills, self.state, True)
        packet = manager.compatibility_packet(self.entry, self.skills, self.state, installed)
        assessment = {"format": "vibe-specialist-compatibility", "schema_version": 1, "specialist_id": self.entry["id"],
                      **{k: packet[k] for k in ("binding_sha256", "upstream_revision", "head_contract_sha256")},
                      "decision": "accepted", "assessed_by": "Head", "assessed_at": capture.now(), "reason": "Read the contained domain text and effective Head contract.",
                      "reviewed_paths": packet["required_review_paths"], "conflicts": [],
                      "checks": [{"area": a, "status": "compatible", "rationale": "The contained fixture uses assigned Head controls without additional requests.", "resource_paths": ["SKILL.md", "vibe-head-contract.md"]} for a in sorted(manager.COMPATIBILITY_AREAS)]}
        self.assertEqual(manager.compatibility(self.entry, self.skills, self.state, installed, assessment)["status"], "accepted")
        self.assessment = assessment
        original = manager.ensure
        self.real_ensure = original
        def ensure(entry, *args):
            return {"id": entry["id"], "status": "current", "updated": False} if entry["id"] == "vibe-coding-skill" else original(entry, *args)
        mocked = patch.object(manager, "ensure", side_effect=ensure)
        mocked.start()
        self.addCleanup(mocked.stop)
        self.contract = receipt_contract()
        self.contract["objective"] = "Save the supplied setting value"
        self.contract["acceptance_criteria"][0]["description"] = "The supplied new value is stored after saving"
        self.contract["scope"] = ["src", "check.py", "docs"]
        self.contract["specialist_assignment_ids"] = ["ui-build"]
        self.spec = {"format": "vibe-specialist-assignment", "schema_version": 1, "task_id": self.contract["task_id"], "assignment_id": "ui-build",
                     "specialist_id": self.entry["id"], "stage": "build", "contract_sha256": behavior.digest(self.contract), "criterion_ids": ["setting"],
                     "scope": ["src"], "input_excludes": ["src/generated"], "settled_decisions": ["Preserve the actual stack"], "protected_invariants": [],
                     "authorized_actions": ["Edit assigned UI within existing authority"], "evidence_requirement_ids": ["check"], "platform": {"stack": "fixture product", "runtime": "Python"},
                     "completion_binding": "current-delivery"}

    def start(self, spec=None):
        return handoff.assign(self.root, self.contract, spec or self.spec, self.skills, self.state)

    def install_head_fixture(self):
        head = manager.registry()["head"]
        source = dict(self.source, repository=head["repository"], skill_path=head["skill_path"])
        with patch.object(manager, "resolve_latest", return_value=source):
            self.real_ensure(head, self.skills, self.state, True)

    def resolve_fixture(self, entry):
        return dict(self.source, repository=entry["repository"], skill_path=entry["skill_path"])

    def install_isolated_head(self, changed=False):
        head = manager.registry()["head"]
        paths = [ROOT / name for name in ("SKILL.md", "VERSION", "LICENSE")]
        for name in ("scripts", "references", "config", "assets/templates", "packs", "agents", "evals"):
            paths.extend(p for p in (ROOT / name).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
        content = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in paths if p.is_file()}
        if changed:
            content["SKILL.md"] += b"\nNew default fixture instructions.\n"
        with patch.object(manager, "resolve_latest", side_effect=self.resolve_fixture), patch.object(manager, "source_package", return_value=content):
            result = self.real_ensure(head, self.skills, self.state, True)
        self.assertEqual(result["status"], "current", result)
        return self.skills / head["skill_name"]

    def update_isolated_defaults(self):
        self.source["commit"] = "b" * 40
        self.source["ref"] = "v2"
        head = self.install_isolated_head(changed=True)
        self.files["SKILL.md"] += b"\nNew specialist fixture instructions.\n"
        installed = self.real_ensure(self.entry, self.skills, self.state, True)
        self.assertEqual(installed["status"], "current", installed)
        packet = manager.compatibility_packet(self.entry, self.skills, self.state, installed)
        assessment = dict(copy.deepcopy(self.assessment), **{k: packet[k] for k in ("binding_sha256", "upstream_revision", "head_contract_sha256")},
                          reviewed_paths=packet["required_review_paths"])
        self.assertEqual(manager.compatibility(self.entry, self.skills, self.state, installed, assessment)["status"], "accepted")
        return head

    def test_isolated_runtime_two_projects_use_actual_old_and_new_resources(self):
        import resume_context
        import assignment_runtime as runtime
        self.install_isolated_head()
        start = self.start()
        self.assertIsNotNone(start["runtime_binding"], start)
        returned = self.output(start)
        head = self.update_isolated_defaults()
        second = self.base / "second-product"
        shutil.copytree(self.root, second)
        with patch.object(manager, "ROOT", head), patch.object(manager, "REGISTRY", head / "config/specialists.json"):
            started = handoff.assign(second, self.contract, self.spec, self.skills, self.state)
            self.assertIsNotNone(started["runtime_binding"], started)
            self.assertNotEqual(start["runtime_binding"], started["runtime_binding"])
            old = resume_context.build_context(self.root)["local_state"]["specialist_runtimes"][0]
            new = resume_context.build_context(second)["local_state"]["specialist_runtimes"][0]
            self.assertEqual(old["head_source"]["commit"], "a" * 40)
            self.assertEqual(new["head_source"]["commit"], "b" * 40)
            self.assertNotIn("New default fixture", Path(old["head_skill"]).read_text(encoding="utf-8"))
            self.assertIn("New default fixture", Path(new["head_skill"]).read_text(encoding="utf-8"))
            self.assertFalse(Path(old["head_root"]).is_relative_to(self.skills))
            # This review runs in a fresh interpreter imported from A's old Head.
            inspected = self.inspect(returned)
            self.assertEqual(inspected["gate"], "UNVERIFIED", inspected)
            self.assertEqual(inspected["runtime"]["head_source"]["commit"], "a" * 40)
            self.assertTrue(self.inspect(returned, self.decision(returned, inspected))["accepted"])
            self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "PASS")
            # Historical lookup cannot bypass a changed current delivery control.
            with patch.object(handoff, "control_fingerprint", return_value="changed-current-controls"):
                self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "BLOCK")
            with self.assertRaisesRegex(ValueError, "unsupported"):
                _, operation = handoff.load_operation(self.root, self.contract, "ui-build")
                runtime.invoke(operation, "release")
        self.assertEqual(len(list(self.skills.glob("*/SKILL.md"))), 2)
        retained = runtime.prune(self.skills, self.state, apply=True)
        self.assertEqual(retained["removed"], [])
        self.assertEqual(len(retained["retained"]), 2)  # Includes closed acceptance history.

    def test_isolated_runtime_migration_preserves_findings_and_invalidates_scoped_acceptance(self):
        import assignment_runtime as runtime
        self.install_isolated_head()
        start = self.start()
        returned = self.output(start)
        finding = {"id": "saved", "required": True, "description": "Saved setting must match input", "status": "open"}
        returned["findings"] = [finding]
        self.assertEqual(self.inspect(returned)["gate"], "BLOCK")
        resumed = handoff.resume_assignment(self.root, self.contract, "ui-build")
        self.assertEqual(resumed["required_findings"], [{"id": "saved", "description": finding["description"]}])
        base, old = handoff.load_operation(self.root, self.contract, "ui-build")
        head = self.update_isolated_defaults()
        with patch.object(manager, "ROOT", head), patch.object(manager, "REGISTRY", head / "config/specialists.json"):
            write = manager.write_record
            def interrupted(path, value):
                if path == base / "operation.json":
                    raise OSError("interrupted runtime migration")
                return write(path, value)
            with patch.object(manager, "write_record", side_effect=interrupted), self.assertRaises(OSError):
                handoff.reassess(self.root, self.contract, "ui-build", "Adopt reviewed current controls", migrate=True)
            self.assertIsNotNone(runtime.update_blocker(self.entry, self.skills, self.state))
            with self.assertRaisesRegex(ValueError, "incomplete runtime transition"):
                handoff.resume_assignment(self.root, self.contract, "ui-build")
            migrated = handoff.reassess(self.root, self.contract, "ui-build", "Adopt the new default after reviewing changed controls", migrate=True)
            self.assertEqual(migrated["action"], "migrated")
            self.assertFalse(migrated["accepted"])
            _, current = handoff.load_operation(self.root, self.contract, "ui-build")
            self.assertEqual(current["assignment"], old["assignment"])
            self.assertEqual(current["baseline"], old["baseline"])
            self.assertNotEqual(current["runtime_binding"], old["runtime_binding"])
            stale = dict(returned, upstream_revision=migrated["upstream_revision"], head_contract_sha256=migrated["head_contract_sha256"])
            self.assertEqual(self.inspect(stale)["gate"], "BLOCK")
            fresh = self.output(migrated)
            with self.assertRaisesRegex(ValueError, "required finding"):
                self.inspect(fresh)
            fresh["findings"] = [dict(finding, status="resolved", resolution_evidence_ids=fresh["evidence_ids"])]
            checked = self.inspect(fresh)
            self.assertEqual(checked["gate"], "UNVERIFIED", checked)
            self.assertTrue(self.inspect(fresh, self.decision(fresh, checked))["accepted"])
        archives = [manager.read_local_json(p) for p in (base / "revisions").glob("*.json")]
        self.assertTrue(any(a["operation"] == old for a in archives))
        self.assertIn(old["runtime_binding"]["bundle"], runtime.prune(self.skills, self.state, apply=True)["retained"])

    def test_isolated_runtime_damage_and_interrupted_binding_keep_update_protection(self):
        import assignment_runtime as runtime
        import resume_context
        self.install_isolated_head()
        base = handoff.directory(self.root, self.contract["task_id"], "ui-build")
        write = manager.write_record
        def interrupted(path, value):
            if path == base / "operation.json":
                raise OSError("interrupted operation publication")
            return write(path, value)
        with patch.object(manager, "write_record", side_effect=interrupted), self.assertRaises(OSError):
            self.start()
        self.source["commit"] = "b" * 40
        self.assertEqual(self.real_ensure(self.entry, self.skills, self.state, True)["status"], "update-deferred-active-assignment")
        self.source["commit"] = "a" * 40
        self.start()  # Retry can finish the same unpublished assignment safely.
        _, operation = handoff.load_operation(self.root, self.contract, "ui-build")
        bundle, _ = runtime.resolve(operation)
        target = bundle / "specialist/SKILL.md"
        original = target.read_bytes()
        self.source["commit"] = "b" * 40
        for missing in (False, True):
            with self.subTest(missing=missing):
                if missing:
                    target.unlink()
                else:
                    target.write_bytes(original + b"changed")
                self.assertEqual(self.real_ensure(self.entry, self.skills, self.state, True)["status"], "update-deferred-active-assignment")
                with self.assertRaisesRegex(RuntimeError, "continuation needs repair"):
                    resume_context.build_context(self.root)
                target.write_bytes(original)
        with patch.object(runtime, "PROTOCOL", 2):
            self.assertIsNotNone(runtime.update_blocker(self.entry, self.skills, self.state))
        # A broken retained compatibility decision is not a usable historical source.
        manifest = bundle / "manifest.json"
        original_manifest = manifest.read_bytes()
        value = json.loads(original_manifest)
        value["compatibility"]["assessment"]["decision"] = "blocked"
        manager.write_record(manifest, value)
        self.assertIsNotNone(runtime.update_blocker(self.entry, self.skills, self.state))
        manifest.write_bytes(original_manifest)
        cached = bundle / "head/scripts/__pycache__/specialist_manager.pyc"
        cached.parent.mkdir()
        cached.write_bytes(b"untracked executable cache")
        with self.assertRaisesRegex(ValueError, "cached/executable"):
            handoff.resume_assignment(self.root, self.contract, "ui-build")
        cached.unlink()
        cached.parent.rmdir()
        orphan_manifest = json.loads(original_manifest)
        orphan_manifest["head"]["source"]["ref"] = "interrupted-unpublished-candidate"
        orphan = bundle.parent / manager.canonical_digest(orphan_manifest)
        shutil.copytree(bundle, orphan, ignore=shutil.ignore_patterns("owners"))
        manager.write_record(orphan / "manifest.json", orphan_manifest)
        self.assertEqual(runtime.prune(self.skills, self.state)["eligible"], [orphan.name])
        self.assertTrue(orphan.exists())
        self.assertEqual(runtime.prune(self.skills, self.state, apply=True)["removed"], [orphan.name])
        self.assertTrue(bundle.exists())

    def test_preparation_reuses_only_the_same_assignment_without_duplicate_upstream_checks(self):
        self.install_head_fixture()
        contract_path, assignment_path = self.base / "contract.json", self.base / "assignment.json"
        contract_path.write_text(json.dumps(self.contract), encoding="utf-8")
        assignment_path.write_text(json.dumps(self.spec), encoding="utf-8")
        def cli(mode):
            output = io.StringIO()
            args = [handoff.__file__, mode, "--root", str(self.root), "--task-contract", str(contract_path),
                    "--assignment", str(assignment_path), "--skills-dir", str(self.skills), "--state-dir", str(self.state)]
            with patch.object(sys, "argv", args), redirect_stdout(output):
                result = handoff.main()
            self.assertEqual(result, 0, output.getvalue())
            return json.loads(output.getvalue())
        with patch.object(manager, "ensure", wraps=self.real_ensure), patch.object(manager, "resolve_latest", side_effect=self.resolve_fixture) as upstream:
            result = cli("prepare")
            self.assertEqual(result["gate"], "PASS")
            self.assertEqual(upstream.call_count, 2)  # Head and selected specialist, once each.
            manager.write_record(self.state / "inventory.json", {
                "schema_version": 1, "checked_at": "2000-01-01T00:00:00+00:00",
                "attempted_at": "2000-01-02T00:00:00+00:00", "status": "failed",
                "failures": [{"id": "debugging-and-error-recovery", "status": "currency-unverified"}]})
            # A new explicit task-start preparation always observes upstream again.
            result = cli("prepare")
            self.assertEqual(result["gate"], "WARN")
            self.assertTrue(result["inventory"]["due"])
            self.assertEqual(upstream.call_count, 4)
            prepared = manager.read_local_json(Path(result["preparation_path"]))
            with patch.object(manager, "resolve_latest", side_effect=OSError("offline")) as offline:
                started = cli("assign")
                offline.assert_not_called()
            self.assertTrue(started["preflight_reuse"]["reused"])
            self.assertFalse(started["preflight_reuse"]["upstream_checked"])
            self.assertEqual(started["preflight_reuse"]["checked_at"], prepared["checked_at"])
            self.assertFalse(started["accepted"])
            self.assertFalse(Path(result["preparation_path"]).exists())

    def test_changed_preparation_inputs_and_expiry_require_fresh_checks(self):
        self.install_head_fixture()
        with patch.object(manager, "ensure", wraps=self.real_ensure), patch.object(manager, "resolve_latest", side_effect=self.resolve_fixture):
            for case in ("scope-file", "assignment", "contract", "resource", "head-resource", "source", "controls", "assessment", "expired"):
                with self.subTest(case=case):
                    result = handoff.prepare(self.root, self.contract, self.spec, self.skills, self.state)
                    self.assertEqual(result["gate"], "PASS")
                    path = Path(result["preparation_path"])
                    contract, spec = copy.deepcopy(self.contract), copy.deepcopy(self.spec)
                    originals = {}
                    def write(target, value):
                        originals[target] = target.read_bytes()
                        target.write_bytes(value if isinstance(value, bytes) else json.dumps(value).encode())
                    registry = manager.registry()
                    try:
                        if case == "scope-file":
                            write(self.root / "src/value.txt", b"new input")
                        elif case == "assignment":
                            spec["settled_decisions"].append("New accepted layout decision")
                        elif case == "contract":
                            contract["scope"].append("extra")
                            spec["contract_sha256"] = behavior.digest(contract)
                        elif case in ("resource", "head-resource"):
                            name = self.entry["skill_name"] if case == "resource" else registry["head"]["skill_name"]
                            write(self.skills / name / "SKILL.md", b"changed instructions")
                        elif case == "source":
                            record = self.state / (self.entry["id"] + ".json")
                            value = manager.read_local_json(record)
                            value["source"]["commit"] = "b" * 40
                            write(record, value)
                        elif case == "controls":
                            registry["permissions"]["head_owned"].append("new-control")
                        elif case == "assessment":
                            installed = manager.read_local_json(self.state / (self.entry["id"] + ".json"))
                            packet = manager.compatibility_packet(self.entry, self.skills, self.state, installed)
                            target = Path(packet["assessment_path"])
                            value = manager.read_local_json(target)
                            value["decision"] = "blocked"
                            write(target, value)
                        else:
                            target = path
                            value = manager.read_local_json(target)
                            value["checked_at"] = "2000-01-01T00:00:00+00:00"
                            write(target, value)
                        with patch.object(manager, "registry", return_value=registry), patch.object(manager, "resolve_latest", side_effect=OSError("offline")) as upstream:
                            with self.assertRaisesRegex(ValueError, "current Head"):
                                handoff.assign(self.root, contract, spec, self.skills, self.state)
                            self.assertGreater(upstream.call_count, 0)
                    finally:
                        for target, raw in originals.items():
                            target.write_bytes(raw)

    def test_failed_new_preparation_cannot_reuse_old_currency(self):
        self.install_head_fixture()
        with patch.object(manager, "ensure", wraps=self.real_ensure), patch.object(manager, "resolve_latest", side_effect=self.resolve_fixture):
            handoff.prepare(self.root, self.contract, self.spec, self.skills, self.state)
            with patch.object(manager, "resolve_latest", side_effect=OSError("offline")):
                changed = copy.deepcopy(self.spec)
                changed["settled_decisions"].append("A revised decision for the same assignment")
                failed = handoff.prepare(self.root, self.contract, changed, self.skills, self.state)
                self.assertEqual(failed["gate"], "BLOCK")
                # Reverting the spec after a failed refresh cannot revive old success.
                with self.assertRaisesRegex(ValueError, "current Head"):
                    self.start()

    def output(self, start, changes=None):
        (self.root / "src/value.txt").write_text("changed", encoding="utf-8")
        result = capture.capture(self.root, self.contract, "check", [sys.executable, "check.py"])
        self.assertEqual(result["receipt"]["result"], "pass")
        r = result["receipt"]
        self.evidence = [{"id": r["id"], "kind": r["kind"], "origin": r["origin"], "result": "pass", "required": True,
                          "requirement_id": "check", "receipt_ref": result["receipt_ref"], "receipt_sha256": result["receipt_sha256"]}]
        return {"format": "vibe-specialist-return", "schema_version": 1, **{k: start["assignment"][k] for k in ("task_id", "assignment_id", "specialist_id", "stage", "contract_sha256")},
                "upstream_revision": start["upstream_revision"], "head_contract_sha256": start["head_contract_sha256"], "changed_surfaces": changes or [{"path": "src/value.txt", "action": "modify"}],
                "decisions": [], "invariants": [], "evidence_ids": [r["id"]], "findings": [], "unperformed_checks": [], "conflicts": [], "next_action": "Head integrates and verifies the product outcome"}

    def inspect(self, returned, decision=None):
        return handoff.review(self.root, self.contract, "ui-build", returned, self.evidence, decision)

    def decision(self, returned, result):
        return {"format": "vibe-head-acceptance", "schema_version": 1,
                **{k: returned[k] for k in ("task_id", "assignment_id", "contract_sha256", "upstream_revision", "head_contract_sha256")},
                **{k: result["review"][k] for k in ("return_sha256", "delivery_sha256", "unresolved_required_finding_ids")},
                "decision": "accepted", "assessed_by": "Head", "assessed_at": capture.now(), "reason": "Inspected actual changes and the linked execution receipt.",
                "scope_reconciliations": [], "contract_decisions": []}

    def report(self):
        return {"schema_version": 3, "task_id": self.contract["task_id"], "contract_sha256": behavior.digest(self.contract), "status": "Done", "risk_tier": 1, "blockers": [],
                "acceptance_criteria": [dict(self.contract["acceptance_criteria"][0], met=True, evidence_ids=[self.evidence[0]["id"]])], "evidence": self.evidence}

    def revise(self, remove=False):
        import project_state
        previous = copy.deepcopy(self.contract)
        project_state.capture(self.root, task_contract=previous)
        self.contract["scope"].append("extra")
        if remove:
            self.contract["specialist_assignment_ids"] = []
        project_state.capture(self.root, task_contract=self.contract, accept_contract_change="User-approved scope revision")
        self.spec["contract_sha256"] = behavior.digest(self.contract)
        return previous

    def test_accepted_specialist_reopens_after_revision_with_new_receipts_and_acceptance(self):
        returned = self.output(self.start())
        self.assertTrue(self.inspect(returned, self.decision(returned, self.inspect(returned)))["accepted"])
        previous = self.revise()
        self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "BLOCK")
        start = handoff.reconcile(self.root, self.contract, previous, "ui-build", "Reassess against approved scope", self.spec)
        self.assertFalse(start["accepted"])
        stale = dict(returned, contract_sha256=behavior.digest(self.contract))
        self.assertEqual(self.inspect(stale)["gate"], "BLOCK")
        returned = self.output(start)
        result = self.inspect(returned)
        self.assertEqual(result["gate"], "UNVERIFIED")
        self.assertTrue(self.inspect(returned, self.decision(returned, result))["accepted"])
        self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "PASS")
        base = handoff.directory(self.root, self.contract["task_id"], "ui-build")
        self.assertTrue(list((base / "revisions").glob("*.json")))

    def test_same_contract_reassessment_requires_fresh_evidence_and_preserves_history(self):
        original_contract = copy.deepcopy(self.contract)
        returned = self.output(self.start())
        finding = {"id": "saved", "required": True, "description": "Saved setting must match input",
                   "status": "resolved", "resolution_evidence_ids": returned["evidence_ids"]}
        returned["findings"] = [finding]
        decision = self.decision(returned, self.inspect(returned))
        self.assertTrue(self.inspect(returned, decision)["accepted"])
        old_evidence = copy.deepcopy(self.evidence)
        self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "PASS")
        with (self.root / "check.py").open("a", encoding="utf-8") as stream:
            stream.write("# in-scope correction\n")
        self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "BLOCK")
        base, old = handoff.load_operation(self.root, self.contract, "ui-build")
        start = handoff.reassess(self.root, self.contract, "ui-build", "Recheck the corrected input under the unchanged contract")
        self.assertFalse(start["accepted"])
        _, active = handoff.load_operation(self.root, self.contract, "ui-build")
        self.assertEqual(active["assignment"], old["assignment"])
        self.assertEqual(active["baseline"], old["baseline"])
        self.assertEqual(self.contract, original_contract)
        archived = [manager.read_local_json(path) for path in (base / "revisions").glob("*.json")]
        self.assertTrue(any(row["review"]["decision"] == decision for row in archived))
        for name in ("vibe-coding-skill", self.entry["id"]):
            self.assertTrue(list((self.state / "active-assignments" / name).glob("*.json")))
        # Even reverting inputs cannot resurrect the prior receipt/Head decision.
        (self.root / "check.py").write_text("from pathlib import Path\nassert Path('src/value.txt').read_text() == 'changed'\n", encoding="utf-8")
        self.assertEqual(self.inspect(returned, decision)["gate"], "BLOCK")
        fresh = self.output(start)
        with self.assertRaisesRegex(ValueError, "required finding"):
            self.inspect(fresh)
        fresh["findings"] = [dict(finding, resolution_evidence_ids=fresh["evidence_ids"])]
        result = self.inspect(fresh)
        self.assertEqual(result["gate"], "UNVERIFIED")
        self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "BLOCK")
        self.assertTrue(self.inspect(fresh, self.decision(fresh, result))["accepted"])
        self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "PASS")
        self.assertNotEqual(self.evidence[0]["id"], old_evidence[0]["id"])
        self.assertFalse(list((self.state / "active-assignments" / self.entry["id"]).glob("*.json")))

    def test_reassessment_blocks_old_decision_without_receipts_and_retains_guard_on_interruption(self):
        spec = dict(self.spec, stage="design", completion_binding="stage-handoff", evidence_requirement_ids=[])
        returned = self.output(self.start(spec))
        returned["evidence_ids"] = []
        self.evidence = []
        decision = self.decision(returned, self.inspect(returned))
        self.assertTrue(self.inspect(returned, decision)["accepted"])
        base, before = handoff.load_operation(self.root, self.contract, "ui-build")
        original = manager.write_record
        def interrupt(path, value):
            if path == base / "operation.json":
                raise OSError("interrupted operation write")
            return original(path, value)
        with patch.object(manager, "write_record", side_effect=interrupt), self.assertRaisesRegex(OSError, "interrupted"):
            handoff.reassess(self.root, self.contract, "ui-build", "Reassess domain controls")
        self.assertEqual(handoff.load_operation(self.root, self.contract, "ui-build")[1], before)
        self.assertTrue(list((self.state / "active-assignments" / self.entry["id"]).glob("*.json")))
        handoff.reassess(self.root, self.contract, "ui-build", "Resume explicit reassessment")
        with self.assertRaisesRegex(ValueError, "already active"):
            handoff.reassess(self.root, self.contract, "ui-build", "Duplicate reopen")
        self.assertEqual(self.inspect(returned, decision)["gate"], "BLOCK")
        result = self.inspect(returned)
        self.assertTrue(self.inspect(returned, self.decision(returned, result))["accepted"])

    def test_active_revision_cannot_drop_required_findings_or_retire_unresolved_work(self):
        returned = self.output(self.start())
        finding = {"id": "denial", "required": True, "description": "Permission denial needs resolution", "status": "open"}
        returned["findings"] = [finding]
        self.assertEqual(self.inspect(returned)["gate"], "BLOCK")
        previous = self.revise(remove=True)
        with self.assertRaisesRegex(ValueError, "unresolved"):
            handoff.reconcile(self.root, self.contract, previous, "ui-build", "Remove specialist", retire=True)
        start = handoff.reconcile(self.root, self.contract, previous, "ui-build", "Resolve retained finding under revised scope", self.spec)
        returned = self.output(start)
        with self.assertRaisesRegex(ValueError, "required finding"):
            self.inspect(returned)
        returned["findings"] = [dict(finding, status="resolved", resolution_evidence_ids=returned["evidence_ids"])]
        self.assertTrue(self.inspect(returned, self.decision(returned, self.inspect(returned)))["accepted"])
        self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "PASS")

    def test_removed_accepted_assignment_retires_without_auto_accepting_new_task_evidence(self):
        returned = self.output(self.start())
        self.assertTrue(self.inspect(returned, self.decision(returned, self.inspect(returned)))["accepted"])
        previous = self.revise(remove=True)
        result = handoff.reconcile(self.root, self.contract, previous, "ui-build", "Accepted UI work superseded by revised scope", retire=True)
        self.assertEqual(result["action"], "retired")
        self.assertEqual(handoff.completion_failures(self.root, self.contract), [])
        self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "BLOCK")
        self.output(result)  # collect new task-bound evidence; historical return is not resubmitted
        self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "PASS")

    def test_unrecorded_revision_and_weakened_freshness_cannot_reopen(self):
        self.start()
        previous = copy.deepcopy(self.contract)
        self.contract["scope"].append("extra")
        with self.assertRaisesRegex(ValueError, "capture"):
            handoff.reconcile(self.root, self.contract, previous, "ui-build", "Unrecorded revision", self.spec)
        self.contract = previous
        previous = self.revise()
        self.spec["completion_binding"] = "stage-handoff"
        with self.assertRaisesRegex(ValueError, "freshness"):
            handoff.reconcile(self.root, self.contract, previous, "ui-build", "Reassess", self.spec)

    def test_valid_form_is_not_acceptance_then_real_head_decision_allows_done(self):
        start = self.start()
        returned = self.output(start)
        inspected = self.inspect(returned)
        self.assertEqual(inspected["gate"], "UNVERIFIED")
        light = manager.select_specialists("Correct label", ["src/view.tsx"], facts={"concern": ["ui"]},
                                            risk_facts={"operation": "tiny", "environment": "local", "data_sensitivity": "none", "change_boundary": "local"},
                                            guidance_evidence="Inspected the follow-up diff: mechanical label only, existing decisions preserved.",
                                            inspection_complete=True)
        self.assertFalse(light[0]["handoff_required"])
        # New lightweight routing never accepts/removes the retained formal work.
        self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "BLOCK")
        self.assertTrue(self.inspect(returned, self.decision(returned, inspected))["accepted"])
        self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "PASS")
        self.assertFalse(any((self.state / "active-assignments/ui-ux-skill").glob("*.json")))
        (self.root / "README.md").write_text("later unrelated document", encoding="utf-8")
        self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "PASS")
        (self.root / "src/value.txt").write_text("stale", encoding="utf-8")
        self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "BLOCK")

    def test_preexisting_dirty_source_and_outside_scope_need_explicit_reconciliation(self):
        (self.root / "preexisting.txt").write_text("user work", encoding="utf-8")
        start = self.start()
        returned = self.output(start)
        (self.root / "docs").mkdir()
        (self.root / "docs/usage.md").write_text("usage", encoding="utf-8")
        self.assertEqual(self.inspect(returned)["gate"], "BLOCK")
        returned["changed_surfaces"].append({"path": "docs/usage.md", "action": "add"})
        result = self.inspect(returned)
        self.assertNotIn("preexisting.txt", result["review"]["actual_changes"])
        decision = self.decision(returned, result)
        self.assertEqual(self.inspect(returned, decision)["gate"], "BLOCK")
        decision["scope_reconciliations"] = [{"path": "docs/usage.md", "reason": "Usage documentation is within retained product scope and existing Head authority."}]
        self.assertTrue(self.inspect(returned, decision)["accepted"])

    def test_required_finding_cannot_be_deleted_or_downgraded_and_conflicts_block(self):
        returned = self.output(self.start())
        returned["findings"] = [{"id": "denial", "required": True, "description": "Permission denial needs resolution", "status": "open"}]
        result = self.inspect(returned)
        self.assertEqual(result["gate"], "BLOCK")
        self.assertEqual(self.inspect(returned, self.decision(returned, result))["gate"], "BLOCK")
        for change in ([], [dict(returned["findings"][0], required=False)]):
            other = copy.deepcopy(returned)
            other["findings"] = change
            with self.assertRaises(ValueError):
                self.inspect(other)
        returned["findings"][0].update(status="resolved", resolution_evidence_ids=returned["evidence_ids"])
        returned["conflicts"] = ["Consumer contract not reconciled"]
        self.assertEqual(self.inspect(returned)["gate"], "BLOCK")
        returned["conflicts"] = []
        result = self.inspect(returned)
        self.assertTrue(self.inspect(returned, self.decision(returned, result))["accepted"])

    def test_platform_invariants_shared_contracts_and_plan_links_survive(self):
        self.contract["acceptance_criteria"][0]["behavior"] = {"user_action": "Open settings", "expected_result": "See stored value", "protected_invariants": ["Preserve tenant ownership"]}
        spec = copy.deepcopy(self.spec)
        spec["contract_sha256"] = behavior.digest(self.contract)
        with self.assertRaises(ValueError):
            self.start(spec)
        spec["protected_invariants"] = ["Preserve tenant ownership"]
        spec["shared_contracts"] = [{"id": "settings-api", "description": "Existing settings API response remains compatible with its consumer."}]
        returned = self.output(self.start(spec))
        returned["decisions"] = [{"description": "Retain API response", "criterion_ids": ["setting"], "contract_refs": ["settings-api"], "rationale": "UI consumes the unchanged response."}]
        returned["invariants"] = [{"description": "Preserve tenant ownership", "status": "preserved", "explanation": "Reviewed unchanged ownership path", "evidence_ids": returned["evidence_ids"]}]
        result = self.inspect(returned)
        decision = self.decision(returned, result)
        self.assertEqual(self.inspect(returned, decision)["gate"], "BLOCK")
        decision["contract_decisions"] = [{"id": "settings-api", "status": "compatible", "reason": "Compared the unchanged producer response with the UI consumer."}]
        self.assertTrue(self.inspect(returned, decision)["accepted"])
        plan = execution_plan.draft(self.root, self.contract["objective"], task_contract=self.contract, specialist_handoffs=[spec])
        self.assertEqual(execution_plan.validate_plan(plan, self.contract)["gate"], "PASS")
        plan["bound_specialist_assignments"] = []
        self.assertEqual(execution_plan.validate_plan(plan, self.contract)["gate"], "BLOCK")

    def test_revision_and_stage_mismatch_failed_receipt_and_missing_assignment_block(self):
        bad_contract = copy.deepcopy(self.contract)
        bad_contract["specialist_assignment_ids"] = ["ui-build", "ui-build"]
        with self.assertRaises(ValueError):
            behavior.validate(bad_contract)
        returned = self.output(self.start())
        for key, value in (("stage", "ship"), ("upstream_revision", "b" * 40), ("contract_sha256", "0" * 64)):
            changed = copy.deepcopy(returned)
            changed[key] = value
            with self.assertRaises(ValueError):
                self.inspect(changed)
        self.evidence[0]["receipt_sha256"] = "0" * 64
        self.assertEqual(self.inspect(returned)["gate"], "BLOCK")
        new = copy.deepcopy(self.contract)
        new["task_id"] = "no-ledger"
        report = self.report()
        report.update(task_id=new["task_id"], contract_sha256=behavior.digest(new))
        self.assertEqual(gate.evaluate(report, task_contract=new, root=self.root)["gate"], "BLOCK")

    def test_active_assignment_defers_upstream_replacement_and_renames_are_observed(self):
        start = self.start()
        self.source["commit"] = "b" * 40
        self.assertEqual(manager.ensure(self.entry, self.skills, self.state, True)["status"], "update-deferred-active-assignment")
        self.source["commit"] = "a" * 40
        returned = self.output(start)
        (self.root / "src/value.txt").rename(self.root / "src/renamed.txt")
        returned["changed_surfaces"] = [{"path": "src/renamed.txt", "previous_path": "src/value.txt", "action": "rename"}]
        # Old execution evidence is stale; the surface comparison still observes the rename correctly.
        result = self.inspect(returned)
        self.assertEqual(result["review"]["actual_changes"], {"src/value.txt": "delete", "src/renamed.txt": "add"})
        self.assertEqual(result["gate"], "BLOCK")

    def test_analysis_handoff_acceptance_is_historical_not_current_execution(self):
        spec = copy.deepcopy(self.spec)
        spec.update(stage="design", completion_binding="stage-handoff", evidence_requirement_ids=[])
        start = self.start(spec)
        returned = self.output(start)
        returned.update(changed_surfaces=[{"path": "src/value.txt", "action": "modify"}], evidence_ids=[])
        self.evidence = []
        result = self.inspect(returned)
        self.assertTrue(self.inspect(returned, self.decision(returned, result))["accepted"])
        (self.root / "src/value.txt").write_text("later build", encoding="utf-8")
        self.assertEqual(handoff.completion_failures(self.root, self.contract), [])

    def test_real_review_cli_reads_retained_context_and_records_acceptance(self):
        returned = self.output(self.start())
        result = self.inspect(returned)
        decision = self.decision(returned, result)
        for name, value in (("contract", self.contract), ("return", returned), ("evidence", self.evidence), ("decision", decision)):
            (self.base / (name + ".json")).write_text(json.dumps(value), encoding="utf-8")
        process = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts/specialist_handoff.py"), "review", "--root", str(self.root),
                                  "--task-contract", str(self.base / "contract.json"), "--assignment-id", "ui-build", "--return", str(self.base / "return.json"),
                                  "--evidence", str(self.base / "evidence.json"), "--decision", str(self.base / "decision.json")], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertTrue(json.loads(process.stdout)["accepted"])

    def test_new_file_baseline_is_supported_without_execution_claim(self):
        spec = copy.deepcopy(self.spec)
        spec.update(scope=["src/new.txt"], stage="design", completion_binding="stage-handoff", evidence_requirement_ids=[])
        start = self.start(spec)
        returned = self.output(start)
        (self.root / "src/value.txt").write_text("original", encoding="utf-8")
        (self.root / "src/new.txt").write_text("new design artifact", encoding="utf-8")
        returned.update(changed_surfaces=[{"path": "src/new.txt", "action": "add"}], evidence_ids=[])
        self.evidence = []
        inspected = self.inspect(returned)
        self.assertEqual(inspected["review"]["actual_changes"], {"src/new.txt": "add"})
        self.assertTrue(self.inspect(returned, self.decision(returned, inspected))["accepted"])

    def test_literal_routes_outside_assignment_do_not_block_git_observation(self):
        names = ["apps/web/[id]/page.tsx", "apps/web/[...slug]/page.tsx", "apps/web/[[...slug]]/page.tsx"]
        for name in names:
            path = self.root / name
            path.parent.mkdir(parents=True)
            path.write_text("original", encoding="utf-8")
        for args in (["add", "."], ["commit", "-qm", "literal web baseline"]):
            subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)
        self.start()  # The assigned src scope does not contain the web routes.
        _, operation = handoff.load_operation(self.root, self.contract, "ui-build")
        self.assertTrue(set(names) <= set(operation["baseline_tracked"]))
        (self.root / names[0]).unlink()
        (self.root / names[1]).write_text("changed", encoding="utf-8")
        added = "apps/web/[token]/page.tsx"
        (self.root / added).parent.mkdir()
        (self.root / added).write_text("untracked", encoding="utf-8")
        observed = handoff.observation(self.root, operation["assignment"], operation["baseline_commit"])
        self.assertTrue(observed[names[0]]["missing"])
        self.assertIn("sha256", observed[names[1]])
        self.assertIn("sha256", observed[added])

    def test_literal_route_handoff_executes_and_keeps_current_acceptance_fresh(self):
        route = "src/[id]/value.txt"
        (self.root / route).parent.mkdir()
        (self.root / "src/value.txt").rename(self.root / route)
        (self.root / "check.py").write_text("from pathlib import Path\nassert Path(" + repr(route) + ").read_text() == 'changed'\n", encoding="utf-8")
        for args in (["add", "."], ["commit", "-qm", "literal route baseline"]):
            subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)
        self.spec["scope"] = ["src/[id]"]
        start = self.start()
        (self.root / route).write_text("changed", encoding="utf-8")
        result = capture.capture(self.root, self.contract, "check", [sys.executable, "check.py"])
        r = result["receipt"]
        self.assertEqual(r["result"], "pass")
        self.evidence = [{"id": r["id"], "kind": r["kind"], "origin": r["origin"], "result": "pass", "required": True,
                          "requirement_id": "check", "receipt_ref": result["receipt_ref"], "receipt_sha256": result["receipt_sha256"]}]
        returned = {"format": "vibe-specialist-return", "schema_version": 1,
                    **{k: start["assignment"][k] for k in ("task_id", "assignment_id", "specialist_id", "stage", "contract_sha256")},
                    "upstream_revision": start["upstream_revision"], "head_contract_sha256": start["head_contract_sha256"],
                    "changed_surfaces": [{"path": route, "action": "modify"}], "decisions": [], "invariants": [],
                    "evidence_ids": [r["id"]], "findings": [], "unperformed_checks": [], "conflicts": [], "next_action": "Head verifies the route"}
        inspected = self.inspect(returned)
        self.assertEqual(inspected["review"]["actual_changes"], {route: "modify"})
        self.assertTrue(self.inspect(returned, self.decision(returned, inspected))["accepted"])
        self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "PASS")
        (self.root / route).write_text("stale", encoding="utf-8")
        self.assertEqual(gate.evaluate(self.report(), task_contract=self.contract, root=self.root)["gate"], "BLOCK")


if __name__ == "__main__":
    unittest.main()
