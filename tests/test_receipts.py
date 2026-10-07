"""E2 qualifying execution/manual evidence and retained schema migration."""
from __future__ import annotations
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import behavior_contract as behavior
import completion_gate as gate
import evidence_capture as capture
import receipt_validation as receipts
import project_state
from test_cross_platform import receipt_contract


class ReceiptCompletionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "product"
        (self.root / "src/generated").mkdir(parents=True)
        (self.root / "src/value.txt").write_text("accepted", encoding="utf-8")
        (self.root / "check.py").write_text("assert True", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        for args in (["config", "user.name", "Test"], ["config", "user.email", "test@example.invalid"], ["add", "."], ["commit", "-qm", "baseline"]):
            subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)
        env = patch.dict(os.environ, {"VIBE_CODING_HOME": str(self.root.parent / "state"), "PYTHONDONTWRITEBYTECODE": "1"})
        env.start()
        self.addCleanup(env.stop)
        self.c = receipt_contract()
        self.r = capture.capture(self.root, self.c, "check", [sys.executable, "check.py"])
        row = dict(copy.deepcopy(self.c["acceptance_criteria"][0]), met=True, evidence_ids=[self.r["receipt"]["id"]])
        self.report = {"schema_version": 3, "task_id": self.c["task_id"], "contract_sha256": behavior.digest(self.c),
            "status": "Done", "risk_tier": 1, "blockers": [], "acceptance_criteria": [row],
            "evidence": [{"id": self.r["receipt"]["id"], "kind": "unit-test", "origin": "collected", "result": "pass", "required": True,
                          "requirement_id": "check", "receipt_ref": self.r["receipt_ref"], "receipt_sha256": self.r["receipt_sha256"]}]}

    def evaluate(self, report=None, contract=None, **options):
        return gate.evaluate(report or self.report, task_contract=contract or self.c, root=self.root, **options)

    def test_workspace_and_receipts_survive_remote_changes_and_legacy_adoption(self):
        import local_workspace as workspace
        import resume_context
        from test_cross_platform import git
        saved = project_state.capture(self.root, task_contract=self.c, completion_report=self.report)
        identity = workspace.project_id(self.root)
        for url in ("https://example.invalid/owner/product.git", "git@example.invalid:owner/product.git"):
            git(self.root, "remote", "remove", "origin") if workspace.git_origin(self.root) else None
            git(self.root, "remote", "add", "origin", url)
            self.assertEqual(workspace.project_id(self.root), identity)
            self.assertEqual(project_state.load_previous(self.root)["task_contract"], self.c)
            self.assertTrue(resume_context.build_context(self.root)["local_state"]["project_state"]["acceptance"]["receipt_verified"])
        # Simulate the legacy origin-derived folder before collecting new evidence.
        path = workspace.project_workspace(self.root)
        legacy = path.with_name("product-0123456789abcdef")
        path.rename(legacy)
        metadata = json.loads((legacy / "metadata.json").read_text())
        metadata["project_id"] = legacy.name
        (legacy / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
        self.assertEqual(workspace.project_id(self.root), legacy.name)
        receipt = capture.capture(self.root, self.c, "check", [sys.executable, "check.py"])
        git(self.root, "remote", "set-url", "origin", "https://example.invalid/renamed/product.git")
        row = dict(self.report["evidence"][0], id=receipt["receipt"]["id"], receipt_ref=receipt["receipt_ref"], receipt_sha256=receipt["receipt_sha256"])
        self.assertTrue(receipts.validate(receipt["receipt"], row, self.c, self.c["evidence_requirements"][0], self.root, {})["qualified"])
        self.assertEqual(project_state.load_previous(self.root)["task_contract"], saved["task_contract"])

    def test_same_name_projects_are_isolated_and_ambiguous_legacy_state_blocks(self):
        import local_workspace as workspace
        other = self.root.parent / "other/product"
        other.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(other)], check=True)
        self.assertNotEqual(workspace.project_workspace(other, create=True), workspace.project_workspace(self.root))
        duplicate = workspace.project_workspace(self.root).with_name("product-duplicate")
        duplicate.mkdir()
        (duplicate / "metadata.json").write_text(json.dumps({"project_root": str(self.root), "project_id": duplicate.name}), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "ambiguous"):
            project_state.load_previous(self.root)

    def test_recovery_restores_contract_and_rechecks_current_receipts(self):
        import state_recovery
        import resume_context
        saved = project_state.capture(self.root, task_contract=self.c, completion_report=self.report)
        project_state.state_path(self.root).write_text("{broken", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            resume_context.build_context(self.root)
        restored = state_recovery.repair(self.root, True)
        self.assertEqual(restored["status"], "PASS")
        state = project_state.load_previous(self.root)
        self.assertEqual(state["task_contract"], saved["task_contract"])
        self.assertEqual(state["completion_schema"], 3)
        (self.root / "src/value.txt").write_text("stale", encoding="utf-8")
        self.assertFalse(resume_context.build_context(self.root)["local_state"]["project_state"]["acceptance"]["receipt_verified"])

    def test_interrupted_capture_keeps_new_obligations_and_unknown_loss_blocks(self):
        import local_workspace as workspace
        import state_recovery
        import resume_context
        project_state.capture(self.root, task_contract=self.c)
        revised = dict(copy.deepcopy(self.c), specialist_assignment_ids=["mandatory-review"])
        original = workspace.atomic_json
        def interrupted(path, value):
            if path.name == "project-state.json":
                raise OSError("injected interruption")
            return original(path, value)
        with patch.object(workspace, "atomic_json", side_effect=interrupted):
            with self.assertRaises(OSError):
                project_state.capture(self.root, task_contract=revised)
        with self.assertRaises(RuntimeError):
            project_state.load_previous(self.root)
        self.assertEqual(state_recovery.repair(self.root, True)["status"], "PASS")
        self.assertEqual(project_state.load_previous(self.root)["task_contract"], revised)
        project_state.backup_path(self.root).unlink()
        project_state.state_path(self.root).write_text("{broken", encoding="utf-8")
        self.assertEqual(state_recovery.repair(self.root, True)["status"], "BLOCK")
        for action in (lambda: resume_context.build_context(self.root), lambda: project_state.capture(self.root, task_contract=self.c)):
            with self.assertRaises(RuntimeError):
                action()
        restored = project_state.capture(self.root, task_contract=revised, reconcile_recovery="Reconstructed from independently verified approved scope")
        self.assertEqual(restored["task_contract"]["specialist_assignment_ids"], ["mandatory-review"])
        self.assertEqual(restored["completion_schema"], 3)
        self.assertFalse(restored["acceptance"].get("receipt_verified", False))

    def test_atomic_replacement_failure_does_not_truncate_valid_state(self):
        import local_workspace as workspace
        path = self.root.parent / "atomic.json"
        workspace.atomic_json(path, {"required": "original"})
        with patch.object(workspace.os, "replace", side_effect=OSError("interrupted replace")):
            with self.assertRaises(OSError):
                workspace.atomic_json(path, {"required": "replacement"})
        self.assertEqual(json.loads(path.read_text()), {"required": "original"})
        self.assertEqual(list(path.parent.glob("atomic.json.*.tmp")), [])

    def test_missing_primary_and_partial_json_restore_without_dropping_risk_floor(self):
        import state_recovery
        import local_workspace as workspace
        project_state.capture(self.root, task_contract=self.c)
        project_state.state_path(self.root).unlink()
        with self.assertRaises(RuntimeError):
            project_state.load_previous(self.root)
        self.assertEqual(state_recovery.repair(self.root, True)["status"], "PASS")
        # Syntactically valid but incomplete JSON is not an accepted baseline.
        project_state.state_path(self.root).write_text("{}", encoding="utf-8")
        self.assertEqual(state_recovery.repair(self.root, True)["status"], "PASS")
        self.assertEqual(project_state.load_previous(self.root)["task_contract"], self.c)
        workspace.atomic_json(project_state.recovery_path(self.root), {"recovery_required": True})
        weaker = dict(copy.deepcopy(self.c), risk_tier=0)
        with self.assertRaises(ValueError):
            project_state.capture(self.root, task_contract=weaker, reconcile_recovery="Cannot bypass a recoverable baseline")
        self.assertTrue(project_state.recovery_path(self.root).exists())

    def test_actual_receipt_pass_reuse_excluded_output_and_source_staleness(self):
        result = self.evaluate()
        self.assertEqual(result["gate"], "PASS", result)
        self.assertTrue(result["receipt_verified"])
        (self.root / "README.md").write_text("unrelated documentation", encoding="utf-8")
        (self.root / "src/generated/log.txt").write_text("generated", encoding="utf-8")
        self.assertEqual(self.evaluate()["gate"], "PASS")
        (self.root / "src/new.txt").write_text("new source", encoding="utf-8")
        self.assertEqual(self.evaluate()["gate"], "BLOCK")

    def test_literal_route_execution_receipt_and_bracket_reference_remain_bound(self):
        name = "src/[id]/page.tsx"
        path = self.root / name
        path.parent.mkdir()
        path.write_text("accepted", encoding="utf-8")
        self.c["evidence_requirements"][0].update(input_paths=[name], input_excludes=[], artifact_paths=[name])
        self.r = capture.capture(self.root, self.c, "check", [sys.executable, "-c",
            "from pathlib import Path; assert Path('page.tsx').read_text() == 'accepted'"], cwd=path.parent)
        self.assertEqual(self.r["receipt"]["result"], "pass")
        self.assertTrue(self.r["receipt"]["process_started"])
        receipt_path = Path(self.r["receipt_path"])
        reference = "execution[id].json"
        receipt_path.rename(receipt_path.with_name(reference))
        self.report["contract_sha256"] = behavior.digest(self.c)
        self.report["evidence"][0].update(id=self.r["receipt"]["id"], receipt_ref=reference, receipt_sha256=self.r["receipt_sha256"])
        self.report["acceptance_criteria"][0]["evidence_ids"] = [self.r["receipt"]["id"]]
        self.assertEqual(self.evaluate()["gate"], "PASS")
        path.write_text("stale", encoding="utf-8")
        self.assertEqual(self.evaluate()["gate"], "BLOCK")

    def test_failed_missing_altered_escaping_and_cross_task_receipts_block(self):
        for change in ({"receipt_ref": "../outside.json"}, {"receipt_ref": "missing.json"},
                       {"receipt_sha256": "0" * 64}, {"origin": "manual"}, {"requirement_id": "other"}):
            report = copy.deepcopy(self.report)
            report["evidence"][0].update(change)
            self.assertEqual(self.evaluate(report)["gate"], "BLOCK")
        path = Path(self.r["receipt_path"])
        for field, value in (("result", "fail"), ("task_id", "other"), ("process_started", False),
                             ("artifacts", {}), ("command", dict(self.r["receipt"]["command"], shell=True))):
            record = copy.deepcopy(self.r["receipt"])
            record[field] = value
            path.write_text(json.dumps(record), encoding="utf-8")
            report = copy.deepcopy(self.report)
            report["evidence"][0]["receipt_sha256"] = behavior.digest(record)
            self.assertEqual(self.evaluate(report)["gate"], "BLOCK")

    def test_bound_report_rejects_legacy_downgrade_and_changed_required_behavior(self):
        old = copy.deepcopy(self.report)
        old["schema_version"] = 2
        self.assertEqual(self.evaluate(old)["gate"], "BLOCK")
        # Unbound in-flight version 2 remains the declared-evidence route.
        old["risk_tier"] = 0
        self.assertFalse(gate.evaluate(old)["receipt_verified"])
        for key, value in (("description", "Different outcome"), ("required", False)):
            changed = copy.deepcopy(self.report)
            changed["acceptance_criteria"][0][key] = value
            self.assertEqual(self.evaluate(changed)["gate"], "BLOCK")
        self.assertEqual(self.evaluate(context={"dataset": "changed"})["gate"], "BLOCK")

    def test_artifact_mutation_and_narrowed_input_scope_block(self):
        artifact = self.root.parent / "package.zip"
        artifact.write_bytes(b"actual artifact")
        c = copy.deepcopy(self.c)
        c["evidence_requirements"][0]["artifact_paths"] = [str(artifact)]
        r = capture.capture(self.root, c, "check", [sys.executable, "check.py"])
        report = copy.deepcopy(self.report)
        report["contract_sha256"] = behavior.digest(c)
        report["evidence"][0].update(id=r["receipt"]["id"], receipt_ref=r["receipt_ref"], receipt_sha256=r["receipt_sha256"])
        report["acceptance_criteria"][0]["evidence_ids"] = [r["receipt"]["id"]]
        self.assertEqual(self.evaluate(report, c)["gate"], "PASS")
        artifact.write_bytes(b"different")
        self.assertEqual(self.evaluate(report, c)["gate"], "BLOCK")
        record = copy.deepcopy(self.r["receipt"])
        record["inputs"]["paths"] = ["check.py"]
        Path(self.r["receipt_path"]).write_text(json.dumps(record), encoding="utf-8")
        report = copy.deepcopy(self.report)
        report["evidence"][0]["receipt_sha256"] = behavior.digest(record)
        self.assertEqual(self.evaluate(report)["gate"], "BLOCK")

    def test_manual_observation_is_supported_without_fabricating_execution(self):
        c = copy.deepcopy(self.c)
        c["evidence_requirements"][0].update(origin="manual", kind="visual-check")
        r = receipts.observe(self.root, c, "check", {"description": "Inspected settings and observed stored value preserved", "method": "rendered inspection", "environment": "test browser"})
        report = copy.deepcopy(self.report)
        report["contract_sha256"] = behavior.digest(c)
        report["evidence"][0].update(id=r["receipt"]["id"], kind="visual-check", origin="manual", receipt_ref=r["receipt_ref"], receipt_sha256=r["receipt_sha256"])
        report["acceptance_criteria"][0]["evidence_ids"] = [r["receipt"]["id"]]
        self.assertEqual(self.evaluate(report, c)["gate"], "PASS")
        result = behavior.completion(c, report, root=self.root, expected_schema=3)
        self.assertTrue(result["receipt_verified"])
        self.assertFalse(result["execution_verified"])
        self.assertEqual(result["outcomes"][0]["status"], "receipt-qualified")
        with self.assertRaises(ValueError):
            receipts.observe(self.root, self.c, "check", {"description": "pass"})
        c["evidence_requirements"][0]["unsupported_policy"] = True
        report["contract_sha256"] = behavior.digest(c)
        record = copy.deepcopy(r["receipt"])
        record["contract_sha256"] = report["contract_sha256"]
        Path(r["receipt_path"]).write_text(json.dumps(record), encoding="utf-8")
        report["evidence"][0]["receipt_sha256"] = behavior.digest(record)
        self.assertEqual(self.evaluate(report, c)["gate"], "BLOCK")
        with self.assertRaises(ValueError):
            receipts.observe(self.root, c, "check", record["observation"])

    def test_state_activation_survives_resume_and_downgrade_is_blocked(self):
        state = project_state.capture(self.root, task_contract=self.c, receipt_completion=True, completion_report=self.report)
        self.assertEqual(state["completion_schema"], 3)
        self.assertTrue(state["acceptance"]["execution_verified"])
        old = copy.deepcopy(self.report)
        old["schema_version"] = 2
        state = project_state.capture(self.root, completion_report=old)
        self.assertEqual(state["acceptance"]["gate"], "BLOCK")
        self.assertEqual(state["completion_schema"], 3)

    def test_fresh_structured_state_defaults_to_receipts_through_handoff_and_resume(self):
        import resume_context
        # The caller omits activation, exactly as in the reported new-task gap.
        old = copy.deepcopy(self.report)
        old["schema_version"] = 2
        state = project_state.capture(self.root, task_contract=self.c, completion_report=old)
        self.assertEqual(state["completion_schema"], 3)
        self.assertEqual(state["acceptance"]["gate"], "BLOCK")
        state = project_state.handoff(self.root, True, completion_report=self.report)["state"]
        self.assertTrue(state["acceptance"]["execution_verified"])
        resumed = resume_context.build_context(self.root)["local_state"]["project_state"]
        self.assertEqual(resumed["completion_schema"], 3)
        self.assertTrue(resumed["acceptance"]["receipt_verified"])

    def test_retained_legacy_is_supported_but_new_tasks_do_not_inherit_it(self):
        import resume_context
        # Model an actual pre-receipt snapshot, not a flag allowing fresh tasks
        # to opt out. Older B2 snapshots have no completion_schema field.
        saved = project_state.capture(self.root, task_contract=self.c)
        for legacy_schema in (None, 2):
            with self.subTest(legacy_schema=legacy_schema):
                legacy = copy.deepcopy(saved)
                legacy.pop("completion_schema")
                if legacy_schema is not None:
                    legacy["completion_schema"] = legacy_schema
                project_state.state_path(self.root).write_text(json.dumps(legacy), encoding="utf-8")
                project_state.backup_path(self.root).unlink(missing_ok=True)  # pre-A1 state had no retained copy
                old = copy.deepcopy(self.report)
                old["schema_version"] = 2
                old["evidence"][0]["provenance"] = {"source": "local fixture observation", "reference": self.r["receipt_path"]}
                state = project_state.capture(self.root, completion_report=old)
                self.assertEqual(state["completion_schema"], 2)
                self.assertEqual(state["acceptance"]["gate"], "PASS")
                self.assertFalse(state["acceptance"]["execution_verified"])
                self.assertEqual(state["acceptance"]["outcomes"][0]["status"], "reported-met")
                resumed = resume_context.build_context(self.root)["local_state"]["project_state"]
                self.assertEqual(resumed["completion_schema"], 2)
                migrated = project_state.capture(self.root, receipt_completion=True, completion_report=self.report)
                self.assertTrue(migrated["acceptance"]["execution_verified"])
                self.assertEqual(project_state.capture(self.root, completion_report=old)["acceptance"]["gate"], "BLOCK")
                project_state.state_path(self.root).write_text(json.dumps(legacy), encoding="utf-8")
                project_state.backup_path(self.root).unlink(missing_ok=True)
                replacement = dict(copy.deepcopy(self.c), task_id="next-task")
                next_state = project_state.capture(self.root, task_contract=replacement, new_task=True, completion_report=old)
                self.assertEqual(next_state["completion_schema"], 3)
                self.assertEqual(next_state["acceptance"]["gate"], "BLOCK")
        # A project-only snapshot is not evidence of an in-flight legacy task.
        project_only = {k: v for k, v in saved.items() if k not in ("task_contract", "task_contract_sha256", "acceptance")}
        project_only["completion_schema"] = 2
        project_state.state_path(self.root).write_text(json.dumps(project_only), encoding="utf-8")
        project_state.backup_path(self.root).unlink(missing_ok=True)
        self.assertEqual(project_state.capture(self.root, task_contract=self.c)["completion_schema"], 3)

    def test_unstarted_required_specialist_survives_state_and_explicit_reconciliation(self):
        import resume_context
        import specialist_handoff
        c = dict(copy.deepcopy(self.c), specialist_assignment_ids=["security-review"])
        state = project_state.capture(self.root, task_contract=c)
        snapshot = project_state.state_path(self.root)
        before = snapshot.read_bytes()
        for ids in (None, [], ["replacement-review"]):
            changed = copy.deepcopy(c)
            changed.pop("specialist_assignment_ids")
            if ids is not None:
                changed["specialist_assignment_ids"] = ids
            with self.subTest(ids=ids), self.assertRaisesRegex(ValueError, "required specialist assignment"):
                project_state.capture(self.root, task_contract=changed)
            self.assertEqual(snapshot.read_bytes(), before)
        transferred = project_state.handoff(self.root, True)
        self.assertEqual(transferred["state"]["task_contract"]["specialist_assignment_ids"], ["security-review"])
        self.assertIn("security-review", transferred["markdown"])
        resumed = resume_context.build_context(self.root)["local_state"]["project_state"]
        self.assertEqual(resumed["task_contract"]["specialist_assignment_ids"], ["security-review"])
        self.assertIn("required specialist assignment missing: security-review",
                      specialist_handoff.completion_failures(self.root, c))
        r = capture.capture(self.root, c, "check", [sys.executable, "check.py"])
        pending_report = copy.deepcopy(self.report)
        pending_report["contract_sha256"] = behavior.digest(c)
        pending_report["acceptance_criteria"][0]["evidence_ids"] = [r["receipt"]["id"]]
        pending_report["evidence"][0].update(id=r["receipt"]["id"], receipt_ref=r["receipt_ref"], receipt_sha256=r["receipt_sha256"])
        blocked = project_state.capture(self.root, completion_report=pending_report)
        self.assertEqual(blocked["acceptance"]["gate"], "BLOCK")
        self.assertTrue(any("security-review" in failure for failure in blocked["acceptance"]["failures"]))
        changed = copy.deepcopy(c)
        changed.pop("specialist_assignment_ids")
        reconciled = project_state.capture(self.root, task_contract=changed,
            accept_contract_change="Head removed the unstarted review after reconciling scope")
        self.assertEqual(reconciled["contract_reconciliation"]["previous_contract"], c)
        self.assertFalse(reconciled["contract_reconciliation"]["authorization_verified"])
        self.assertEqual(reconciled["acceptance"]["gate"], "BLOCK")
        # A pre-reconciliation receipt cannot qualify against the new digest.
        self.assertEqual(project_state.capture(self.root, completion_report=pending_report)["acceptance"]["gate"], "BLOCK")

    def test_high_risk_requires_all_obligations_and_distinct_families(self):
        c = copy.deepcopy(self.c)
        c["risk_tier"] = 2
        c["evidence_requirements"].append({"id": "review", "criterion_ids": ["setting"], "kind": "code-review", "origin": "manual", "required": True})
        first = capture.capture(self.root, c, "check", [sys.executable, "check.py"])
        second = receipts.observe(self.root, c, "review", {"description": "Reviewed the changed setting and denial behavior", "method": "source review", "environment": "local test checkout"})
        report = copy.deepcopy(self.report)
        report.update(risk_tier=2, commit=capture.local_workspace.run_git(self.root, "rev-parse", "HEAD")[1], contract_sha256=behavior.digest(c))
        report["evidence"] = []
        for result in (first, second):
            r = result["receipt"]
            report["evidence"].append({"id": r["id"], "kind": r["kind"], "origin": r["origin"], "result": r["result"], "required": True,
                                      "requirement_id": r["requirement_id"], "receipt_ref": result["receipt_ref"], "receipt_sha256": result["receipt_sha256"]})
        report["acceptance_criteria"][0]["evidence_ids"] = [first["receipt"]["id"], second["receipt"]["id"]]
        self.assertEqual(self.evaluate(report, c)["gate"], "PASS")
        report["evidence"].pop()
        self.assertEqual(self.evaluate(report, c)["gate"], "BLOCK")

    def test_reported_claim_stays_unverified_and_non_done_needs_no_receipt(self):
        c = copy.deepcopy(self.c)
        c["evidence_requirements"][0]["origin"] = "reported"
        record = copy.deepcopy(self.r["receipt"])
        record.update(origin="reported", contract_sha256=behavior.digest(c), provenance={"resolution": "verified"})
        Path(self.r["receipt_path"]).write_text(json.dumps(record), encoding="utf-8")
        report = copy.deepcopy(self.report)
        report["contract_sha256"] = behavior.digest(c)
        report["evidence"][0].update(origin="reported", receipt_sha256=behavior.digest(record))
        self.assertEqual(self.evaluate(report, c)["gate"], "BLOCK")
        report.update(status="Unverified", acceptance_criteria=[], evidence=[])
        result = self.evaluate(report, c)
        self.assertEqual(result["gate"], "PASS")
        self.assertFalse(result["receipt_verified"])

    def test_gate_cli_and_resume_use_current_scoped_receipt_validation(self):
        import resume_context
        state = project_state.capture(self.root, task_contract=self.c, receipt_completion=True, completion_report=self.report)
        self.assertTrue(state["acceptance"]["receipt_verified"])
        resumed = resume_context.build_context(self.root)
        self.assertTrue(resumed["local_state"]["project_state"]["acceptance"]["receipt_verified"])
        (self.root / "src/value.txt").write_text("changed", encoding="utf-8")
        self.assertFalse(resume_context.build_context(self.root)["local_state"]["project_state"]["acceptance"]["receipt_verified"])
        base = self.root.parent
        report = base / "report.json"
        contract = base / "contract.json"
        report.write_text(json.dumps(self.report), encoding="utf-8")
        contract.write_text(json.dumps(self.c), encoding="utf-8")
        process = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts/completion_gate.py"), str(report),
                                  "--task-contract", str(contract), "--root", str(self.root), "--json"], text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(process.returncode, 2, process.stdout + process.stderr)
        self.assertEqual(json.loads(process.stdout)["gate"], "BLOCK")


if __name__ == "__main__":
    unittest.main()
