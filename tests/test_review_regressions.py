"""Behavioral regressions from the independent 0.10.7 review."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(
        "review_regression_" + name, ROOT / "scripts" / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RiskAndCompletionRegressions(unittest.TestCase):
    def test_unrecognized_risk_values_remain_unresolved(self):
        result = load("risk_classifier").classify("Update behavior", facts={
            "operation": "unrecognized-operation", "environment": "unrecognized-environment",
            "data_sensitivity": "unrecognized-data", "change_boundary": "unrecognized-boundary",
        })
        self.assertEqual(len(result["uncertainties"]), 4)

    def test_original_persian_destructive_request_is_critical(self):
        result = load("risk_classifier").classify(
            "حذف تمام اطلاعات مشتریان از پایگاه داده عملیاتی"
        )
        self.assertEqual(result["tier"], 3)

    def test_planner_preserves_structured_risk(self):
        with tempfile.TemporaryDirectory() as td:
            result = load("execution_plan").draft(Path(td), "Update behavior", risk_facts={
                "operation": "destructive", "environment": "production",
                "data_sensitivity": "personal", "change_boundary": "local",
            })
        self.assertEqual(result["planning_basis"]["risk_tier"], 3)
        self.assertTrue(result["execution_plan_required"])

    def test_done_requires_a_required_outcome(self):
        result = load("completion_gate").evaluate({
            "schema_version": 2, "status": "Done", "risk_tier": 1, "blockers": [],
            "acceptance_criteria": [{"id": "outcome", "description": "Feature works",
                "required": False, "met": False, "evidence_ids": ["lint"]}],
            "evidence": [{"id": "lint", "kind": "lint", "required": False,
                "result": "pass", "provenance": {"source": "local", "reference": "lint.log"}}],
        })
        self.assertEqual(result["gate"], "BLOCK")

    def test_approved_required_outcome_cannot_be_downgraded(self):
        result = load("completion_gate").evaluate({
            "schema_version": 2, "status": "Done", "risk_tier": 0, "blockers": [],
            "acceptance_criteria": [{"id": "replacement", "description": "Other behavior",
                "required": True, "met": True, "evidence_ids": ["test"]}],
            "evidence": [{"id": "test", "kind": "test", "required": True, "result": "pass"}],
        }, [{"id": "outcome", "description": "Requested behavior", "required": True}])
        self.assertEqual(result["gate"], "BLOCK")
        self.assertTrue(result["acceptance_baseline_checked"])

    def test_risk_aliases_preserve_sensitive_policy(self):
        result = load("risk_classifier").classify("Update behavior", facts={
            "operation": "delete", "environment": "live", "data_sensitivity": "pii",
            "change_boundary": "single-module",
        })
        self.assertEqual(result["tier"], 3)
        self.assertFalse(result["uncertainties"])

    def test_malformed_acceptance_baseline_blocks_without_crashing(self):
        gate = load("completion_gate")
        for baseline in ([], [{"id": [], "required": True}],
                         [{"id": "outcome", "required": False, "description": "Optional"}]):
            with self.subTest(baseline=baseline):
                result = gate.evaluate({"schema_version": 2, "status": "Done", "risk_tier": 0,
                    "acceptance_criteria": [{"id": "outcome", "description": "Required",
                        "required": True, "met": True, "evidence_ids": ["test"]}],
                    "evidence": [{"id": "test", "kind": "test", "result": "pass", "required": True}]}, baseline)
                self.assertEqual(result["gate"], "BLOCK")


class ProjectBoundaryRegressions(unittest.TestCase):
    def test_generic_runtime_fact_does_not_require_a_specialist_pack(self):
        with tempfile.TemporaryDirectory() as td:
            result = load("context_router").plan(Path(td), "Update behavior", context_facts={"runtime": "python"})
        self.assertEqual(result["task"]["structured_context_facts"], {"runtime": ["python"]})
        self.assertFalse(result["packs"])

    def test_custom_siblings_preserve_platform_locality(self):
        router = load("context_router")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "components/shop").mkdir(parents=True)
            (root / "components/api").mkdir(parents=True)
            (root / "components/shop/plugin.php").write_text(
                "<?php\n/* Plugin Name: Shop */\n", encoding="utf-8"
            )
            (root / "components/api/pyproject.toml").write_text("[project]\nname='api'\n")
            (root / "components/api/main.py").write_text("def endpoint(): return {}\n")
            result = router.plan(root, "Add an endpoint", ["components/api/main.py"])
            self.assertNotIn("wordpress", {pack["name"] for pack in result["packs"]})
            self.assertNotIn("php", {pack["name"] for pack in result["packs"]})
            result = router.plan(root, "Update helpers", [
                "components/api/main.py", "components/shop/plugin.php"
            ])
            self.assertEqual(result["task"]["scope"]["level"], "cross-boundary")

    def test_wordpress_sibling_plugins_are_distinct_areas(self):
        router = load("context_router")
        scope = router.change_scope([
            "wp-content/plugins/a/main.php", "wp-content/plugins/b/main.php"
        ], load("risk_classifier").classify("Update helpers"))
        self.assertEqual(scope["level"], "cross-boundary")


class ArtifactEvidenceRegressions(unittest.TestCase):
    def test_npm_evidence_is_selected_version_only(self):
        guard = load("dependency_guard")
        package = {"dist-tags": {"latest": "2.0.0"}, "license": "MIT",
                   "repository": "https://example.test/latest", "versions": {
                       "1.0.0": {"license": {"type": "GPL-3.0-only"},
                                 "repository": {"url": "git+https://example.test/old.git"}},
                       "1.5.0": {}, "2.0.0": {"license": "Apache-2.0",
                                                "repository": "https://example.test/v2"},
                   }}
        for requested, license_value, repository, exists in [
            ("1.0.0", "GPL-3.0-only", "git+https://example.test/old.git", True),
            ("1.5.0", None, None, True), ("9.0.0", None, None, False),
            (None, "Apache-2.0", "https://example.test/v2", None),
        ]:
            with self.subTest(version=requested), mock.patch.object(guard, "http_json", return_value=package):
                result = guard.lookup_npm("sample", requested)
                self.assertEqual(result["metadata_version"], requested or "2.0.0")
                self.assertEqual(result["license"], license_value)
                self.assertEqual(result["repository"], repository)
                self.assertEqual(result["version_exists"], exists)

    def test_missing_npm_metadata_requires_same_version_independent_evidence(self):
        guard = load("dependency_guard")
        with mock.patch.object(guard, "http_json", return_value={
            "license": "MIT", "repository": "https://example.test/latest",
            "dist-tags": {"latest": "2.0.0"}, "versions": {"1.0.0": {}},
        }):
            registry = guard.lookup_npm("sample", "1.0.0")
        for selected, checked, expected in [
            ("1.0.0", True, "ACCEPT"), ("2.0.0", True, "REVIEW REQUIRED"),
            (None, True, "REVIEW REQUIRED"), ("1.0.0", False, "REVIEW REQUIRED"),
        ]:
            with self.subTest(selected=selected, checked=checked):
                independent = {"checked": checked, "selected_version": selected, "licenses": ["MIT"],
                               "links": [{"label": "SOURCE_REPO", "url": "https://example.test/v1"}]}
                licenses = guard.effective_licenses(registry, independent)
                repository = guard.source_repository(registry, independent)
                signal = guard.license_policy_signal(licenses, ["MIT"], [])
                decision, signals = guard.evaluate_dependency(
                    registry, {"checked": True}, independent, {}, {}, {}, signal,
                    "1.0.0", 1, "required", "Protocol parser",
                )
                self.assertEqual(decision, expected)
                if expected == "ACCEPT":
                    self.assertEqual(repository, "https://example.test/v1")
                    self.assertEqual(licenses, ["MIT"])
                else:
                    self.assertIsNone(repository)
                    self.assertEqual(licenses, [])
                    self.assertTrue({"license.missing", "provenance.repository_missing"}
                                    <= {s["code"] for s in signals})

    def test_dependency_metadata_belongs_to_selected_release(self):
        guard = load("dependency_guard")
        project = {"info": {"name": "sample", "version": "2.0.0", "license": "MIT"},
                   "releases": {"1.0.0": [], "2.0.0": []}}
        selected = {"info": {"name": "sample", "version": "1.0.0", "license": "GPL-3.0",
                             "project_urls": {"Source": "https://example.org/old-source"}}}
        with mock.patch.object(guard, "http_json", side_effect=[project, selected]) as fetch:
            result = guard.lookup_pypi("sample", "1.0.0")
        self.assertEqual(result["license"], "GPL-3.0")
        self.assertEqual(result["repository"], "https://example.org/old-source")
        self.assertTrue(fetch.call_args.args[0].endswith("/1.0.0/json"))
        with mock.patch.object(guard, "http_json", return_value={"crate": {
            "name": "sample", "max_stable_version": "2.0.0", "license": "MIT"},
            "versions": [{"num": "1.0.0", "license": "GPL-3.0"}, {"num": "2.0.0", "license": "MIT"}]}):
            result = guard.lookup_crates("sample", "1.0.0")
        self.assertEqual(result["license"], "GPL-3.0")

    def test_wordpress_install_evidence_records_initial_state(self):
        wp = load("wordpress_artifact")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            source.mkdir()
            (source / "demo.php").write_text("<?php\n/*\nPlugin Name: Demo\nVersion: 1.0.0\n*/\n")
            artifact = root / "demo.zip"
            wp.package_artifact(source, artifact, slug="demo")
            for initial in ([], [{"name": "demo"}]):
                with self.subTest(initial=initial):
                    def run(binary, directory, args):
                        import json
                        output = json.dumps(initial) if args[:2] == ["plugin", "list"] else "1.0.0"
                        return {"command": args, "returncode": 0, "output": output}
                    with mock.patch.object(wp, "run_wp", side_effect=run):
                        result = wp.runtime_check(artifact, root)
                    self.assertEqual(result["plugin_present_before"], bool(initial))
                    self.assertEqual(result["fresh_plugin_install_checked"], not bool(initial))
                    self.assertFalse(result["fresh_install_checked"])
                    self.assertFalse(result["data_freshness_verified"])
