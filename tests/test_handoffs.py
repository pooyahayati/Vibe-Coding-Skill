"""S2 actual project changes, retained findings, receipt resolution and completion."""
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
        original = manager.ensure
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

    def test_valid_form_is_not_acceptance_then_real_head_decision_allows_done(self):
        start = self.start()
        returned = self.output(start)
        inspected = self.inspect(returned)
        self.assertEqual(inspected["gate"], "UNVERIFIED")
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
