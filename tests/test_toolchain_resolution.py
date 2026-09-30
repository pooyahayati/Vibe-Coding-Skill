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
import scripts.trivy_compat as trivy_compat


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

    def test_explicit_session_resolves_once_and_reuses_exact_version(self):
        calls = [
            {
                "tool": "graphify",
                "selected_version": "1.2.3",
                "source": "latest-compatible-stable",
                "fallback_used": False,
            },
            {
                "tool": "graphify",
                "selected_version": "1.2.4",
                "source": "latest-compatible-stable",
                "fallback_used": False,
            },
        ]
        key = "VIBE_TOOLCHAIN_GRAPHIFY_SESSION_VERSION"
        with (
            mock.patch.dict(runtime.os.environ, {key: ""}, clear=False),
            mock.patch.object(
                runtime.toolchain_resolution,
                "load_config",
                return_value={"graphify": {}},
            ),
            mock.patch.object(
                runtime.toolchain_resolution,
                "resolve",
                side_effect=calls,
            ) as resolver,
        ):
            session = runtime.new_session()
            first = session.resolve("graphify")
            second = session.resolve("graphify")
            newer = runtime.new_session().resolve("graphify")

        self.assertEqual(resolver.call_count, 2)
        self.assertEqual(first["selected_version"], "1.2.3")
        self.assertEqual(second["selected_version"], "1.2.3")
        self.assertEqual(newer["selected_version"], "1.2.4")
        self.assertTrue(first["contract_verified"])

    def test_environment_session_pin_is_reused_without_compatibility_check(self):
        key = "VIBE_TOOLCHAIN_GRAPHIFY_SESSION_VERSION"
        with (
            mock.patch.dict(runtime.os.environ, {key: "7.8.9"}, clear=False),
            mock.patch.object(
                runtime.toolchain_resolution,
                "resolve",
            ) as resolver,
        ):
            session = runtime.new_session()
            first = session.resolve("graphify")
            second = session.resolve("graphify")
        resolver.assert_not_called()
        self.assertEqual(first["selected_version"], "7.8.9")
        self.assertEqual(second["selected_version"], "7.8.9")
        self.assertFalse(first["contract_verified"])

    def test_trivy_fs_container_command_mounts_host_read_only(self):
        with tempfile.TemporaryDirectory(prefix="vibe trivy target ") as td:
            target = Path(td)
            with (
                mock.patch.object(runtime, "matching_native", return_value=None),
                mock.patch.object(
                    runtime.shutil,
                    "which",
                    side_effect=lambda name: "/usr/bin/docker"
                    if name == "docker"
                    else None,
                ),
            ):
                cmd = runtime.trivy_fs_command(
                    "1.2.3",
                    target,
                    ["--scanners", "secret"],
                )

        self.assertEqual(cmd[:4], ["docker", "run", "--rm", "--mount"])
        mount = cmd[4]
        self.assertIn("type=bind,src=", mount)
        self.assertIn(",dst=/workspace,readonly", mount)
        self.assertIn("vibe trivy target", mount)
        self.assertEqual(cmd[-1], "/workspace")
        self.assertIn("aquasec/trivy:1.2.3", cmd)

    def test_docker_bind_mount_preserves_windows_path_and_spaces(self):
        mount = runtime.docker_bind_mount(r"C:\Work Folder\demo")
        self.assertEqual(
            mount,
            r"type=bind,src=C:\Work Folder\demo,dst=/workspace,readonly",
        )

    def test_generic_trivy_command_rejects_host_filesystem_scan(self):
        with self.assertRaisesRegex(ValueError, "trivy_fs_command"):
            runtime.trivy_command("1.2.3", ["fs", "."])

    def test_graphify_compat_can_use_matching_native_without_uvx(self):
        with (
            mock.patch.object(
                graphify_compat.shutil,
                "which",
                side_effect=lambda name: "/opt/graphify"
                if name == "graphify"
                else None,
            ),
            mock.patch.object(
                graphify_compat,
                "detected_version",
                return_value="1.2.3",
            ),
        ):
            prefix, selected = graphify_compat.graphify_prefix("1.2.3")
        self.assertEqual(prefix, ["/opt/graphify"])
        self.assertEqual(selected, "native")

    def test_trivy_compat_can_use_matching_native_without_docker(self):
        with (
            mock.patch.object(
                trivy_compat.shutil,
                "which",
                side_effect=lambda name: "/opt/trivy"
                if name == "trivy"
                else None,
            ),
            mock.patch.object(
                trivy_compat,
                "detected_version",
                return_value="1.2.3",
            ),
        ):
            selected, executable = trivy_compat.trivy_runtime("1.2.3")
        self.assertEqual(selected, "native")
        self.assertEqual(executable, "/opt/trivy")

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
