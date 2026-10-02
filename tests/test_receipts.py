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
