from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DependencyGuardTests(unittest.TestCase):
    def test_reject_missing_package(self):
        mod = load_script("dependency_guard.py")
        decision, _ = mod.decide(
            {"supported": True, "exists": False, "version_exists": False},
            {"checked": True, "vulnerabilities": []},
            "1.0.0",
        )
        self.assertEqual(decision, "REJECT")

    def test_review_when_osv_missing(self):
        mod = load_script("dependency_guard.py")
        decision, _ = mod.decide(
            {
                "supported": True, "exists": True, "version_exists": True,
                "repository": "https://example.test/repo", "license": "MIT",
            },
            {"checked": False, "vulnerabilities": [], "warning": "offline"},
            "1.0.0",
        )
        self.assertEqual(decision, "REVIEW REQUIRED")

    def test_accept_complete_baseline(self):
        mod = load_script("dependency_guard.py")
        decision, _ = mod.decide(
            {
                "supported": True, "exists": True, "version_exists": True,
                "repository": "https://example.test/repo", "license": "MIT",
            },
            {"checked": True, "vulnerabilities": []},
            "1.0.0",
        )
        self.assertEqual(decision, "ACCEPT")

    def test_vulnerable_version_requires_review(self):
        mod = load_script("dependency_guard.py")
        decision, reasons = mod.decide(
            {
                "supported": True, "exists": True, "version_exists": True,
                "repository": "https://example.test/repo", "license": "MIT",
            },
            {"checked": True, "vulnerabilities": [{"id": "TEST-1"}]},
            "1.0.0",
        )
        self.assertEqual(decision, "REVIEW REQUIRED")
        self.assertTrue(any("vulnerabilities" in r for r in reasons))


class RiskClassifierTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_script("risk_classifier.py")

    def test_tiny_typo(self):
        self.assertEqual(self.mod.classify("Change one typo in the footer text.")["tier"], 0)

    def test_auth_is_significant_and_requires_approval(self):
        result = self.mod.classify("Change authentication from session cookies to JWTs across the application.")
        self.assertEqual(result["tier"], 2)
        self.assertTrue(result["approval_required"])

    def test_destructive_production_migration_is_critical(self):
        result = self.mod.classify("Drop the customer table and migrate production data.")
        self.assertEqual(result["tier"], 3)
        self.assertTrue(result["approval_required"])

    def test_paths_can_raise_tier(self):
        result = self.mod.classify("small refactor", ["src/auth/session.py"])
        self.assertGreaterEqual(result["tier"], 2)


class BootstrapTests(unittest.TestCase):
    def test_bootstrap_does_not_overwrite_existing_status(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            status = root / "STATUS.md"
            status.write_text("keep me\n", encoding="utf-8")
            cmd = [
                sys.executable, str(ROOT / "scripts" / "bootstrap_project.py"),
                "--root", str(root), "--profile", "minimal",
                "--objective", "Test objective", "--json",
            ]
            out = subprocess.run(cmd, text=True, capture_output=True, check=True)
            data = json.loads(out.stdout)
            self.assertEqual(status.read_text(encoding="utf-8"), "keep me\n")
            self.assertTrue(any("STATUS.md: exists" in item for item in data["skipped"]))
            self.assertTrue((root / ".vibe" / "project.json").exists())

    def test_standard_skips_project_doc_without_product_facts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            cmd = [
                sys.executable, str(ROOT / "scripts" / "bootstrap_project.py"),
                "--root", str(root), "--profile", "standard",
                "--objective", "Test objective", "--json",
            ]
            out = subprocess.run(cmd, text=True, capture_output=True, check=True)
            data = json.loads(out.stdout)
            self.assertFalse((root / "PROJECT.md").exists())
            self.assertTrue(any("PROJECT.md: insufficient" in item for item in data["skipped"]))


class IntegrationGuardTests(unittest.TestCase):
    def _fake_exe(self, root: Path, name: str, body: str) -> None:
        path = root / name
        path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    def test_tier2_reports_stale_graph_without_mutating_repo(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as bindir:
            root = Path(td)
            binroot = Path(bindir)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "app.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "init"], cwd=root, check=True)
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
            (root / ".vibe").mkdir()
            (root / ".vibe" / "graph-state.json").write_text(
                json.dumps({"source_commit": "0" * 40, "provider": "graphify"}),
                encoding="utf-8",
            )
            self._fake_exe(binroot, "graphify", 'echo "graphify 0.9.64"')
            self._fake_exe(binroot, "trivy", 'echo "Version: 0.74.0"')
            env = os.environ.copy()
            env["PATH"] = str(binroot) + os.pathsep + env["PATH"]
            out = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "integration_guard.py"),
                 "--root", str(root), "--tier", "2", "--json"],
                text=True, capture_output=True, env=env, check=True,
            )
            data = json.loads(out.stdout)
            self.assertEqual(data["status"], "WARN")
            self.assertTrue(data["checks"]["graph_state"]["stale"])
            self.assertEqual(
                subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
                head,
            )


if __name__ == "__main__":
    unittest.main()
