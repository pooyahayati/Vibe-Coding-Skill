"""B2 behavior identity, retained outcomes and real local CLI propagation."""
from __future__ import annotations
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import behavior_contract as behavior
import execution_plan
import project_state


def contract(tier=0):
    return {"format": "vibe-task-contract", "schema_version": 1, "task_id": "settings-label",
            "objective": "Correct a typo", "scope": ["settings.txt"], "risk_tier": tier,
            "acceptance_criteria": [{"id": "label", "description": "The supplied label is shown without changing the setting",
                "required": True, "behavior": {"user_action": "Open settings", "expected_result": "See the supplied label",
                    "protected_invariants": ["Stored setting unchanged"]}}],
            "evidence_requirements": [{"id": "view", "criterion_ids": ["label"], "kind": "visual-check", "origin": "manual", "required": True}]}


class BehaviorContractTests(unittest.TestCase):
    def test_contract_rejects_invalid_identity_behavior_and_requirement_links(self):
        original = contract()
        variants = [dict(original, schema_version=True), dict(original, risk_tier=True)]
        for field, value in [("id", ""), ("behavior", {"user_action": "Open settings"})]:
            item = copy.deepcopy(original)
            item["acceptance_criteria"][0][field] = value
            variants.append(item)
        for field, value in [("criterion_ids", ["unknown"]), ("origin", []), ("required", False)]:
            item = copy.deepcopy(original)
            item["evidence_requirements"][0][field] = value
            variants.append(item)
        for item in variants:
            with self.subTest(item=item), self.assertRaises(ValueError):
                behavior.validate(item)
        self.assertEqual(behavior.digest(original), behavior.digest(json.loads(json.dumps(original))))

    def test_light_plan_preserves_ids_and_floor_without_forcing_new_plan(self):
        with tempfile.TemporaryDirectory() as td:
            bound = execution_plan.draft(Path(td), "Correct a typo", task_contract=contract())
            self.assertFalse(bound["execution_plan_required"])
            self.assertEqual(bound["task_contract"], contract())
            self.assertEqual(bound["workstreams"][0]["criterion_ids"], ["label"])
            self.assertEqual(execution_plan.validate_plan(bound, contract())["gate"], "PASS")
            high = execution_plan.draft(Path(td), "Correct a typo", task_contract=contract(2))
            self.assertTrue(high["execution_plan_required"])
            self.assertEqual(high["planning_basis"]["risk_tier"], 2)
            self.assertEqual(high["risk_policy"]["tier"], 2)
            legacy = execution_plan.draft(Path(td), "Correct a typo")
            self.assertNotIn("task_contract", legacy)
            self.assertFalse(execution_plan.validate_plan(legacy)["task_contract_checked"])

    def test_plan_blocks_required_outcome_drift_and_removed_binding(self):
        with tempfile.TemporaryDirectory() as td:
            original = execution_plan.draft(Path(td), "Correct a typo", task_contract=contract())
        variants = []
        for field, value in [("description", "Different behavior"), ("required", False),
                             ("behavior", {"user_action": "Open settings", "expected_result": "Different result"})]:
            altered = copy.deepcopy(original)
            altered["task_contract"]["acceptance_criteria"][0][field] = value
            altered["task_contract_sha256"] = behavior.digest(altered["task_contract"])
            variants.append(altered)
        missing = copy.deepcopy(original)
        missing.pop("task_contract")
        missing.pop("task_contract_sha256")
        variants.append(missing)
        for key in ("criterion_ids", "evidence_requirement_ids"):
            altered = copy.deepcopy(original)
            altered["workstreams"][0][key] = []
            variants.append(altered)
        for altered in variants:
            with self.subTest(altered=altered):
                self.assertEqual(execution_plan.validate_plan(altered, contract())["gate"], "BLOCK")

    def test_reported_outcomes_never_become_receipt_verified(self):
        c = contract()
        self.assertEqual(behavior.completion(c, None)["outcomes"][0]["status"], "unverified")
        report = {"schema_version": 2, "status": "Done", "risk_tier": 0, "blockers": [],
                  "acceptance_criteria": [dict(copy.deepcopy(c["acceptance_criteria"][0]), met=True, evidence_ids=["observed"])],
                  "evidence": [{"id": "observed", "kind": "visual-check", "required": True, "result": "pass"}]}
        result = behavior.completion(c, report)
        self.assertEqual(result["outcomes"][0]["status"], "reported-met")
        self.assertIn("not verified", result["reason"])
        self.assertEqual(behavior.completion(c, report, stale=True)["outcomes"][0]["status"], "unverified")
        report["acceptance_criteria"][0]["behavior"]["protected_invariants"] = []
        self.assertEqual(behavior.completion(c, report)["gate"], "BLOCK")
        report["acceptance_criteria"][0]["met"] = False
        self.assertEqual(behavior.completion(c, report)["outcomes"][0]["status"], "unmet")

    def test_cli_capture_handoff_resume_preserve_contract_and_stale_result(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "product"
            root.mkdir()
            env = dict(os.environ, VIBE_CODING_HOME=str(base / "local"), PYTHONDONTWRITEBYTECODE="1")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "settings.txt").write_text("new label", encoding="utf-8")
            subprocess.run(["git", "add", "settings.txt"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=B2 Test", "-c", "user.email=b2-test@example.invalid",
                            "commit", "-qm", "fixture"], cwd=root, check=True)
            c_path = base / "contract.json"
            accepted = contract()
            accepted["acceptance_criteria"][0]["behavior"]["user_action"] = "باز کردن تنظیمات"
            c_path.write_text(json.dumps(accepted), encoding="utf-8")
            def cli(script, *args, expected=0):
                p = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts" / script), *args], env=env, text=True, encoding="utf-8", capture_output=True)
                self.assertEqual(p.returncode, expected, p.stdout + p.stderr)
                return json.loads(p.stdout)
            plan = cli("execution_plan.py", "draft", "--root", str(root), "--task-contract", str(c_path), "--json")
            self.assertEqual(plan["task_contract"]["acceptance_criteria"][0]["id"], "label")
            first = cli("project_state.py", "capture", "--root", str(root), "--task-contract", str(c_path), "--json")
            snapshot = Path(first["state_path"])
            before = snapshot.read_bytes()
            changed = contract()
            changed["acceptance_criteria"][0]["behavior"]["user_action"] = "باز کردن تنظیمات"
            changed["acceptance_criteria"][0]["behavior"]["protected_invariants"] = ["Different invariant"]
            c_path.write_text(json.dumps(changed), encoding="utf-8")
            cli("project_state.py", "capture", "--root", str(root), "--task-contract", str(c_path), "--json", expected=2)
            self.assertEqual(before, snapshot.read_bytes())
            report = {"schema_version": 2, "status": "Done", "risk_tier": 0,
                      "acceptance_criteria": [dict(accepted["acceptance_criteria"][0], met=True, evidence_ids=["view"])],
                      "evidence": [{"id": "view", "kind": "visual-check", "required": True, "result": "pass"}]}
            r_path = base / "report.json"
            r_path.write_text(json.dumps(report), encoding="utf-8")
            done = cli("project_state.py", "handoff", "--root", str(root), "--completion-report", str(r_path),
                       "--how-to-use", "Open settings", "--how-to-check", "Inspect the supplied label", "--next-action", "Review the change", "--write-local", "--json")
            self.assertIn("reported-met", done["markdown"])
            self.assertIn("Stored setting unchanged", done["markdown"])
            self.assertIn("باز کردن تنظیمات", done["markdown"])
            self.assertIn("How to use: Open settings", done["markdown"])
            (root / "settings.txt").write_text("another label", encoding="utf-8")
            resumed = cli("resume_context.py", "--root", str(root), "--json")
            self.assertEqual(resumed["local_state"]["project_state"]["acceptance"]["gate"], "UNVERIFIED")
            for _ in range(2):
                state = cli("project_state.py", "capture", "--root", str(root), "--json")
                self.assertEqual(state["acceptance"]["outcomes"][0]["status"], "unverified")
            self.assertFalse((root / "handoff.md").exists())
            self.assertEqual(sorted(p.name for p in root.iterdir()), [".git", "settings.txt"])
            changed["risk_tier"] = 2
            c_path.write_text(json.dumps(changed), encoding="utf-8")
            reconciled = cli("project_state.py", "capture", "--root", str(root), "--task-contract", str(c_path),
                             "--accept-contract-change", "Head accepted the changed protected outcome", "--json")
            self.assertEqual(reconciled["contract_reconciliation"]["previous_sha256"], behavior.digest(accepted))
            self.assertFalse(reconciled["contract_reconciliation"]["authorization_verified"])
            self.assertEqual(reconciled["acceptance"]["gate"], "UNVERIFIED")
            changed["risk_tier"] = 0
            c_path.write_text(json.dumps(changed), encoding="utf-8")
            before = snapshot.read_bytes()
            cli("project_state.py", "capture", "--root", str(root), "--task-contract", str(c_path),
                "--accept-contract-change", "Attempt to lower the known floor", "--json", expected=2)
            self.assertEqual(before, snapshot.read_bytes())

    def test_cross_boundary_contract_keeps_outcomes_with_separate_owners(self):
        c = contract(2)
        c["scope"] = ["web", "api"]
        c["acceptance_criteria"].append({"id": "data", "description": "Stored value is unchanged", "required": True})
        c["evidence_requirements"].append({"id": "stored", "criterion_ids": ["data"], "kind": "integration", "origin": "reported", "required": True})
        with tempfile.TemporaryDirectory() as td:
            p = execution_plan.draft(Path(td), c["objective"], task_contract=c)
        original = p["workstreams"][0]
        p["workstreams"] = [dict(original, id="web", owner="ui-owner", scope=["web"], criterion_ids=["label"], evidence_requirement_ids=["view"]),
                            dict(original, id="api", owner="api-owner", scope=["api"], criterion_ids=["data"], evidence_requirement_ids=["stored"])]
        for boundary in p["integration_points"]:
            boundary.update(contract="Preserve the existing setting response", status="confirmed", producers=["api"], consumers=["web"])
        self.assertTrue(p["execution_plan_required"])
        self.assertEqual(execution_plan.validate_plan(p, c)["gate"], "PASS")
        p["workstreams"][1]["criterion_ids"] = []
        self.assertEqual(execution_plan.validate_plan(p, c)["gate"], "BLOCK")


if __name__ == "__main__":
    unittest.main()
