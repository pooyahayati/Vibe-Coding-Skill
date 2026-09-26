from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = ROOT / "scripts" / "run_real_world_validations.py"
    spec = importlib.util.spec_from_file_location(
        "test_run_real_world_validations",
        path,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RealWorldRoutingExpectationTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_validator()

    def route(self):
        return {
            "project": {"complexity": {"level": "large"}},
            "task": {"risk": {"tier": 3}},
            "packs": [
                {"name": "php"},
                {"name": "wordpress"},
                {"name": "woocommerce"},
                {"name": "payments"},
                {"name": "external-http"},
                {"name": "security-web"},
                {"name": "performance-web"},
            ],
            "integration_points": [
                "checkout ↔ payment adapter",
                "gateway ↔ callback/webhook",
                "payment state ↔ order/business state",
                "application ↔ remote service",
                "untrusted input ↔ privileged/state-changing operation",
            ],
            "context_plan": {
                "metrics": {
                    "candidate_packs": 9,
                    "packs_loaded": 7,
                    "context_files_selected": 9,
                    "estimated_skill_context_bytes": 12000,
                    "project_files_considered": 600,
                    "project_text_files_scanned": 600,
                    "project_text_bytes_scanned": 1000000,
                },
                "coverage": {
                    "project_intelligence_preserved": True,
                },
            },
        }

    def plan(self):
        return {
            "execution_plan_required": True,
            "mode": "execution-plan",
            "workstreams": [{"id": "implementation"}],
        }

    def test_expectations_accept_payment_overlap_with_reduction(self):
        checks, details = self.mod.validate_routing_expectations(
            self.route(),
            self.plan(),
            {
                "expected_complexity_at_least": "medium",
                "expected_min_tier": 3,
                "required_packs": [
                    "php",
                    "wordpress",
                    "woocommerce",
                    "payments",
                    "external-http",
                    "security-web",
                    "performance-web",
                ],
                "forbidden_packs": ["wordpress-rest"],
                "max_loaded_packs": 8,
                "require_context_reduction": True,
                "min_pack_reduction_ratio": 0.1,
                "require_project_intelligence": True,
                "require_execution_plan": True,
                "min_integration_points": 5,
            },
        )
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual(details["packs_loaded"], 7)
        self.assertGreater(details["pack_reduction_ratio"], 0)

    def test_expectations_reject_forbidden_domain_noise(self):
        route = self.route()
        route["packs"] = [{"name": "wordpress"}]
        route["context_plan"]["metrics"]["packs_loaded"] = 1

        checks, _ = self.mod.validate_routing_expectations(
            route,
            self.plan(),
            {
                "required_packs": [],
                "forbidden_packs": ["wordpress", "woocommerce"],
                "require_context_reduction": True,
            },
        )
        self.assertFalse(checks["forbidden_packs"])
        self.assertTrue(checks["context_reduction"])

    def test_expectations_enforce_complexity_and_tier_bounds(self):
        route = self.route()
        route["project"]["complexity"]["level"] = "small"
        route["task"]["risk"]["tier"] = 2

        checks, _ = self.mod.validate_routing_expectations(
            route,
            self.plan(),
            {
                "expected_complexity_at_least": "large",
                "expected_min_tier": 3,
                "expected_max_tier": 3,
                "required_packs": [],
                "forbidden_packs": [],
            },
        )
        self.assertFalse(checks["complexity_floor"])
        self.assertFalse(checks["tier_floor"])
        self.assertTrue(checks["tier_ceiling"])


if __name__ == "__main__":
    unittest.main()
