"""Behavioral contracts for required routing and safe current-source installs."""
from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("specialist_manager_test", ROOT / "scripts/specialist_manager.py")
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


class SpecialistTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.skills, self.state = self.root / "skills", self.root / "state"
        self.entry = manager.registry()["specialists"][0]
        self.source = {"repository": self.entry["repository"], "skill_path": self.entry["skill_path"],
                       "commit": "a" * 40, "channel": "stable-release", "ref": "v2.0.0"}
        self.files = {"SKILL.md": b"---\nname: ui-ux-skill\n---\nRead `references/ui.md`.\n",
                      "references/ui.md": b"UI guidance\n"}

    def ensure(self, apply=False):
        with patch.object(manager, "resolve_latest", return_value=self.source), patch.object(manager, "source_package", return_value=self.files):
            return manager.ensure(self.entry, self.skills, self.state, apply)

    def test_one_required_specialist_for_product_ui_and_none_for_backend(self):
        for task, paths, facts in [("Design dashboard", [], {}), ("طراحی سایت", [], {}),
                                   ("Improve", ["app/view.tsx"], {}),
                                   ("Build mobile product", [], {"concern": ["ui"]}),
                                   ("Plugin settings interface", [], {"concern": ["ux"]})]:
            with self.subTest(task=task):
                selected = manager.select_specialists(task, paths, facts)
                self.assertEqual([row["id"] for row in selected], ["ui-ux-skill"])
                self.assertTrue(selected[0]["required"])
        self.assertEqual(manager.select_specialists("Fix SQL persistence", ["storage/store.py"]), [])
        with self.assertRaises(ValueError):
            manager.select_specialists("Design", explicit=["production-dashboard-ui-ux-skill"])

    def test_stage_alone_selects_none_and_multiple_domains_keep_one_head(self):
        for stage in manager.registry()["lifecycle"]:
            self.assertEqual(manager.select_specialists("Fix spelling", ["README.md"], stage=stage), [])
        rows = manager.select_specialists("Build checkout", facts={"concern": ["ui", "payments"]}, stage="design")
        self.assertEqual({row["id"] for row in rows}, {"ui-ux-skill", "security-and-hardening", "api-and-interface-design"})
        self.assertTrue(all(row["active_in_stage"] and row["stage_owner"] == "vibe-coding-skill" for row in rows))
        self.assertTrue(all("publish-or-deploy-independently" in row["permissions"]["denied"] for row in rows))
        explicit = manager.select_specialists("Investigate", explicit=["security-and-hardening", "debugging-and-error-recovery"], stage="review")
        self.assertEqual(len(explicit), 2)
        self.assertFalse(next(row for row in explicit if row["id"] == "debugging-and-error-recovery")["active_in_stage"])

    def test_domain_semantics_docs_and_sensitive_risk_do_not_select_unrelated_skills(self):
        self.assertEqual(manager.select_specialists("Describe API authentication", ["docs/API.md"]), [])
        self.assertEqual(manager.select_specialists("Fix isolated calculation", ["lib/math.py"]), [])
        debug = manager.select_specialists("Unknown cause", facts={"concern": "debugging"}, stage="build")
        self.assertEqual([row["id"] for row in debug], ["debugging-and-error-recovery"])
        sensitive = manager.select_specialists("Change retention", risk_facts={"data_sensitivity": "personal"})
        self.assertEqual([row["id"] for row in sensitive], ["security-and-hardening"])

    def test_contract_stage_and_assignment_survive_router_and_execution_plan(self):
        spec = importlib.util.spec_from_file_location("specialist_execution_test", ROOT / "scripts/execution_plan.py")
        planner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(planner)
        result = planner.draft(self.root, "Change boundary", context_facts={"concern": "contracts"}, stage="design")
        self.assertEqual(result["context_plan"]["task"]["stage"], "design")
        self.assertEqual(result["specialist_assignments"][0]["id"], "api-and-interface-design")
        self.assertTrue(result["specialist_assignments"][0]["active_in_stage"])

    def test_router_accepts_ui_semantics_and_emits_actual_requirement(self):
        router_spec = importlib.util.spec_from_file_location("router_specialist_test", ROOT / "scripts/context_router.py")
        router = importlib.util.module_from_spec(router_spec)
        router_spec.loader.exec_module(router)
        result = router.plan(self.root, "Build product", context_facts={"concern": "ui"})
        self.assertEqual(result["required_specialists"][0]["repository"], "pooyahayati/UI-UX-Skill")

    def test_latest_stable_and_no_release_default_branch(self):
        with patch.object(manager, "api", side_effect=[{"tag_name": "v2.0.0"}, {"sha": "a" * 40}]) as api:
            self.assertEqual(manager.resolve_latest(self.entry)["channel"], "stable-release")
            self.assertIn("/commits/v2.0.0", api.call_args.args[0])
        missing = urllib.error.HTTPError("https://api.github.com/", 404, "none", {}, None)
        with patch.object(manager, "api", side_effect=[missing, {"default_branch": "main"}, {"sha": "b" * 40}]):
            self.assertEqual(manager.resolve_latest(self.entry)["channel"], "default-branch")
        denied = urllib.error.HTTPError("https://api.github.com/", 403, "denied", {}, None)
        with patch.object(manager, "api", side_effect=denied) as api:
            self.assertRaises(urllib.error.HTTPError, manager.resolve_latest, self.entry)
            self.assertEqual(api.call_count, 1)

    def test_archive_identity_resources_and_path_escape(self):
        manager.validate_package(self.files, "ui-ux-skill")
        self.assertRaises(ValueError, manager.validate_package, {"SKILL.md": self.files["SKILL.md"]}, "ui-ux-skill")
        self.assertRaises(ValueError, manager.validate_package, self.files, "other-skill")
        self.assertRaises(ValueError, manager.validate_package, {"SKILL.md": b"---\nname: ui-ux-skill\n"}, "ui-ux-skill")
        payload = io.BytesIO()
        with ZipFile(payload, "w") as archive:
            archive.writestr("repo/../../escape", b"bad")
        with patch.object(manager, "request_bytes", return_value=payload.getvalue()):
            self.assertRaises(ValueError, manager.source_package, self.entry, self.source)

    def test_shared_references_are_relocated_transitively_without_other_skills(self):
        entry = next(row for row in manager.registry()["specialists"] if row["id"] == "security-and-hardening")
        payload = io.BytesIO()
        with ZipFile(payload, "w") as archive:
            archive.writestr("repo/skills/security-and-hardening/SKILL.md", "---\nname: security-and-hardening\n---\nRead `../../references/shared.md`.\n[Details](references/detail.md#section)\n")
            archive.writestr("repo/skills/security-and-hardening/references/detail.md", "Read `../../../references/shared.md`.\n")
            archive.writestr("repo/references/shared.md", "[More](next.md#example)\n")
            archive.writestr("repo/references/next.md", "Evidence\n")
            archive.writestr("repo/references/unrelated.md", "Unneeded\n")
            archive.writestr("repo/skills/using-agent-skills/SKILL.md", "Do not install\n")
            archive.writestr("repo/LICENSE", "MIT\n")
        with patch.object(manager, "request_bytes", return_value=payload.getvalue()):
            files = manager.source_package(entry, self.source)
        self.assertIn(b"upstream-references/shared.md", files["SKILL.md"])
        self.assertIn(b"../upstream-references/shared.md", files["references/detail.md"])
        self.assertIn(b"next.md#example", files["upstream-references/shared.md"])
        self.assertIn("upstream-references/next.md", files)
        self.assertIn("vibe-head-contract.md", files)
        self.assertEqual(files["LICENSE"], b"MIT\n")
        self.assertNotIn("upstream-references/unrelated.md", files)
        self.assertFalse(any("using-agent-skills" in path for path in files))

    def test_real_relative_prefix_and_reference_escape_are_rejected(self):
        broken = {"SKILL.md": b"---\nname: ui-ux-skill\n---\nRead `../../references/ui.md`.\n", "references/ui.md": b"Existing different resource\n"}
        self.assertRaises(ValueError, manager.validate_package, broken, "ui-ux-skill")
        entry = next(row for row in manager.registry()["specialists"] if row["id"] == "security-and-hardening")
        missing = {"skills/security-and-hardening/SKILL.md": b"---\nname: security-and-hardening\n---\nRead `../../references/missing.md`.\n"}
        self.assertRaises(ValueError, manager.adapt_resources, missing, entry)
        sibling = {"skills/security-and-hardening/SKILL.md": b"---\nname: security-and-hardening\n---\n[Other](../other/SKILL.md)\n", "skills/other/SKILL.md": b"Other skill\n"}
        self.assertRaises(ValueError, manager.adapt_resources, sibling, entry)

    def test_install_adopt_update_and_cached_current_source(self):
        self.assertEqual(self.ensure()["status"], "missing")
        self.assertTrue(self.ensure(True)["updated"])
        target = self.skills / "ui-ux-skill"
        with patch.object(manager, "resolve_latest", return_value=self.source), patch.object(manager, "source_package") as package:
            self.assertEqual(manager.ensure(self.entry, self.skills, self.state)["status"], "current")
            package.assert_not_called()
        record_path = self.state / "ui-ux-skill.json"
        old_policy = json.loads(record_path.read_text())
        old_policy["source"]["package_policy"] = "older-adapter"
        record_path.write_text(json.dumps(old_policy), encoding="utf-8")
        with patch.object(manager, "resolve_latest", return_value=self.source), patch.object(manager, "source_package", return_value=self.files) as package:
            self.assertEqual(manager.ensure(self.entry, self.skills, self.state)["status"], "current")
            package.assert_called_once()
        self.source["commit"] = "b" * 40
        self.files["references/ui.md"] = b"New guidance\n"
        self.assertEqual(self.ensure()["status"], "outdated")
        updated = self.ensure(True)
        self.assertEqual((target / "references/ui.md").read_bytes(), b"New guidance\n")
        self.assertEqual((Path(updated["backup"]) / "references/ui.md").read_bytes(), b"UI guidance\n")
        record = json.loads((self.state / "ui-ux-skill.json").read_text())
        self.assertEqual(record["source"]["commit"], "b" * 40)

    def test_local_edits_and_replacement_failure_preserve_old_install(self):
        self.ensure(True)
        target = self.skills / "ui-ux-skill" / "references/ui.md"
        target.write_bytes(b"Local guidance\n")
        self.assertEqual(self.ensure(True)["status"], "local-modifications")
        self.assertEqual(target.read_bytes(), b"Local guidance\n")
        target.write_bytes(b"UI guidance\n")
        self.source["commit"] = "b" * 40
        self.files["references/ui.md"] = b"New guidance\n"
        with patch.object(manager, "write_record", side_effect=OSError("disk full")):
            self.assertRaises(OSError, self.ensure, True)
        self.assertEqual(target.read_bytes(), b"UI guidance\n")
        self.assertEqual(json.loads((self.state / "ui-ux-skill.json").read_text())["source"]["commit"], "a" * 40)

    def test_unverified_or_incompatible_current_source_is_explicit(self):
        with patch.object(manager, "resolve_latest", side_effect=OSError("offline")):
            self.assertEqual(manager.ensure(self.entry, self.skills, self.state)["status"], "currency-unverified")
        with patch.object(manager, "resolve_latest", return_value=self.source), patch.object(manager, "source_package", side_effect=ValueError("missing resource")):
            self.assertEqual(manager.ensure(self.entry, self.skills, self.state, True)["status"], "latest-incompatible")
        self.assertFalse((self.skills / "ui-ux-skill").exists())
        self.state.mkdir()
        (self.state / "ui-ux-skill.json").write_text("[]", encoding="utf-8")
        self.assertEqual(manager.ensure(self.entry, self.skills, self.state)["status"], "installation-unverified")

    def test_head_reload_and_required_gap_do_not_claim_pass(self):
        with patch.object(manager, "ensure", return_value={"id": "vibe-coding-skill", "status": "current", "updated": True}) as ensure:
            self.assertEqual(manager.run("prepare", self.skills, self.state, [self.entry], True)["gate"], "RELOAD")
            self.assertEqual(ensure.call_count, 1)
        with patch.object(manager, "ensure", side_effect=[{"id": "vibe-coding-skill", "status": "currency-unverified"}, {"id": "ui-ux-skill", "status": "missing"}]):
            self.assertEqual(manager.run("prepare", self.skills, self.state, [self.entry], False)["gate"], "BLOCK")
        with manager.installation_lock(self.skills):
            with self.assertRaises(ValueError):
                manager.run("inventory", self.skills, self.state, [], False)

    def test_daily_inventory_reports_unused_failure_without_blocking_backend(self):
        (self.skills / "ui-ux-skill").mkdir(parents=True)
        with patch.object(manager, "ensure", side_effect=[{"id": "vibe-coding-skill", "status": "current"}, {"id": "ui-ux-skill", "status": "currency-unverified"}]):
            result = manager.run("prepare", self.skills, self.state, [], False)
            self.assertEqual(result["gate"], "WARN")
            self.assertFalse((self.state / "inventory.json").exists())
        with patch.object(manager, "ensure", side_effect=lambda entry, *args: {"id": entry["id"], "status": "current"}) as ensure:
            manager.run("inventory", self.skills, self.state, [], False)
            self.assertEqual(ensure.call_count, 2)
        with patch.object(manager, "ensure", return_value={"id": "vibe-coding-skill", "status": "current"}) as ensure:
            manager.run("prepare", self.skills, self.state, [], False)
            self.assertEqual(ensure.call_count, 1)


if __name__ == "__main__":
    unittest.main()
