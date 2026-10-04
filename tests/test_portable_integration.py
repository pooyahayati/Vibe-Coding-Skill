"""I1: exercise representative routes from an extracted, install-checked ZIP."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PortableIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix="vibe-i1-package-")
        cls.addClassCleanup(temporary.cleanup)
        cls.base = Path(temporary.name).resolve()
        cls.package_env = dict(os.environ, VIBE_CODING_HOME=str(cls.base / "package-state"),
                               PYTHONDONTWRITEBYTECODE="1", PYTHONPATH="")
        process = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts/build_release.py"),
                                  "--output-dir", str(cls.base / "artifacts"), "--json"],
                                 cwd=cls.base, env=cls.package_env, capture_output=True, text=True,
                                 encoding="utf-8", timeout=180)
        if process.returncode:
            raise AssertionError(process.stdout + process.stderr)
        cls.build = json.loads(process.stdout[process.stdout.index("{"):])
        if cls.build["installation_status"] not in {"PASS", "WARN"}:
            raise AssertionError(cls.build)
        with zipfile.ZipFile(cls.base / "artifacts" / cls.build["archive"]) as archive:
            archive.extractall(cls.base / "installed")
        cls.installed = cls.base / "installed/vibe-coding-skill"

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="vibe-i1-route-")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name).resolve()
        self.product = self.home / "product"
        self.product.mkdir()
        self.env = dict(self.package_env, VIBE_CODING_HOME=str(self.home / "state"))
        self.git("init", "-q")
        self.git("config", "user.name", "Portable Integration Fixture")
        self.git("config", "user.email", "i1@example.invalid")

    def test_portable_release_gate_blocks_without_installed_native_trivy(self):
        self.env["PATH"] = str(self.home / "no-executables")
        result = self.cli("trivy_compat.py", "--release-target", self.product,
                          "--output", self.home / "security/report.json", "--json", expected=2)
        self.assertEqual(result["gate"], "BLOCK")
        self.assertFalse(result["release_scan_verified"])

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.product, check=True, capture_output=True)

    def json_file(self, name, value):
        path = self.home / (name + ".json")
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def cli(self, script, *args, expected=0):
        process = subprocess.run([sys.executable, "-X", "utf8", str(self.installed / "scripts" / script), *map(str, args)],
                                 cwd=self.product, env=self.env, capture_output=True, text=True,
                                 encoding="utf-8", timeout=60)
        self.assertEqual(process.returncode, expected, process.stdout + process.stderr)
        return json.loads(process.stdout)

    def contract(self, tier=0, origin="manual", kind="manual-check"):
        return {"format": "vibe-task-contract", "schema_version": 1, "task_id": "portable-fixture",
                "objective": "Correct the fixture label", "scope": ["settings.txt"], "risk_tier": tier,
                "acceptance_criteria": [{"id": "label", "description": "The fixture contains the supplied label",
                    "required": True, "behavior": {"user_action": "Read the fixture", "expected_result": "See accepted"}}],
                "evidence_requirements": [{"id": "check", "criterion_ids": ["label"], "kind": kind,
                    "origin": origin, "required": True, "input_paths": ["settings.txt"], "input_excludes": []}]}

    def report(self, contract, result):
        receipt = result["receipt"]
        return {"schema_version": 3, "task_id": contract["task_id"], "contract_sha256": receipt["contract_sha256"],
                "status": "Done", "risk_tier": contract["risk_tier"], "blockers": [],
                "acceptance_criteria": [dict(copy.deepcopy(contract["acceptance_criteria"][0]), met=True, evidence_ids=[receipt["id"]])],
                "evidence": [{"id": receipt["id"], "kind": receipt["kind"], "origin": receipt["origin"],
                    "result": receipt["result"], "required": True, "requirement_id": "check",
                    "receipt_ref": result["receipt_ref"], "receipt_sha256": result["receipt_sha256"]}]}

    def test_bounded_routing_uses_installed_prefix_reader_and_surfaces_limitations(self):
        entry = self.product / "plugin.php"
        entry.write_text("<?php\n/* Plugin Name: Portable Prefix Fixture */\n" + " " * 70_000, encoding="utf-8")
        args = ["--root", self.product, "--task", "Update settings behavior", "--path", "plugin.php"]
        route = self.cli("context_router.py", *args, "--json")
        self.assertIn("wordpress", {row["name"] for row in route["packs"]})
        self.assertTrue(route["task"]["routing_uncertainties"])
        self.assertEqual(route["context_plan"]["inspection"]["scans"]["affected"]["bytes_read"], 65_536)
        plain = subprocess.run([sys.executable, "-X", "utf8", str(self.installed / "scripts/context_router.py"), *map(str, args)],
                               cwd=self.product, env=self.env, capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(plain.returncode, 0, plain.stderr)
        self.assertIn("WARNING: affected inspection incomplete", plain.stdout)
        self.assertIn("Head must assess", plain.stdout)
        entry.write_text("<?php function report() { return 1; }\n" + " " * 70_000, encoding="utf-8")
        route = self.cli("context_router.py", *args, "--json")
        self.assertNotIn("wordpress", {row["name"] for row in route["packs"]})
        drafted = self.cli("execution_plan.py", "draft", *args, "--json")
        self.assertFalse(drafted["execution_plan_required"])
        self.assertTrue(drafted["context_plan"]["task"]["routing_uncertainties"])

    def test_installed_root_ownership_blocks_conflicts_and_preserves_covered_drift(self):
        contract = self.contract()
        contract["scope"] = ["./"]
        contract_path = self.json_file("root-contract", contract)
        plan = self.cli("execution_plan.py", "draft", "--root", self.product,
                        "--task-contract", contract_path, "--path", "scripts/[id]/feature.py", "--json")
        first = plan["workstreams"][0]
        first.update(id="root", owner="agent-a", scope=["."])
        plan["workstreams"].append(dict(copy.deepcopy(first), id="nested", owner="agent-b", scope=["./scripts"]))
        plan["coordination"]["recommended_parallelism"] = 2
        blocked = self.cli("execution_plan.py", "validate", self.json_file("overlap", plan),
                           "--task-contract", contract_path, "--json", expected=2)
        self.assertTrue(any("ownership scopes overlap" in f for f in blocked["failures"]))
        plan["workstreams"] = [first]
        plan["coordination"]["recommended_parallelism"] = 1
        plan_path = self.json_file("root-plan", plan)
        self.assertEqual(self.cli("execution_plan.py", "validate", plan_path, "--task-contract", contract_path, "--json")["gate"], "PASS")
        change = self.json_file("covered-change", {"changed_paths": ["scripts/[id]/feature.py"]})
        self.assertEqual(self.cli("execution_plan.py", "drift", plan_path, change, "--json")["gate"], "CONTINUE")
        first["scope"] = ["./scripts/backend"]
        plan["workstreams"].append(dict(copy.deepcopy(first), id="frontend", owner="agent-b", scope=["scripts/frontend"]))
        plan["coordination"]["recommended_parallelism"] = 2
        self.assertEqual(self.cli("execution_plan.py", "validate", self.json_file("disjoint", plan),
                                 "--task-contract", contract_path, "--json")["gate"], "PASS")

    def test_light_route_preserves_legacy_claims_without_forcing_receipts_or_plans(self):
        (self.product / "settings.txt").write_text("accepted", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "light fixture")
        contract = self.contract()
        contract_path = self.json_file("contract", contract)
        plan = self.cli("execution_plan.py", "draft", "--root", self.product, "--task-contract", contract_path, "--json")
        self.assertFalse(plan["execution_plan_required"])
        self.assertEqual(plan["workstreams"][0]["criterion_ids"], ["label"])
        self.assertEqual(self.cli("execution_plan.py", "validate", self.json_file("plan", plan),
                                 "--task-contract", contract_path, "--json")["gate"], "PASS")
        legacy = {"schema_version": 2, "status": "Done", "risk_tier": 0, "blockers": [],
                  "acceptance_criteria": [dict(contract["acceptance_criteria"][0], met=True, evidence_ids=["read"])],
                  "evidence": [{"id": "read", "kind": "manual-check", "required": True, "result": "pass"}]}
        result = self.cli("completion_gate.py", self.json_file("legacy", legacy), "--json")
        self.assertFalse(result["receipt_verified"])
        # Seed an in-flight pre-receipt snapshot. Fresh structured tasks must
        # not acquire legacy eligibility from omitting the activation flag.
        saved = self.cli("project_state.py", "capture", "--root", self.product, "--task-contract", contract_path, "--json")
        self.assertEqual(saved["completion_schema"], 3)
        saved.pop("completion_schema")
        Path(saved["state_path"]).write_text(json.dumps(saved), encoding="utf-8")
        handoff = self.cli("project_state.py", "handoff", "--root", self.product, "--task-contract", contract_path,
                           "--completion-report", self.json_file("legacy", legacy), "--write-local", "--json")
        self.assertEqual(handoff["state"]["acceptance"]["outcomes"][0]["status"], "reported-met")
        self.assertFalse(Path(handoff["handoff_path"]).is_relative_to(self.product))
        resumed = self.cli("resume_context.py", "--root", self.product, "--json")
        self.assertEqual(resumed["local_state"]["project_state"]["task_contract"], contract)
        self.assertEqual(sorted(p.name for p in self.product.iterdir()), [".git", "settings.txt"])

    def test_bound_route_runs_literal_inputs_and_rejects_failed_stale_and_downgraded_evidence(self):
        relative = "src/[id]/settings.txt"
        source = self.product / relative
        source.parent.mkdir(parents=True)
        source.write_text("original", encoding="utf-8")
        (self.product / "check.py").write_text("from pathlib import Path\nassert Path(" + repr(relative) + ").read_text() == 'accepted'\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "bound fixture")
        contract = self.contract(1, "collected", "unit-test")
        contract["scope"] = ["src", "check.py"]
        contract["evidence_requirements"][0]["input_paths"] = [relative, "check.py"]
        contract_path = self.json_file("contract", contract)
        args = ["run", "--root", self.product, "--task-contract", contract_path, "--requirement", "check", "--", sys.executable, "check.py"]
        failed = self.cli("evidence_capture.py", *args, expected=2)
        self.assertEqual(failed["receipt"]["result"], "fail")
        self.assertTrue(failed["receipt"]["process_started"])
        self.cli("completion_gate.py", self.json_file("failed", self.report(contract, failed)), "--task-contract", contract_path,
                 "--root", self.product, "--json", expected=2)
        source.write_text("accepted", encoding="utf-8")
        passed = self.cli("evidence_capture.py", *args)
        report_path = self.json_file("report", self.report(contract, passed))
        complete_args = [report_path, "--task-contract", contract_path, "--root", self.product, "--json"]
        self.assertTrue(self.cli("completion_gate.py", *complete_args)["receipt_verified"])
        state = self.cli("project_state.py", "capture", "--root", self.product, "--task-contract", contract_path,
                         "--completion-report", report_path, "--json")
        self.assertEqual(state["completion_schema"], 3)
        self.assertTrue(state["acceptance"]["receipt_verified"])
        (self.product / "README.md").write_text("unrelated fixture note", encoding="utf-8")
        self.assertTrue(self.cli("completion_gate.py", *complete_args)["receipt_verified"])
        legacy = self.report(contract, passed)
        legacy["schema_version"] = 2
        self.cli("completion_gate.py", self.json_file("downgrade", legacy), "--task-contract", contract_path,
                 "--root", self.product, "--json", expected=2)
        source.write_text("stale", encoding="utf-8")
        self.cli("completion_gate.py", *complete_args, expected=2)
        resumed = self.cli("resume_context.py", "--root", self.product, "--json")
        self.assertFalse(resumed["local_state"]["project_state"]["acceptance"]["receipt_verified"])
        self.assertFalse(Path(passed["receipt_path"]).is_relative_to(self.product))

    def test_cross_boundary_specialist_uses_packed_runtime_and_separate_head_acceptance(self):
        # Reuse the existing offline specialist fixture, but preload every runtime
        # module from the extracted ZIP. No live freshness/model claims are made.
        program = textwrap.dedent('''
            import copy, importlib, json, os, subprocess, sys
            from pathlib import Path
            installed, tests = map(Path, sys.argv[1:])
            sys.path.insert(0, str(installed / "scripts"))
            names = ("behavior_contract", "completion_gate", "evidence_capture", "receipt_validation",
                     "specialist_manager", "specialist_handoff", "execution_plan", "local_workspace")
            modules = [importlib.import_module(name) for name in names]
            assert all(Path(module.__file__).resolve().is_relative_to(installed) for module in modules)
            sys.path.append(str(tests))
            import test_handoffs as fixtures
            fixtures.ROOT = installed
            case = fixtures.HandoffTests()
            try:
                case.setUp()
                case.spec["shared_contracts"] = [{"id": "setting-response", "description": "Usage documentation preserves the setting response"}]
                start = case.start()
                returned = case.output(start)
                (case.root / "docs").mkdir()
                (case.root / "docs/usage.md").write_text("The setting response stays unchanged", encoding="utf-8")
                returned["changed_surfaces"].append({"path": "docs/usage.md", "action": "add"})
                returned["decisions"] = [{"description": "Preserve the documented response", "criterion_ids": ["setting"],
                                          "contract_refs": ["setting-response"], "rationale": "Inspected fixture documentation and setting check"}]
                def write(name, value):
                    path = case.base / (name + ".json")
                    path.write_text(json.dumps(value), encoding="utf-8")
                    return str(path)
                contract = write("contract", case.contract)
                report = write("report", case.report())
                def cli(script, args, expected):
                    process = subprocess.run([sys.executable, "-X", "utf8", str(installed / "scripts" / script), *args],
                                             cwd=case.root, env=dict(os.environ, PYTHONPATH=""), capture_output=True, text=True,
                                             encoding="utf-8", timeout=60)
                    assert process.returncode == expected, process.stdout + process.stderr
                    return json.loads(process.stdout)
                plan = cli("execution_plan.py", ["draft", "--root", str(case.root), "--task-contract", contract,
                           "--stage", "build", "--specialist-assignment", write("assignment", case.spec), "--json"], 0)
                assert plan["bound_specialist_assignments"][0]["criterion_ids"] == ["setting"]
                assert cli("execution_plan.py", ["validate", write("plan", plan), "--task-contract", contract, "--json"], 0)["gate"] == "PASS"
                dropped = copy.deepcopy(plan)
                dropped["bound_specialist_assignments"] = []
                assert cli("execution_plan.py", ["validate", write("dropped", dropped), "--task-contract", contract, "--json"], 2)["gate"] == "BLOCK"
                gate_args = [report, "--task-contract", contract, "--root", str(case.root), "--json"]
                assert cli("completion_gate.py", gate_args, 2)["gate"] == "BLOCK"
                review_args = ["review", "--root", str(case.root), "--task-contract", contract, "--assignment-id", "ui-build",
                               "--return", write("return", returned), "--evidence", write("evidence", case.evidence)]
                inspected = cli("specialist_handoff.py", review_args, 2)
                assert inspected["gate"] == "UNVERIFIED" and not inspected["accepted"]
                assert inspected["review"]["scope_reconciliation_paths"] == ["docs/usage.md"]
                decision = case.decision(returned, inspected)
                assert cli("specialist_handoff.py", review_args + ["--decision", write("decision", decision)], 2)["gate"] == "BLOCK"
                decision["scope_reconciliations"] = [{"path": "docs/usage.md", "reason": "Documentation is within the retained task and existing authority"}]
                decision["contract_decisions"] = [{"id": "setting-response", "status": "compatible", "reason": "Fixture documentation preserves the checked response"}]
                assert cli("specialist_handoff.py", review_args + ["--decision", write("decision", decision)], 0)["accepted"]
                assert cli("completion_gate.py", gate_args, 0)["receipt_verified"]
                (case.root / "src/value.txt").write_text("stale", encoding="utf-8")
                assert cli("completion_gate.py", gate_args, 2)["gate"] == "BLOCK"
                print(json.dumps({"installed_runtime": True, "head_acceptance": True, "stale_blocked": True}))
            finally:
                case.doCleanups()
        ''')
        process = subprocess.run([sys.executable, "-X", "utf8", "-c", program, str(self.installed), str(ROOT / "tests")],
                                 cwd=self.product, env=self.env, capture_output=True, text=True, encoding="utf-8", timeout=90)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertEqual(json.loads(process.stdout), {"installed_runtime": True, "head_acceptance": True, "stale_blocked": True})


if __name__ == "__main__":
    unittest.main()
