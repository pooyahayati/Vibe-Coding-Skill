from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.toolchain_resolution as resolution
import scripts.toolchain_runtime as runtime
import scripts.graphify_compat as graphify_compat


ROOT = Path(__file__).resolve().parents[1]


class ToolchainResolutionTests(unittest.TestCase):
    def test_toolchain_config_uses_latest_compatible_policy(self):
        cfg = json.loads(
            (ROOT / "config" / "toolchain.json").read_text(encoding="utf-8")
        )
        for tool in ("graphify", "trivy"):
            entry = cfg[tool]
            self.assertEqual(entry["channel"], "stable")
            self.assertEqual(
                entry["resolution"],
                "latest-compatible-stable",
            )
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
            if version is None:
                return {"version": "new", "ok": False}
            return {"version": version, "ok": True}

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

    def test_timeout_on_latest_candidate_triggers_one_fallback_attempt(self):
        cfg = {
            "graphify": {
                "channel": "stable",
                "resolution": "latest-compatible-stable",
                "last_known_good": "old",
            }
        }
        fallback_json = json.dumps({"version": "old", "ok": True})
        completed = subprocess.CompletedProcess(
            args=["compat"],
            returncode=0,
            stdout=fallback_json,
            stderr="",
        )
        with mock.patch.object(
            resolution.subprocess,
            "run",
            side_effect=[
                subprocess.TimeoutExpired(cmd=["compat"], timeout=900),
                completed,
            ],
        ) as run_mock:
            result = resolution.resolve("graphify", cfg)

        self.assertEqual(run_mock.call_count, 2)
        self.assertEqual(result["selected_version"], "old")
        self.assertTrue(result["fallback_used"])
        self.assertIn("timed out", result["candidate"]["error"])

    def test_contract_uses_current_python_interpreter(self):
        completed = subprocess.CompletedProcess(
            args=["compat"],
            returncode=0,
            stdout=json.dumps({"version": "1.2.3", "ok": True}),
            stderr="",
        )
        with mock.patch.object(
            resolution.subprocess,
            "run",
            return_value=completed,
        ) as run_mock:
            resolution.contract("graphify", "1.2.3")
        self.assertEqual(run_mock.call_args.args[0][0], resolution.sys.executable)

    def test_runtime_command_uses_exact_graphify_version(self):
        def which(name):
            return None if name == "graphify" else "/usr/bin/uvx"

        with mock.patch.object(runtime.shutil, "which", side_effect=which):
            cmd = runtime.graphify_command("1.2.3", ["--version"])
        self.assertEqual(
            cmd[:4],
            ["uvx", "--from", "graphifyy==1.2.3", "graphify"],
        )

    def test_runtime_command_rejects_unverified_installed_graphify(self):
        def which(name):
            if name == "graphify":
                return "/usr/bin/graphify"
            return None

        completed = subprocess.CompletedProcess(
            args=["graphify", "--version"],
            returncode=0,
            stdout="Graphify 9.9.9",
            stderr="",
        )
        with (
            mock.patch.object(runtime.shutil, "which", side_effect=which),
            mock.patch.object(runtime.subprocess, "run", return_value=completed),
        ):
            with self.assertRaisesRegex(RuntimeError, "uvx runtime"):
                runtime.graphify_command("1.2.3", ["--version"])

    def test_graphify_skill_version_works_without_root_version_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "SKILL.md").write_text(
                '---\nmetadata:\n  version: "9.8.7"\n---\n',
                encoding="utf-8",
            )
            with mock.patch.object(graphify_compat, "ROOT", root):
                self.assertEqual(graphify_compat.skill_version(), "9.8.7")

    def test_runtime_module_imports_as_package(self):
        self.assertIs(runtime.toolchain_resolution, resolution)


if __name__ == "__main__":
    unittest.main()
