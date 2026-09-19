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
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
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
                "supported": True,
                "exists": True,
                "version_exists": True,
                "repository": "https://example.test/repo",
                "license": "MIT",
            },
            {"checked": False, "vulnerabilities": [], "warning": "offline"},
            "1.0.0",
        )
        self.assertEqual(decision, "REVIEW REQUIRED")

    def test_accept_complete_baseline(self):
        mod = load_script("dependency_guard.py")
        decision, _ = mod.decide(
            {
                "supported": True,
                "exists": True,
                "version_exists": True,
                "repository": "https://example.test/repo",
                "license": "MIT",
            },
            {"checked": True, "vulnerabilities": []},
            "1.0.0",
        )
        self.assertEqual(decision, "ACCEPT")


class BootstrapTests(unittest.TestCase):
    def test_bootstrap_does_not_overwrite_existing_status(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            status = root / "STATUS.md"
            status.write_text("keep me\n", encoding="utf-8")
            cmd = [
                sys.executable,
                str(ROOT / "scripts" / "bootstrap_project.py"),
                "--root",
                str(root),
                "--profile",
                "minimal",
                "--objective",
                "Test objective",
                "--json",
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
                sys.executable,
                str(ROOT / "scripts" / "bootstrap_project.py"),
                "--root",
                str(root),
                "--profile",
                "standard",
                "--objective",
                "Test objective",
                "--json",
            ]
            out = subprocess.run(cmd, text=True, capture_output=True, check=True)
            data = json.loads(out.stdout)
            self.assertFalse((root / "PROJECT.md").exists())
            self.assertTrue(any("PROJECT.md: insufficient" in item for item in data["skipped"]))


if __name__ == "__main__":
    unittest.main()
