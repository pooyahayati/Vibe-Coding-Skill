from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(
        "test_" + name.replace(".py", ""),
        path,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def init_project(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)


def write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


WORDPRESS_WOO = """<?php
/*
Plugin Name: Vibe Test Extension
*/
add_action('plugins_loaded', 'vibe_test_boot');
function vibe_test_boot() {
    if ( class_exists( 'WooCommerce' ) ) {
        add_filter( 'woocommerce_order_status_changed', '__return_true' );
    }
}
"""


class ContextRouterTests(unittest.TestCase):
    def setUp(self):
        self.router = load_script("context_router.py")

    def test_tiny_woocommerce_ui_task_avoids_heavy_concern_packs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            init_project(root)
            write(root, "vibe-test.php", WORDPRESS_WOO)

            result = self.router.plan(
                root,
                "Change checkout button label text only",
                ["vibe-test.php"],
            )

        names = {row["name"] for row in result["packs"]}
        self.assertEqual(
            {"php", "wordpress", "woocommerce"},
            names,
        )
        self.assertNotIn("payments", names)
        self.assertNotIn("security-web", names)
        self.assertNotIn("performance-web", names)
        self.assertLess(
            result["context_plan"]["metrics"]["packs_loaded"],
            result["context_plan"]["metrics"]["candidate_packs"],
        )

    def test_woocommerce_payment_overlap_activates_required_concerns(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            init_project(root)
            write(
                root,
                "gateway.php",
                WORDPRESS_WOO
                + "\nclass Vibe_Gateway extends WC_Payment_Gateway {}\n",
            )

            result = self.router.plan(
                root,
                "Add a Stripe payment gateway with webhook refund handling",
                ["gateway.php"],
            )

        names = {row["name"] for row in result["packs"]}
        self.assertTrue(
            {
                "php",
                "wordpress",
                "woocommerce",
                "payments",
                "external-http",
                "security-web",
                "performance-web",
            }.issubset(names)
        )
        self.assertEqual(result["task"]["risk"]["tier"], 3)
        self.assertTrue(result["interactions"])
        self.assertGreaterEqual(len(result["integration_points"]), 3)

    def test_wordpress_rest_external_api_composes_without_duplicate_context(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            init_project(root)
            write(
                root,
                "rest-controller.php",
                WORDPRESS_WOO
                + "\nregister_rest_route('vibe/v1', '/sync', ["
                + "'permission_callback' => 'current_user_can']);\n",
            )

            result = self.router.plan(
                root,
                "Add REST endpoint that calls an external API",
                ["rest-controller.php"],
            )

        names = [row["name"] for row in result["packs"]]
        self.assertIn("wordpress-rest", names)
        self.assertIn("external-http", names)
        self.assertIn("security-web", names)
        self.assertIn("performance-web", names)
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(
            len(result["integration_points"]),
            len(set(result["integration_points"])),
        )

    def test_large_generic_project_keeps_project_intelligence_without_domain_noise(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            init_project(root)
            for index in range(305):
                write(root, f"src/module_{index}.py", "VALUE = 1\n")
            write(root, "ARCHITECTURE.md", "# Architecture\n")
            write(root, "PROJECT.md", "# Project\n")

            result = self.router.plan(
                root,
                "Add report export",
                ["src/module_1.py"],
            )

        names = {row["name"] for row in result["packs"]}
        self.assertEqual(result["project"]["complexity"]["level"], "large")
        self.assertTrue(result["core"]["large_project_awareness"])
        self.assertTrue(
            result["context_plan"]["coverage"]["project_intelligence_preserved"]
        )
        self.assertNotIn("wordpress", names)
        self.assertNotIn("woocommerce", names)

    def test_browser_pack_can_overlap_wordpress_without_becoming_wordpress_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            init_project(root)
            write(root, "plugin.php", WORDPRESS_WOO)
            write(
                root,
                "src/admin.tsx",
                "window.wp = window.wp || {}; const view = wp.data.select('core');\n",
            )

            result = self.router.plan(
                root,
                "Update the React admin settings panel",
                ["src/admin.tsx"],
            )

        names = {row["name"] for row in result["packs"]}
        self.assertIn("browser-js", names)
        self.assertIn("wordpress", names)
        self.assertIn("woocommerce", names)


class ExecutionPlanTests(unittest.TestCase):
    def setUp(self):
        self.planner = load_script("execution_plan.py")

    def test_large_or_significant_task_gets_execution_plan_but_one_agent_default(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            init_project(root)
            write(
                root,
                "gateway.php",
                WORDPRESS_WOO
                + "\nclass Vibe_Gateway extends WC_Payment_Gateway {}\n",
            )
            result = self.planner.draft(
                root,
                "Add Stripe payment gateway with webhook processing",
                ["gateway.php"],
            )

        self.assertTrue(result["execution_plan_required"])
        self.assertEqual(result["coordination"]["recommended_parallelism"], 1)
        self.assertEqual(len(result["workstreams"]), 1)
        self.assertGreaterEqual(len(result["integration_points"]), 3)
        self.assertIn(
            "objective_done",
            result["completion_levels"],
        )

    def test_plan_validation_rejects_unknown_dependency_and_missing_owner(self):
        result = self.planner.validate_plan({
            "workstreams": [
                {
                    "id": "backend",
                    "owner": "",
                    "depends_on": ["missing"],
                }
            ],
            "integration_points": [],
        })
        self.assertEqual(result["gate"], "BLOCK")
        self.assertTrue(
            any("requires owner" in failure for failure in result["failures"])
        )
        self.assertTrue(
            any("unknown dependency" in failure for failure in result["failures"])
        )

    def test_plan_drift_requires_approval_for_architecture_or_security_change(self):
        plan = {"objective": "Add checkout integration"}
        result = self.planner.evaluate_drift(
            plan,
            {
                "scope": False,
                "architecture": True,
                "data_semantics": False,
                "public_api": False,
                "security_posture": True,
                "recurring_cost": False,
            },
        )
        self.assertEqual(result["gate"], "APPROVAL_REQUIRED")
        self.assertEqual(
            set(result["triggered"]),
            {"architecture", "security_posture"},
        )

    def test_plan_drift_allows_local_execution_detail(self):
        result = self.planner.evaluate_drift(
            {"objective": "Refactor local helper"},
            {key: False for key in self.planner.APPROVAL_TRIGGERS},
        )
        self.assertEqual(result["gate"], "CONTINUE")
        self.assertFalse(result["approval_required"])


class ContextRoutingContractTests(unittest.TestCase):
    def test_pack_config_paths_exist_and_are_unique(self):
        config = json.loads(
            (ROOT / "config" / "context-routing.json").read_text(
                encoding="utf-8"
            )
        )
        paths = [row["path"] for row in config["packs"].values()]
        self.assertEqual(len(paths), len(set(paths)))
        for rel in paths:
            self.assertTrue((ROOT / rel).exists(), rel)

    def test_pack_contract_has_required_sections(self):
        config = json.loads(
            (ROOT / "config" / "context-routing.json").read_text(
                encoding="utf-8"
            )
        )
        required = (
            "## Activation",
            "## Constraints",
            "## Risks",
            "## Integration points",
            "## Required checks",
            "## Avoid",
        )
        for row in config["packs"].values():
            text = (ROOT / row["path"]).read_text(encoding="utf-8")
            for heading in required:
                self.assertIn(heading, text, row["path"])


if __name__ == "__main__":
    unittest.main()
