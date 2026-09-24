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

    def test_new_wordpress_project_can_route_from_task_evidence_before_files_exist(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            init_project(root)
            result = self.router.plan(
                root,
                "Create a new WooCommerce plugin for order exports",
                [],
            )

        names = {row["name"] for row in result["packs"]}
        self.assertIn("wordpress", names)
        self.assertIn("woocommerce", names)
        self.assertIn("php", names)

    def test_unrelated_backend_task_does_not_load_browser_pack_just_because_tsx_exists(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            init_project(root)
            write(root, "plugin.php", WORDPRESS_WOO)
            write(root, "src/admin.tsx", "window.wp = window.wp || {};\n")
            write(root, "src/service.php", "<?php function service_change() {}\n")

            result = self.router.plan(
                root,
                "Refactor PHP order service helper",
                ["src/service.php"],
            )

        names = {row["name"] for row in result["packs"]}
        self.assertNotIn("browser-js", names)
        self.assertIn("php", names)
        self.assertIn("wordpress", names)

    def test_project_invariants_are_extracted_without_loading_full_docs_for_tiny_task(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            init_project(root)
            write(root, "plugin.php", WORDPRESS_WOO)
            write(
                root,
                "PROJECT.md",
                "# Project\n\n## Invariants\n"
                "- Never write directly to WooCommerce internal order tables.\n"
                "- Preserve backward-compatible public hooks.\n",
            )
            result = self.router.plan(
                root,
                "Change button label text only",
                ["plugin.php"],
            )

        detected = result["project"]["detected_invariants"]
        self.assertEqual(len(detected), 2)
        self.assertTrue(
            any("internal order tables" in row["text"] for row in detected)
        )
        self.assertTrue(
            result["context_plan"]["coverage"]["project_invariants_preserved"]
        )
        self.assertNotIn("PROJECT.md", result["context_plan"]["load"])

    def test_large_generic_project_always_loads_project_intelligence_policy(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            init_project(root)
            for index in range(305):
                write(root, f"src/module_{index}.py", "VALUE = 1\n")
            result = self.router.plan(
                root,
                "Update report copy",
                ["src/module_1.py"],
            )

        self.assertIn(
            "references/project-intelligence.md",
            result["core"]["references"],
        )

    def test_tiny_wording_cannot_suppress_higher_risk_interaction(self):
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
                "Rename payment webhook handler and change webhook state transition",
                ["gateway.php"],
            )

        names = {row["name"] for row in result["packs"]}
        self.assertIn("payments", names)
        self.assertIn("external-http", names)
        self.assertEqual(result["task"]["risk"]["tier"], 3)

    def test_read_only_wordpress_rest_task_stays_standard_but_loads_security(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            init_project(root)
            write(
                root,
                "rest.php",
                "<?php\n/* Plugin Name: REST Test */\n"
                "register_rest_route('demo/v1', '/items', ["
                "'methods' => 'GET', 'permission_callback' => '__return_true']);\n",
            )
            result = self.router.plan(
                root,
                "Add a read-only REST endpoint for public catalog data",
                ["rest.php"],
            )

        names = {row["name"] for row in result["packs"]}
        self.assertIn("wordpress-rest", names)
        self.assertIn("security-web", names)
        self.assertEqual(result["task"]["risk"]["tier"], 1)

    def test_generated_dist_files_do_not_make_project_large(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            init_project(root)
            write(root, "src/app.php", "<?php\n")
            for index in range(350):
                write(root, f"dist/chunk_{index}.js", "compiled = true;\n")
            result = self.router.plan(
                root,
                "Refactor PHP helper",
                ["src/app.php"],
            )

        self.assertEqual(result["project"]["complexity"]["level"], "small")
        self.assertGreater(
            result["project"]["complexity"]["raw_file_count"],
            result["project"]["complexity"]["file_count"],
        )

    def test_large_mixed_monorepo_does_not_load_wordpress_for_unrelated_service(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            init_project(root)
            write(
                root,
                "apps/store/plugin.php",
                WORDPRESS_WOO,
            )
            for index in range(305):
                write(
                    root,
                    f"services/api/module_{index}.py",
                    "VALUE = 1\n",
                )

            result = self.router.plan(
                root,
                "Refactor report export service",
                ["services/api/module_1.py"],
            )

        names = {row["name"] for row in result["packs"]}
        self.assertEqual(
            result["project"]["complexity"]["level"],
            "large",
        )
        self.assertNotIn("wordpress", names)
        self.assertNotIn("woocommerce", names)
        self.assertNotIn("php", names)
        self.assertTrue(result["core"]["large_project_awareness"])

    def test_documentation_mentions_do_not_activate_platform_pack(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            init_project(root)
            write(
                root,
                "README.md",
                "# Integration notes\nMentions WooCommerce and WC_Order for comparison.\n",
            )
            write(root, "src/app.py", "VALUE = 1\n")

            result = self.router.plan(
                root,
                "Refactor Python report helper",
                ["src/app.py"],
            )

        names = {row["name"] for row in result["packs"]}
        self.assertNotIn("wordpress", names)
        self.assertNotIn("woocommerce", names)

    def test_interaction_added_pack_without_direct_evidence_is_explainable(self):
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
                "Add payment method",
                ["gateway.php"],
            )

        rows = {row["name"]: row for row in result["packs"]}
        self.assertIn("security-web", rows)
        self.assertTrue(rows["security-web"]["evidence"])
        self.assertTrue(
            any(
                value.startswith("required-by:")
                for value in rows["security-web"]["evidence"]
            )
        )

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

    def test_tiny_wordpress_task_does_not_require_execution_plan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            init_project(root)
            write(root, "plugin.php", WORDPRESS_WOO)
            result = self.planner.draft(
                root,
                "Change checkout button label text only",
                ["plugin.php"],
            )

        self.assertFalse(result["execution_plan_required"])
        self.assertEqual(result["mode"], "light-task")
        self.assertEqual(result["draft_status"], "light-task-ready")

    def test_plan_validation_rejects_unknown_dependency_and_missing_owner(self):
        result = self.planner.validate_plan({
            "objective": "Test execution coordination",
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

    def test_plan_validation_rejects_dependency_cycle(self):
        result = self.planner.validate_plan({
            "objective": "Test execution coordination",
            "workstreams": [
                {
                    "id": "backend",
                    "owner": "agent-a",
                    "scope": ["src/backend"],
                    "depends_on": ["frontend"],
                },
                {
                    "id": "frontend",
                    "owner": "agent-b",
                    "scope": ["src/frontend"],
                    "depends_on": ["backend"],
                },
            ],
            "integration_points": [],
        })
        self.assertEqual(result["gate"], "BLOCK")
        self.assertTrue(
            any("dependency cycle" in failure for failure in result["failures"])
        )

    def test_plan_validation_rejects_overlapping_multi_agent_ownership(self):
        result = self.planner.validate_plan({
            "objective": "Test execution coordination",
            "workstreams": [
                {
                    "id": "api",
                    "owner": "agent-a",
                    "scope": ["src"],
                    "depends_on": [],
                },
                {
                    "id": "payments",
                    "owner": "agent-b",
                    "scope": ["src/payments"],
                    "depends_on": [],
                },
            ],
            "integration_points": [],
        })
        self.assertEqual(result["gate"], "BLOCK")
        self.assertTrue(
            any("ownership scopes overlap" in failure for failure in result["failures"])
        )

    def test_plan_validation_rejects_unknown_integration_workstream(self):
        result = self.planner.validate_plan({
            "objective": "Coordinate API integration",
            "workstreams": [
                {
                    "id": "backend",
                    "owner": "agent-a",
                    "scope": ["src/backend"],
                    "depends_on": [],
                    "completion": ["tests pass"],
                }
            ],
            "integration_points": [
                {
                    "id": "api",
                    "boundary": "backend ↔ client",
                    "owner": "lead-agent",
                    "status": "confirmed",
                    "producers": ["backend"],
                    "consumers": ["missing-client"],
                    "contract": "versioned schema",
                    "required_evidence": ["integration test"],
                }
            ],
        })
        self.assertEqual(result["gate"], "BLOCK")
        self.assertTrue(
            any(
                "references unknown workstreams" in failure
                for failure in result["failures"]
            )
        )

    def test_plan_validation_enforces_single_writer_for_shared_contract(self):
        result = self.planner.validate_plan({
            "objective": "Coordinate shared API schema",
            "coordination": {"recommended_parallelism": 2},
            "workstreams": [
                {
                    "id": "backend",
                    "owner": "agent-a",
                    "scope": ["src/backend"],
                    "depends_on": [],
                    "shared_contracts": ["contracts/checkout.json"],
                    "completion": ["backend tests pass"],
                },
                {
                    "id": "frontend",
                    "owner": "agent-b",
                    "scope": ["src/frontend"],
                    "depends_on": [],
                    "shared_contracts": ["contracts/checkout.json"],
                    "completion": ["frontend tests pass"],
                },
            ],
            "integration_points": [],
        })
        self.assertEqual(result["gate"], "BLOCK")
        self.assertTrue(
            any(
                "shared contract has multiple writers" in failure
                for failure in result["failures"]
            )
        )

    def test_plan_validation_rejects_invalid_parallelism(self):
        result = self.planner.validate_plan({
            "objective": "Coordinate work",
            "coordination": {"recommended_parallelism": 0},
            "workstreams": [
                {
                    "id": "implementation",
                    "owner": "lead-agent",
                    "scope": ["src"],
                    "depends_on": [],
                    "completion": ["tests pass"],
                }
            ],
            "integration_points": [],
        })
        self.assertEqual(result["gate"], "BLOCK")
        self.assertIn(
            "recommended_parallelism must be a positive integer",
            result["failures"],
        )

    def test_plan_validation_requires_integration_contract(self):
        result = self.planner.validate_plan({
            "objective": "Test execution coordination",
            "workstreams": [
                {
                    "id": "backend",
                    "owner": "lead-agent",
                    "scope": ["src/backend"],
                    "depends_on": [],
                }
            ],
            "integration_points": [
                {
                    "id": "api-boundary",
                    "boundary": "browser ↔ API",
                    "owner": "lead-agent",
                    "status": "candidate",
                    "producers": [],
                    "consumers": [],
                    "contract": "",
                    "required_evidence": ["integration test"],
                }
            ],
        })
        self.assertEqual(result["gate"], "BLOCK")
        self.assertTrue(
            any("requires verified contract description" in failure for failure in result["failures"])
        )

    def test_valid_multi_workstream_plan_passes(self):
        result = self.planner.validate_plan({
            "objective": "Deliver checkout integration",
            "coordination": {"recommended_parallelism": 2},
            "workstreams": [
                {
                    "id": "backend",
                    "owner": "agent-a",
                    "scope": ["src/backend"],
                    "depends_on": [],
                    "completion": ["backend tests pass"],
                },
                {
                    "id": "frontend",
                    "owner": "agent-b",
                    "scope": ["src/frontend"],
                    "depends_on": ["backend"],
                    "completion": ["frontend tests pass"],
                },
            ],
            "integration_points": [
                {
                    "id": "checkout-api",
                    "boundary": "frontend ↔ backend checkout API",
                    "owner": "lead-agent",
                    "status": "confirmed",
                    "producers": ["backend"],
                    "consumers": ["frontend"],
                    "contract": "versioned request/response schema",
                    "required_evidence": ["contract integration test"],
                }
            ],
        })
        self.assertEqual(result["gate"], "PASS")

    def test_plan_drift_detects_changed_path_outside_owned_scope(self):
        plan = {
            "objective": "Change checkout API",
            "workstreams": [
                {
                    "id": "checkout",
                    "owner": "lead-agent",
                    "scope": ["src/checkout"],
                    "depends_on": [],
                }
            ],
        }
        result = self.planner.evaluate_drift(
            plan,
            {
                **{key: False for key in self.planner.APPROVAL_TRIGGERS},
                "changed_paths": ["src/payments/gateway.php"],
            },
        )
        self.assertEqual(result["gate"], "APPROVAL_REQUIRED")
        self.assertIn("scope", result["triggered"])

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
