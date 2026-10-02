"""Behavioral contracts for required routing and safe current-source installs."""
from __future__ import annotations

import importlib.util
import copy
import io
import json
import tempfile
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile
from contextlib import redirect_stdout

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

    def test_head_package_prose_does_not_require_specialist_resources(self):
        package = ROOT / "skills/vibe-coding-skill"
        files = {p.relative_to(package).as_posix(): p.read_bytes()
                 for p in package.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
        self.assertNotIn("vibe-head-contract.md", files)
        manager.validate_package(files, "vibe-coding-skill")
        files["SKILL.md"] += b"\nSpecialists may discuss `product-types.json` and `specialists.json`.\n"
        manager.validate_package(files, "vibe-coding-skill")

    def test_delegated_contract_is_required_even_without_a_prose_mention(self):
        with self.assertRaisesRegex(ValueError, "missing delegated Head contract"):
            manager.validate_package(self.files, "ui-ux-skill", mode="head-delegated")
        files = {**self.files, "vibe-head-contract.md": b"Head controls\n"}
        manager.validate_package(files, "ui-ux-skill", mode="head-delegated")

    def test_explicit_resources_and_nested_links_still_require_real_files(self):
        files = {"SKILL.md": b"---\nname: ui-ux-skill\n---\nRead `config/product-types.json` and [Registry](config/specialists.json).\n",
                 "config/product-types.json": b"{}", "config/specialists.json": b"{}"}
        manager.validate_package(files, "ui-ux-skill")
        for missing in ("config/product-types.json", "config/specialists.json"):
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                manager.validate_package({p: content for p, content in files.items() if p != missing}, "ui-ux-skill")
        files["references/detail.md"] = b"[Contract](../vibe-head-contract.md)\n"
        with self.assertRaisesRegex(ValueError, "broken relative link"):
            manager.validate_package(files, "ui-ux-skill")
        files["vibe-head-contract.md"] = b"Head controls\n"
        manager.validate_package(files, "ui-ux-skill")

    def test_real_head_cold_adoption_and_cached_preflight_agree(self):
        head = manager.registry()["head"]
        package = ROOT / "skills/vibe-coding-skill"
        payload = io.BytesIO()
        target = self.skills / head["skill_name"]
        for p in package.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
                rel = p.relative_to(package)
                destination = target / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(p.read_bytes())
        with ZipFile(payload, "w") as archive:
            for p in target.rglob("*"):
                if p.is_file():
                    archive.writestr("repo/" + head["skill_path"] + "/" + p.relative_to(target).as_posix(), p.read_bytes())
        source = {"repository": head["repository"], "skill_path": head["skill_path"],
                  "commit": "c" * 40, "channel": "stable-release", "ref": "v1.1.0"}
        before = manager.installed_hashes(target)
        with patch.object(manager, "resolve_latest", return_value=source), patch.object(manager, "request_bytes", return_value=payload.getvalue()) as request:
            cold = manager.run("prepare", self.skills, self.state, [], True)
            self.assertEqual(cold["gate"], "PASS")
            self.assertEqual(cold["skills"][0]["status"], "current")
            request.assert_called_once()
            warm = manager.run("prepare", self.skills, self.state, [], True)
            self.assertEqual(warm["gate"], cold["gate"])
            self.assertEqual(warm["skills"][0]["status"], cold["skills"][0]["status"])
            request.assert_called_once()
            fresh_state = self.root / "fresh-state"
            fresh = manager.run("prepare", self.skills, fresh_state, [], True)
            self.assertEqual(fresh["gate"], cold["gate"])
            self.assertEqual(request.call_count, 2)
        self.assertEqual(manager.installed_hashes(target), before)

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


class CompatibilityTests(unittest.TestCase):
    def setUp(self):
        SpecialistTests.setUp(self)
        self.files["vibe-head-contract.md"] = (ROOT / "references/specialist-authority.md").read_bytes()
        self.ensure(True)

    def ensure(self, apply=False):
        return SpecialistTests.ensure(self, apply)

    def packet(self):
        return manager.compatibility_packet(self.entry, self.skills, self.state, self.ensure())

    def assessment(self, packet=None):
        packet = packet or self.packet()
        rationale = {
            "authority": "Domain guidance remains subordinate to the injected Head contract.",
            "platform": "UI guidance uses the assigned product runtime; no replacement stack is mandated.",
            "dependencies": "Referenced UI guidance is contained in the package; no additional installation is requested.",
            "verification": "UI checks follow changed behavior and Head risk controls; no unrelated suite is mandated.",
            "scope-authorization": "The Head contract retains assigned surfaces and publication permissions."}
        return {"format": "vibe-specialist-compatibility", "schema_version": 1, "specialist_id": self.entry["id"],
                **{k: packet[k] for k in ("binding_sha256", "upstream_revision", "head_contract_sha256")},
                "decision": "accepted", "assessed_by": "Engineering Head", "assessed_at": "2026-10-02T00:00:00Z",
                "reason": "Read the fixture domain guidance and effective Head controls.",
                "reviewed_paths": packet["required_review_paths"], "conflicts": [],
                "checks": [{"area": area, "status": "compatible", "rationale": rationale[area],
                            "resource_paths": ["SKILL.md", "vibe-head-contract.md"]} for area in sorted(rationale)]}

    def run_manager(self, selected=None, assessment=None, mode="prepare"):
        original = manager.ensure
        def ensure(entry, *args):
            return {"id": entry["id"], "status": "current", "updated": False} if entry["id"] == "vibe-coding-skill" else original(entry, *args)
        with patch.object(manager, "ensure", side_effect=ensure), patch.object(manager, "resolve_latest", return_value=self.source), patch.object(manager, "source_package", return_value=self.files):
            return manager.run(mode, self.skills, self.state, [self.entry] if selected is None else selected, False, assessment)

    def test_valid_installation_is_not_semantic_acceptance_and_reuse_skips_diff(self):
        pending = self.run_manager()
        self.assertEqual(pending["gate"], "BLOCK")
        self.assertEqual(pending["skills"][1]["status"], "current")
        self.assertEqual(pending["skills"][1]["compatibility"]["status"], "assessment-required")
        packet = pending["skills"][1]["compatibility"]["review"]
        self.assertIn("UI guidance", next(d["diff"] for d in packet["diffs"] if d["path"] == "references/ui.md"))
        self.assertEqual(self.run_manager(assessment=self.assessment(packet), mode="assess")["gate"], "PASS")
        self.source["ref"] = "v2.0.1"  # A new release label on unchanged instructions does not need reassessment.
        with patch.object(manager.difflib, "unified_diff", side_effect=AssertionError("cached assessment should not generate another diff")):
            result = self.run_manager()
        self.assertEqual(result["gate"], "PASS")
        self.assertTrue(result["skills"][1]["compatibility"]["reused"])
        # Exercise the public CLI parser and persistence path without live upstream traffic.
        decision = self.root / "head-decision.json"
        decision.write_text(json.dumps(self.assessment()), encoding="utf-8")
        original = manager.ensure
        def ensure(entry, *args):
            return {"id": entry["id"], "status": "current", "updated": False} if entry["id"] == "vibe-coding-skill" else original(entry, *args)
        output = io.StringIO()
        argv = ["specialist_manager.py", "assess", "--specialist", self.entry["id"], "--stage", "design",
                "--skills-dir", str(self.skills), "--state-dir", str(self.state), "--assessment", str(decision), "--json"]
        with patch.object(sys, "argv", argv), patch.object(manager, "ensure", side_effect=ensure), patch.object(manager, "resolve_latest", return_value=self.source), redirect_stdout(output):
            self.assertEqual(manager.main(), 0)
        self.assertEqual(json.loads(output.getvalue())["gate"], "PASS")

    def test_changed_revision_and_deleted_resource_need_review_then_cache(self):
        self.run_manager(assessment=self.assessment(), mode="assess")
        self.source["commit"] = "b" * 40
        self.files.pop("references/ui.md")
        self.files["SKILL.md"] = b"---\nname: ui-ux-skill\n---\nUse assigned UI runtime.\n"
        self.ensure(True)
        packet = self.packet()
        self.assertEqual(packet["previous_revision"], "a" * 40)
        self.assertIn({"path": "references/ui.md", "action": "delete", "before_sha256": manager.digest("references/ui.md", b"UI guidance\n"), "after_sha256": None}, packet["changed_resources"])
        self.assertEqual(self.run_manager()["gate"], "BLOCK")
        self.assertEqual(self.run_manager(assessment=self.assessment(packet), mode="assess")["gate"], "PASS")
        self.assertEqual(self.run_manager()["gate"], "PASS")

    def test_head_policy_and_domain_changes_invalidate_accepted_assessment(self):
        self.run_manager(assessment=self.assessment(), mode="assess")
        old = self.packet()["binding_sha256"]
        self.entry = dict(self.entry, assignment="UI only; preserve a newly required tenant boundary")
        self.assertNotEqual(self.packet()["binding_sha256"], old)
        self.assertEqual(self.run_manager()["gate"], "BLOCK")
        self.run_manager(assessment=self.assessment(), mode="assess")
        previous = self.packet()["binding_sha256"]
        record = json.loads((self.state / "ui-ux-skill.json").read_text())
        record["source"]["package_policy"] = "older-adapter"
        (self.state / "ui-ux-skill.json").write_text(json.dumps(record), encoding="utf-8")
        # The real installer reconciles the old policy before compatibility can be assessed.
        current = self.ensure()
        self.assertNotEqual(current["source"]["package_policy"], "older-adapter")
        self.assertEqual(self.packet()["binding_sha256"], previous)
        with patch.object(manager, "PACKAGE_ADAPTER", manager.PACKAGE_ADAPTER + 1):
            self.ensure()
            self.assertNotEqual(self.packet()["binding_sha256"], previous)
            self.assertEqual(self.run_manager()["gate"], "BLOCK")

    def test_conflicts_cannot_be_accepted_and_head_override_must_be_explicit(self):
        value = self.assessment()
        value["checks"][0]["status"] = "conflict"
        value["conflicts"] = ["Upstream requests an unregistered installer."]
        self.assertEqual(self.run_manager(assessment=value, mode="assess")["gate"], "BLOCK")
        value["decision"] = "blocked"
        blocked = self.run_manager(assessment=value, mode="assess")
        self.assertEqual(blocked["skills"][1]["compatibility"]["status"], "compatibility-blocked")
        value.update(decision="accepted", conflicts=[])
        value["checks"][0].update(status="overridden", rationale="The injected Head contract reserves installation authority and prevents following this request.")
        self.assertEqual(self.run_manager(assessment=value, mode="assess")["gate"], "PASS")
        value["checks"][0]["resource_paths"] = ["SKILL.md"]
        self.assertEqual(self.run_manager(assessment=value, mode="assess")["gate"], "BLOCK")

    def test_changed_binding_missing_review_and_wrong_origin_fail_closed(self):
        valid = self.assessment()
        for fields in ({"upstream_revision": "c" * 40}, {"binding_sha256": "0" * 64}, {"specialist_id": "other"},
                       {"reviewed_paths": ["SKILL.md"]}, {"assessed_at": "2026-10-02"}, {"auto_approved": True}):
            with self.subTest(fields=fields):
                value = copy.deepcopy(valid)
                value.update(fields)
                self.assertEqual(self.run_manager(assessment=value, mode="assess")["gate"], "BLOCK")
        self.assertEqual(self.run_manager(assessment=valid, mode="assess")["gate"], "PASS")
        path = Path(self.packet()["assessment_path"])
        path.write_text('{"decision":"accepted"}', encoding="utf-8")
        self.assertEqual(self.run_manager()["gate"], "BLOCK")

    def test_inventory_and_preparation_only_do_not_block_unaffected_work(self):
        self.assertEqual(self.run_manager(selected=[])["gate"], "PASS")
        inactive = dict(self.entry, active_in_stage=False)
        result = self.run_manager(selected=[inactive])
        self.assertEqual(result["gate"], "PASS")
        self.assertEqual(result["skills"][1]["compatibility"]["status"], "assessment-required")
        (self.skills / "ui-ux-skill/references/ui.md").write_bytes(b"Local edits\n")
        self.assertEqual(self.run_manager()["gate"], "BLOCK")

    def test_review_excerpt_is_bounded_and_full_resource_remains_available(self):
        self.source["commit"] = "b" * 40
        self.files["references/ui.md"] = b"Long changed instructions\n" * 10000
        self.ensure(True)
        packet = self.packet()
        self.assertLessEqual(sum(len(d["diff"].encode("utf-8")) for d in packet["diffs"]), manager.MAX_REVIEW_BYTES)
        self.assertTrue(any(d["truncated"] for d in packet["diffs"]))
        self.assertTrue((Path(packet["resource_root"]) / "references/ui.md").is_file())


if __name__ == "__main__":
    unittest.main()
