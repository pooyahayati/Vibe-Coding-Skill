from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import dependency_guard
import graph_manager
import integration_check
import risk_classifier

class RiskClassifierTests(unittest.TestCase):
    def test_catalog_tiers_and_approvals(self):
        catalog = json.loads((ROOT / "evals" / "scenarios.json").read_text(encoding="utf-8"))
        for scenario in catalog["scenarios"]:
            with self.subTest(scenario=scenario["id"]):
                result = risk_classifier.classify(scenario["prompt"])
                self.assertEqual(result.tier, scenario["expected_tier"])
                self.assertEqual(result.approval_required, scenario["approval_required"])

    def test_sensitive_path_escalates(self):
        result = risk_classifier.classify("Refactor helper", ["auth/tokens.py"])
        self.assertGreaterEqual(result.tier, 2)

    def test_explicit_critical_flag_wins(self):
        result = risk_classifier.classify("Routine operation", flags=["production"])
        self.assertEqual(result.tier, 3)
        self.assertTrue(result.approval_required)

class DependencyAdapterTests(unittest.TestCase):
    def test_maven_coordinate_parser(self):
        self.assertEqual(dependency_guard._maven_parts("org.slf4j:slf4j-api"), ("org.slf4j", "slf4j-api"))
        with self.assertRaises(ValueError):
            dependency_guard._maven_parts("slf4j-api")

    def test_go_proxy_escape(self):
        self.assertEqual(dependency_guard._go_escape("GitHub.com/A!B"), "!git!hub.com/!a!!!b")

    def test_nuget_service_resource_selection(self):
        index = {"resources": [
            {"@id": "https://flat/", "@type": "PackageBaseAddress/3.0.0"},
            {"@id": "https://search/", "@type": ["SearchQueryService/3.5.0"]},
        ]}
        self.assertEqual(dependency_guard._nuget_resource(index, "PackageBaseAddress"), "https://flat/")
        self.assertEqual(dependency_guard._nuget_resource(index, "SearchQueryService"), "https://search/")

class IntegrationHelpersTests(unittest.TestCase):
    def test_parse_github_remote(self):
        self.assertEqual(integration_check.parse_github_remote("https://github.com/pooyahayati/Vibe-Coding-Skill.git"), "pooyahayati/Vibe-Coding-Skill")
        self.assertEqual(integration_check.parse_github_remote("git@github.com:pooyahayati/Vibe-Coding-Skill.git"), "pooyahayati/Vibe-Coding-Skill")

    def test_count_trivy_findings(self):
        counts = integration_check.count_trivy_findings({"Results": [{"Vulnerabilities": [{}, {}], "Misconfigurations": [{}], "Secrets": [{}]}]})
        self.assertEqual(counts["vulnerabilities"], 2)
        self.assertEqual(counts["misconfigurations"], 1)
        self.assertEqual(counts["secrets"], 1)

class GraphManagerTests(unittest.TestCase):
    def test_graph_state_freshness_tracks_git_head(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "app.py").write_text("print('a')\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Eval", "-c", "user.email=eval@example.test", "commit", "-qm", "init"], cwd=root, check=True)
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
            (root / "graphify-out").mkdir()
            (root / "graphify-out" / "graph.json").write_text("{}\n", encoding="utf-8")
            (root / ".vibe").mkdir()
            (root / ".vibe" / "graph-state.json").write_text(json.dumps({"source_commit": head, "provider": "graphify", "provider_version": "0.0.0"}), encoding="utf-8")
            self.assertFalse(graph_manager.status(root)["stale"])
            (root / "app.py").write_text("print('b')\n", encoding="utf-8")
            subprocess.run(["git", "add", "app.py"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Eval", "-c", "user.email=eval@example.test", "commit", "-qm", "change"], cwd=root, check=True)
            self.assertTrue(graph_manager.status(root)["stale"])

if __name__ == "__main__":
    unittest.main()
