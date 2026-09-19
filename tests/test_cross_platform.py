from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(root: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    if p.returncode:
        raise AssertionError((p.stderr or p.stdout).strip())
    return p.stdout.strip()


def init_repo(root: Path) -> None:
    git(root, "init", "-q")
    git(root, "config", "user.email", "cross-platform@example.invalid")
    git(root, "config", "user.name", "Cross Platform Test")


class CrossPlatformRecoveryTests(unittest.TestCase):
    def test_resume_without_chat_or_local_state(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as hd:
            root = Path(td)
            init_repo(root)
            (root / "STATUS.md").write_text(
                "# Status\n\n## Current Objective\nShip recovery validation.\n",
                encoding="utf-8",
            )
            (root / "PROJECT.md").write_text("# Project\n\nCore outcome: resume reliably.\n", encoding="utf-8")
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            (root / "pyproject.toml").write_text("[project]\nname='demo'\nversion='0.1.0'\n", encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "baseline")

            env = os.environ.copy()
            env["VIBE_CODING_HOME"] = hd
            out = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "resume_context.py"),
                    "--root",
                    str(root),
                    "--write-local",
                    "--json",
                ],
                text=True,
                capture_output=True,
                env=env,
            )
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
            data = json.loads(out.stdout)
            self.assertEqual(data["readiness"], "PASS")
            self.assertFalse(data["git"]["dirty"])
            self.assertIn("pyproject.toml", data["manifests"])
            names = [doc["name"] for doc in data["documents"]]
            self.assertEqual(names[:3], ["STATUS.md", "PROJECT.md", "README.md"])
            self.assertTrue(Path(data["written"]["json"]).exists())
            self.assertTrue(Path(data["written"]["markdown"]).exists())
            self.assertFalse((root / "resume-context.json").exists())

    def test_corrupt_local_state_is_quarantined_and_regenerated(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as hd:
            root = Path(td)
            init_repo(root)
            (root / "README.md").write_text("# Recovery\n", encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "baseline")

            env = os.environ.copy()
            env["VIBE_CODING_HOME"] = hd
            init = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "local_workspace.py"),
                    "init",
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                env=env,
                check=True,
            )
            workspace = Path(json.loads(init.stdout)["workspace"])
            (workspace / "state" / "project-state.json").write_text("{broken", encoding="utf-8")
            (workspace / "state" / "traceability.json").write_text("[]", encoding="utf-8")

            inspect = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "state_recovery.py"),
                    "inspect",
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                env=env,
            )
            self.assertEqual(inspect.returncode, 0, inspect.stdout + inspect.stderr)
            self.assertEqual(json.loads(inspect.stdout)["status"], "WARN")

            dry = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "state_recovery.py"),
                    "repair",
                    "--root",
                    str(root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                env=env,
            )
            self.assertEqual(dry.returncode, 0, dry.stdout + dry.stderr)
            self.assertFalse(json.loads(dry.stdout)["applied"])
            self.assertTrue((workspace / "state" / "project-state.json").exists())

            applied = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "state_recovery.py"),
                    "repair",
                    "--root",
                    str(root),
                    "--apply",
                    "--json",
                ],
                text=True,
                capture_output=True,
                env=env,
            )
            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            result = json.loads(applied.stdout)
            self.assertTrue(result["applied"])
            self.assertTrue(Path(result["regenerated_project_state"]).exists())
            self.assertTrue(result["backup_dir"])
            self.assertFalse((root / ".vibe").exists())


class CrossPlatformInstallTests(unittest.TestCase):
    def test_canonical_install_check_is_offline_and_nonblocking(self):
        out = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "install_check.py"),
                "--skill-root",
                str(ROOT),
                "--json",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        result = json.loads(out.stdout)
        self.assertTrue(result["offline"])
        self.assertTrue(result["python_supported"])
        self.assertTrue(result["git_installed"])
        self.assertTrue(result["workspace_smoke"]["ok"])
        self.assertNotEqual(result["status"], "BLOCK")

    def test_last_known_good_and_explicit_rollback(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as hd:
            skill = Path(td)
            shutil.copytree(ROOT / "skills" / "vibe-coding-skill", skill, dirs_exist_ok=True)
            init_repo(skill)
            git(skill, "add", ".")
            git(skill, "commit", "-qm", "validated baseline")
            v1 = git(skill, "rev-parse", "HEAD")

            env = os.environ.copy()
            env["VIBE_CODING_HOME"] = hd
            recorded = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "skill_lifecycle.py"),
                    "record-good",
                    "--skill-root",
                    str(skill),
                    "--json",
                ],
                text=True,
                capture_output=True,
                env=env,
            )
            self.assertEqual(recorded.returncode, 0, recorded.stdout + recorded.stderr)
            self.assertEqual(json.loads(recorded.stdout)["head"], v1)

            skill_text = (skill / "SKILL.md").read_text(encoding="utf-8")
            current_version = json.loads(recorded.stdout)["version"]
            skill_text = skill_text.replace(
                f'  version: "{current_version}"',
                '  version: "9.9.9"',
            )
            (skill / "SKILL.md").write_text(skill_text, encoding="utf-8")
            git(skill, "add", "SKILL.md")
            git(skill, "commit", "-qm", "next version")
            v11 = git(skill, "rev-parse", "HEAD")
            self.assertNotEqual(v1, v11)

            dry = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "skill_lifecycle.py"),
                    "rollback",
                    "--skill-root",
                    str(skill),
                    "--json",
                ],
                text=True,
                capture_output=True,
                env=env,
            )
            self.assertEqual(dry.returncode, 0, dry.stdout + dry.stderr)
            self.assertFalse(json.loads(dry.stdout)["applied"])
            self.assertEqual(git(skill, "rev-parse", "HEAD"), v11)

            applied = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "skill_lifecycle.py"),
                    "rollback",
                    "--skill-root",
                    str(skill),
                    "--apply",
                    "--json",
                ],
                text=True,
                capture_output=True,
                env=env,
            )
            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            self.assertTrue(json.loads(applied.stdout)["applied"])
            self.assertEqual(git(skill, "rev-parse", "HEAD"), v1)


if __name__ == "__main__":
    unittest.main()
