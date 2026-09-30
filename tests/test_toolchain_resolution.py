from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.graphify_compat as graphify_compat
import scripts.toolchain_resolution as resolution
import scripts.toolchain_runtime as runtime


ROOT = Path(__file__).resolve().parents[1]


class ToolchainResolutionTests(unittest.TestCase):
    def test_toolchain_config_uses_latest_compatible_policy(self):
        cfg = json.loads(
            (ROOT / "config" / "toolchain.json").read_text(encoding="utf-8")
        )
        for tool in ("graphify", "trivy"):
            entry = cfg[tool]
            self.assertEqual(entry["channel"], "stable")
            self.assertEqual(entry["resolution"], "latest-compatible-stable")
            self.assertTrue(entry["last_known_good"])
            self.assertNotIn("approved", entry)
            self.assertNotIn("latest_seen", entry)

    def test_resolver_selects_latest_candidate(self):
        cfg = {
            "graphify": {
                "channel": "stable",
                "resolution": "latest-compatible-stable",
                "last_known_good": "old",
            }
        }
        with mock.patch.object(
            resolution,
            "contract",
            side_effect=lambda tool, version=None: {
                "version": version or "new",
                "ok": True,
            },
        ):
            result = resolution.resolve("graphify", cfg)
        self.assertEqual(result["selected_version"], "new")
        self.assertFalse(result["fallback_used"])

    def test_resolver_falls_back_when_latest_fails(self):
        cfg = {
            "graphify": {
                "channel": "stable",
                "resolution": "latest-compatible-stable",
                "last_known_good": "old",
            }
        }

        def fake_contract(tool, version=None):
            return (
                {"version": "new", "ok": False}
                if version is None
                else {"version": version, "ok": True}
            )

        with mock.patch.object(resolution, "contract", side_effect=fake_contract):
            result = resolution.resolve("graphify", cfg)
        self.assertEqual(result["selected_version"], "old")
        self.assertTrue(result["fallback_used"])
        self.assertEqual(result["source"], "last-known-good")

    def test_resolver_rejects_broken_fallback(self):
        cfg = {
            "graphify": {
                "channel": "stable",
                "resolution": "latest-compatible-stable",
                "last_known_good": "old",
            }
        }
        with mock.patch.object(
            resolution,
            "contract",
            side_effect=lambda tool, version=None: {
                "version": version or "new",
                "ok": False,
            },
        ):
            with self.assertRaisesRegex(RuntimeError, "last-known-good"):
                resolution.resolve("graphify", cfg)

    def test_contract_timeout_becomes_structured_failure(self):
        with mock.patch.object(
            resolution.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(["graphify"], 1),
        ):
            result = resolution.contract("graphify")
        self.assertFalse(result["ok"])
        self.assertFalse(result["command_ok"])
        self.assertTrue(result["timed_out"])

    def test_timeout_candidate_still_gets_one_fallback_attempt(self):
        cfg = {
            "graphify": {
                "channel": "stable",
                "resolution": "latest-compatible-stable",
                "last_known_good": "old",
            }
        }
        with mock.patch.object(
            resolution,
            "contract",
            side_effect=[
                {"version": None, "ok": False, "timed_out": True},
                {"version": "old", "ok": True},
            ],
        ) as contract:
            result = resolution.resolve("graphify", cfg)
        self.assertEqual(contract.call_count, 2)
        self.assertEqual(result["selected_version"], "old")
        self.assertTrue(result["fallback_used"])

    def test_runtime_command_uses_exact_graphify_version(self):
        with mock.patch.object(
            runtime.shutil,
            "which",
            side_effect=lambda name: None if name == "graphify" else "/usr/bin/uvx",
        ):
            cmd = runtime.graphify_command("1.2.3", ["--version"])
        self.assertEqual(
            cmd[:4],
            ["uvx", "--from", "graphifyy==1.2.3", "graphify"],
        )

    def test_runtime_command_rejects_unverified_installed_graphify(self):
        class Result:
            returncode = 0
            stdout = "Graphify 9.9.9"
            stderr = ""

        with mock.patch.object(
            runtime.shutil,
            "which",
            side_effect=lambda name: "/usr/bin/graphify" if name == "graphify" else None,
        ), mock.patch.object(runtime.subprocess, "run", return_value=Result()):
            with self.assertRaisesRegex(RuntimeError, "uvx runtime"):
                runtime.graphify_command("1.2.3", ["--version"])

    def test_runtime_module_imports_in_fresh_interpreter(self):
        result = subprocess.run(
            [sys.executable, "-c", "import scripts.toolchain_runtime"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_graphify_skill_version_works_without_root_version_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "SKILL.md").write_text(
                '---\nname: demo\nmetadata:\n  version: "1.2.3"\n---\n',
                encoding="utf-8",
            )
            with mock.patch.object(graphify_compat, "ROOT", root):
                self.assertEqual(graphify_compat.skill_version(), "1.2.3")


if __name__ == "__main__":
    unittest.main()
