from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock
from contextlib import redirect_stdout


ROOT = Path(__file__).resolve().parents[1]


def load_script():
    path = ROOT / "scripts" / "wordpress_artifact.py"
    spec = importlib.util.spec_from_file_location(
        "test_wordpress_artifact_module",
        path,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def plugin_source(root: Path, version: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "demo-plugin.php").write_text(
        "<?php\n"
        "/**\n"
        " * Plugin Name: Demo Plugin\n"
        f" * Version: {version}\n"
        " * Requires at least: 6.0\n"
        " * Requires PHP: 7.4\n"
        " * Text Domain: demo-plugin\n"
        " */\n"
        "add_action('init', static function () {});\n",
        encoding="utf-8",
    )
    (root / "includes").mkdir(exist_ok=True)
    (root / "includes" / "feature.php").write_text(
        "<?php\nfunction demo_plugin_feature() { return true; }\n",
        encoding="utf-8",
    )


class WordPressArtifactTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_script()

    def test_command_preserves_stdout_and_marks_bounded_diagnostics(self):
        stdout = json.dumps([{"name": f"plugin-{i}", "status": "active"} for i in range(150)])
        stderr = "warning\n" * 600
        with mock.patch.object(self.mod.shutil, "which", return_value="fixture-wp"), mock.patch.object(
            self.mod.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout, stderr),
        ):
            step = self.mod.run_wp("fixture-wp", ROOT, ["plugin", "list", "--format=json"])
        self.assertGreater(len(stdout), 4000)
        self.assertEqual(step["stdout"], stdout)
        self.assertEqual(len(json.loads(step["stdout"])), 150)
        self.assertEqual(step["stderr"], stderr[-4000:])
        self.assertTrue(step["stderr_truncated"])
        self.assertTrue(step["output_truncated"])
        self.assertLessEqual(len(step["output"]), 4000)

    def test_invalid_initial_output_and_command_failures_are_structured_cli_errors(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            plugin_source(base / "source", "1.0.0")
            artifact = base / "demo.zip"
            self.mod.package_artifact(base / "source", artifact, slug="demo-plugin")
            cases = [
                (subprocess.CompletedProcess([], 0, "[broken", ""), "not valid JSON"),
                (subprocess.CompletedProcess([], 0, '{}', ""), "must be a plugin array"),
                (subprocess.CompletedProcess([], 0, '["demo-plugin"]', ""), "must be a plugin array"),
                (subprocess.CompletedProcess([], 0, "Warning: stdout noise\n[]", ""), "not valid JSON"),
                (subprocess.CompletedProcess([], 1, "[]", "permission denied"), "initial plugin state failed: []\npermission denied"),
                (subprocess.CompletedProcess([], 0, " " * self.mod.MAX_WP_STDOUT_CHARS + "[]", ""), "stdout exceeds the supported limit"),
                (subprocess.TimeoutExpired(["fixture-wp"], 180), "timed out after 180 seconds"),
            ]
            for outcome, error in cases:
                with self.subTest(error=error):
                    captured = io.StringIO()
                    argv = ["wordpress_artifact.py", "runtime-check", "--artifact", str(artifact),
                            "--wordpress-root", str(base), "--wp-bin", "fixture-wp", "--json"]
                    with mock.patch.object(sys, "argv", argv), redirect_stdout(captured), \
                         mock.patch.object(self.mod.shutil, "which", return_value="fixture-wp"), \
                         mock.patch.object(self.mod.subprocess, "run", side_effect=[outcome]) as command:
                        code = self.mod.main()
                    self.assertEqual(code, 2)
                    result = json.loads(captured.getvalue())
                    self.assertFalse(result["ok"])
                    self.assertIn(error, result["error"])
                    command.assert_called_once()  # No install may follow a failed initial-state check.

    def test_stdout_limit_accepts_complete_json_at_boundary(self):
        stdout = " " * (self.mod.MAX_WP_STDOUT_CHARS - 2) + "[]"
        with mock.patch.object(self.mod.shutil, "which", return_value="fixture-wp"), mock.patch.object(
            self.mod.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout, ""),
        ):
            step = self.mod.run_wp("fixture-wp", ROOT, ["plugin", "list", "--format=json"])
        self.assertEqual(json.loads(step["stdout"]), [])
        self.assertEqual(len(step["stdout"]), self.mod.MAX_WP_STDOUT_CHARS)

    def test_invalid_or_wrong_version_stops_lifecycle_after_install(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            plugin_source(base / "source", "1.0.0")
            artifact = base / "demo.zip"
            self.mod.package_artifact(base / "source", artifact, slug="demo-plugin")
            for version, error in [("", "one nonempty stdout line"),
                                   ("1.0.0\nunexpected", "one nonempty stdout line"),
                                   ("9.9.9", "version differs from ZIP")]:
                with self.subTest(version=version), mock.patch.object(self.mod.shutil, "which", return_value="fixture-wp"), \
                     mock.patch.object(self.mod.subprocess, "run", side_effect=[
                         subprocess.CompletedProcess([], 0, "[]", ""),
                         subprocess.CompletedProcess([], 0, "installed", ""),
                         subprocess.CompletedProcess([], 0, version, "Warning: diagnostic"),
                     ]) as command:
                    with self.assertRaisesRegex(RuntimeError, error):
                        self.mod.runtime_check(artifact, base, "fixture-wp")
                    self.assertEqual(command.call_count, 3)

    def test_package_is_deterministic_and_verifies_embedded_version(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            plugin_source(source, "1.2.3")
            first = base / "first.zip"
            second = base / "second.zip"

            one = self.mod.package_artifact(
                source,
                first,
                slug="demo-plugin",
            )
            two = self.mod.package_artifact(
                source,
                second,
                slug="demo-plugin",
            )

            self.assertEqual(one["artifact_sha256"], two["artifact_sha256"])
            self.assertEqual(one["slug"], "demo-plugin")
            self.assertEqual(one["version"], "1.2.3")

            verified = self.mod.verify_artifact(
                first,
                expected_slug="demo-plugin",
                expected_version="1.2.3",
            )
            self.assertTrue(verified["verified"])
            self.assertEqual(
                verified["main_file"],
                "demo-plugin/demo-plugin.php",
            )

    def test_install_smoke_uses_exact_packaged_shape(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            plugin_source(source, "2.0.0")
            artifact = base / "demo.zip"
            packaged = self.mod.package_artifact(
                source,
                artifact,
                slug="demo-plugin",
            )

            result = self.mod.install_smoke(artifact)

            self.assertEqual(result["install_smoke"], "pass")
            self.assertEqual(result["installed_version"], "2.0.0")
            self.assertEqual(
                result["artifact_sha256"],
                packaged["artifact_sha256"],
            )

    def test_verify_rejects_version_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            plugin_source(source, "1.0.0")
            artifact = base / "demo.zip"
            self.mod.package_artifact(
                source,
                artifact,
                slug="demo-plugin",
            )

            result = self.mod.verify_artifact(
                artifact,
                expected_version="9.9.9",
            )

            self.assertFalse(result["verified"])
            self.assertTrue(
                any(
                    "version mismatch" in failure
                    for failure in result["failures"]
                )
            )

    def test_artifact_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            artifact = Path(td) / "unsafe.zip"
            with zipfile.ZipFile(artifact, "w") as archive:
                archive.writestr("../escape.php", "<?php")
                archive.writestr(
                    "demo-plugin/demo-plugin.php",
                    "<?php\n/* Plugin Name: Demo\nVersion: 1.0.0\n*/\n",
                )

            with self.assertRaisesRegex(ValueError, "unsafe zip path"):
                self.mod.inspect_artifact(artifact)

    def test_source_packaging_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            plugin_source(source, "1.0.0")
            target = base / "outside.txt"
            target.write_text("outside", encoding="utf-8")
            link = source / "linked.txt"
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest("symlinks are unavailable in this test environment")

            with self.assertRaisesRegex(ValueError, "symlink"):
                self.mod.package_artifact(
                    source,
                    base / "demo.zip",
                    slug="demo-plugin",
                )

    def test_runtime_upgrade_uses_previous_and_current_exact_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            old_source = base / "old"
            new_source = base / "new"
            plugin_source(old_source, "1.0.0")
            plugin_source(new_source, "1.1.0")
            old_zip = base / "demo-1.0.0.zip"
            new_zip = base / "demo-1.1.0.zip"
            self.mod.package_artifact(
                old_source,
                old_zip,
                slug="demo-plugin",
            )
            current_meta = self.mod.package_artifact(
                new_source,
                new_zip,
                slug="demo-plugin",
            )
            wordpress_root = base / "wordpress"
            wordpress_root.mkdir()
            fake_wp = base / "wp"
            fake_wp.write_text("fake", encoding="utf-8")

            state = {"version": ""}
            initial_plugins = [{"name": "demo-plugin", "status": "inactive"}] + [
                {"name": f"other-plugin-{i}", "status": "active", "version": "1.0.0"} for i in range(100)
            ]
            initial_stdout = json.dumps(initial_plugins)
            self.assertGreater(len(initial_stdout), 4000)

            class Result:
                def __init__(self, returncode=0, stdout="", stderr=""):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr

            def fake_run(command, **kwargs):
                args = list(command)
                if "list" in args and "--format=json" in args:
                    return Result(0, stdout=initial_stdout, stderr="PHP Warning: fixture diagnostic")
                if "install" in args:
                    artifact_arg = Path(args[args.index("install") + 1])
                    if artifact_arg == old_zip.resolve():
                        state["version"] = "1.0.0"
                    elif artifact_arg == new_zip.resolve():
                        state["version"] = "1.1.0"
                    else:
                        return Result(1, stderr="unexpected artifact")
                    return Result(0, stdout="installed")
                if "get" in args and "--field=version" in args:
                    return Result(0, stdout=state["version"] + "\n", stderr="PHP Warning: fixture diagnostic")
                if "deactivate" in args or "activate" in args:
                    return Result(0, stdout="ok")
                return Result(1, stderr="unexpected command")

            with mock.patch.object(
                self.mod.subprocess,
                "run",
                side_effect=fake_run,
            ):
                result = self.mod.runtime_check(
                    new_zip,
                    wordpress_root,
                    str(fake_wp),
                    previous_artifact=old_zip,
                )

            self.assertTrue(result["upgrade_checked"])
            self.assertTrue(result["plugin_present_before"])
            self.assertEqual(json.loads(result["steps"][0]["stdout"]), initial_plugins)
            self.assertIn("PHP Warning", result["steps"][0]["stderr"])
            self.assertFalse(result["fresh_install_checked"])
            self.assertEqual(result["previous_version"], "1.0.0")
            self.assertEqual(result["installed_version"], "1.1.0")
            self.assertEqual(
                result["artifact_sha256"],
                current_meta["artifact_sha256"],
            )
            commands = [step["command"] for step in result["steps"]]
            flattened = [item for command in commands for item in command]
            self.assertIn(str(old_zip.resolve()), flattened)
            self.assertIn(str(new_zip.resolve()), flattened)

    def test_uninstall_requires_explicit_disposable_environment(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            plugin_source(source, "1.0.0")
            artifact = base / "demo.zip"
            self.mod.package_artifact(
                source,
                artifact,
                slug="demo-plugin",
            )
            wordpress_root = base / "wordpress"
            wordpress_root.mkdir()

            with self.assertRaisesRegex(
                ValueError,
                "disposable-environment",
            ):
                self.mod.runtime_check(
                    artifact,
                    wordpress_root,
                    exercise_uninstall=True,
                    disposable_environment=False,
                )


if __name__ == "__main__":
    unittest.main()
