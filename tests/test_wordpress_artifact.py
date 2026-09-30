from __future__ import annotations

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


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

            class Result:
                def __init__(self, returncode=0, stdout="", stderr=""):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr

            def fake_run(command, **kwargs):
                args = list(command)
                if "list" in args and "--format=json" in args:
                    return Result(0, stdout="[]")
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
                    return Result(0, stdout=state["version"] + "\n")
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
