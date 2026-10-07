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

import copy
import time
import zipfile
from unittest.mock import patch
sys.path.insert(0, str(ROOT / "scripts"))
import behavior_contract as behavior
import evidence_capture as capture



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

    def test_corrupt_local_state_without_baseline_requires_reconstruction(self):
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
            self.assertEqual(applied.returncode, 2, applied.stdout + applied.stderr)
            result = json.loads(applied.stdout)
            self.assertTrue(result["applied"])
            self.assertTrue(result["recovery_required"])
            self.assertIsNone(result["restored_project_state"])
            self.assertTrue((workspace / "state/project-state-recovery.json").exists())
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


def receipt_contract():
    return {"format": "vibe-task-contract", "schema_version": 1, "task_id": "تنظیمات/../../task",
            "objective": "Preserve settings", "scope": ["src"], "risk_tier": 1,
            "acceptance_criteria": [{"id": "setting", "description": "Stored setting unchanged", "required": True}],
            "evidence_requirements": [{"id": "check", "criterion_ids": ["setting"], "kind": "unit-test",
                "origin": "collected", "required": True, "input_paths": ["src", "check.py", "expected-missing"],
                "input_excludes": ["src/generated"]}]}


class EvidenceCaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "product"
        (self.root / "src" / "generated").mkdir(parents=True)
        (self.root / "src/settings.txt").write_text("preserved", encoding="utf-8")
        (self.root / "src/generated/log.txt").write_text("old", encoding="utf-8")
        (self.root / "check.py").write_text("assert True\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        self.env = patch.dict(os.environ, {"VIBE_CODING_HOME": str(self.base / "local-state"), "PYTHONDONTWRITEBYTECODE": "1"})
        self.env.start()
        self.c = receipt_contract()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def run_check(self, code="pass", **options):
        return capture.capture(self.root, self.c, "check", [sys.executable, "-c", code], **options)

    def test_real_success_failure_and_spawn_error_are_distinct_and_local(self):
        passed = self.run_check("print('discarded command output')")
        r = passed["receipt"]
        self.assertEqual(r["result"], "pass")
        self.assertEqual(r["command"]["exit_code"], 0)
        self.assertTrue(r["process_started"])
        self.assertEqual(r["inputs"]["before_sha256"], r["inputs"]["after_sha256"])
        self.assertEqual(r["contract_sha256"], behavior.digest(self.c))
        self.assertEqual(r["criterion_ids"], ["setting"])
        self.assertNotIn("commit", r["source"])
        self.assertLessEqual(r["started_at"], r["finished_at"])
        self.assertFalse(passed["completion_verified"])
        path = Path(passed["receipt_path"])
        self.assertFalse(path.is_relative_to(self.root))
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), r)
        self.assertNotIn("log", r)
        self.assertEqual(self.run_check("raise SystemExit(7)")["receipt"]["command"]["exit_code"], 7)
        failed = capture.capture(self.root, self.c, "check", [str(self.base / "missing-executable")])["receipt"]
        self.assertEqual(failed["result"], "error")
        self.assertFalse(failed["process_started"])
        self.assertIsNone(failed["command"]["exit_code"])

    def test_manifest_includes_untracked_missing_and_empty_directory_membership(self):
        obligation = self.c["evidence_requirements"][0]
        def manifest():
            return capture.snapshot(self.root, obligation["input_paths"], obligation["input_excludes"])
        original = manifest()
        self.assertIn({"path": "expected-missing", "missing": True}, original)
        (self.root / "src/generated/log.txt").write_text("new", encoding="utf-8")
        self.assertEqual(original, manifest())
        (self.root / "src/new.txt").write_text("untracked", encoding="utf-8")
        self.assertNotEqual(original, manifest())
        (self.root / "src/new.txt").unlink()
        (self.root / "src/empty").mkdir()
        self.assertIn({"path": "src/empty", "directory": True}, manifest())
        self.assertNotEqual(original, manifest())

    def test_mutating_inputs_and_checked_artifacts_cannot_pass(self):
        excluded = self.run_check("from pathlib import Path; Path('src/generated/log.txt').write_text('generated output')")["receipt"]
        self.assertEqual(excluded["result"], "pass")
        changed = self.run_check("from pathlib import Path; Path('src/settings.txt').write_text('mutated')")["receipt"]
        self.assertEqual(changed["result"], "error")
        self.assertNotEqual(changed["inputs"]["before_sha256"], changed["inputs"]["after_sha256"])
        artifact = self.base / "delivered.zip"
        artifact.write_bytes(b"exact bytes")
        self.c["evidence_requirements"][0]["artifact_paths"] = [str(artifact)]
        r = self.run_check()["receipt"]
        self.assertEqual(r["result"], "pass")
        self.assertEqual(r["artifacts"], r["artifacts_before"])
        self.assertEqual(r["artifacts"][0]["path"], str(artifact))
        r = self.run_check("from pathlib import Path; Path(" + repr(str(artifact)) + ").write_bytes(b'changed')")["receipt"]
        self.assertEqual(r["result"], "error")
        artifact.unlink()
        r = self.run_check()["receipt"]
        self.assertEqual(r["result"], "error")
        self.assertFalse(r["process_started"])

    def test_timeout_stops_child_tree_and_never_becomes_success(self):
        marker = self.base / "child-survived.txt"
        child = "import time; from pathlib import Path; time.sleep(1.2); Path(" + repr(str(marker)) + ").write_text('bad')"
        code = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c'," + repr(child) + "]); time.sleep(10)"
        start = time.monotonic()
        r = self.run_check(code, timeout_seconds=0.3)["receipt"]
        self.assertEqual(r["result"], "timeout")
        self.assertTrue(r["termination_confirmed"])
        self.assertLess(time.monotonic() - start, 8)
        time.sleep(1.3)
        self.assertFalse(marker.exists())

    def test_unsafe_paths_scope_erasure_limits_and_origins_fail_before_execution(self):
        for value in ("../outside", "/outside", "C:/outside", "src/*", "src/?", "src/\x00value", "src\\value"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                capture.snapshot(self.root, [value], [])
        for paths, excluded in ((["src"], ["src"]), (["src"], ["."])):
            with self.assertRaises(ValueError):
                capture.snapshot(self.root, paths, excluded)
        with self.assertRaises(ValueError):
            capture.snapshot(self.root, ["src"], [], max_files=1)
        with self.assertRaises(ValueError):
            capture.snapshot(self.root, ["check.py"], [], max_bytes=1)
        for timeout in (0, float("nan"), float("inf"), True):
            with self.assertRaises(ValueError):
                self.run_check(timeout_seconds=timeout)
        for origin in ("manual", "reported"):
            altered = copy.deepcopy(self.c)
            altered["evidence_requirements"][0]["origin"] = origin
            with self.assertRaises(ValueError):
                capture.capture(self.root, altered, "check", [sys.executable, "-c", "pass"])
        with patch.dict(os.environ, {"VIBE_CODING_HOME": str(self.root / "state")}):
            with self.assertRaises(ValueError):
                self.run_check()

    def test_route_names_are_literal_in_inputs_exclusions_and_artifacts(self):
        names = ["src/[id]/page.tsx", "src/[...slug]/page.tsx", "src/[[...slug]]/page.tsx",
                 "src/(group)/[name]/page.tsx", "src/صفحه [id]/page.tsx"]
        for name in [*names, "src/i/page.tsx", "src/[generated]/output.txt"]:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(name, encoding="utf-8")
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(capture.relative(name), name)
                rows = capture.snapshot(self.root, [name], [])
                self.assertEqual([row["path"] for row in rows], [name])
                self.assertEqual(rows[0]["sha256"], capture.hashlib.sha256(name.encode()).hexdigest())
                artifact = capture.artifact_snapshot(self.root, [name])[0]
                self.assertEqual(artifact["sha256"], rows[0]["sha256"])
        rows = capture.snapshot(self.root, ["src"], ["src/[generated]"])
        self.assertTrue(set(names) <= {row["path"] for row in rows})
        self.assertFalse(any(row["path"].startswith("src/[generated]") for row in rows))
        self.assertEqual(capture.snapshot(self.root, ["src/[missing]/page.tsx"], [], require_file=False),
                         [{"path": "src/[missing]/page.tsx", "missing": True}])

    def test_link_escape_is_rejected_including_missing_child(self):
        link = self.root / "src/link"
        try:
            link.symlink_to(self.base, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                self.skipTest("host does not permit symlink creation")
            created = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(self.base)], capture_output=True)
            if created.returncode != 0:
                self.skipTest("host does not permit symlink/junction creation")
        try:
            with self.assertRaises(ValueError):
                capture.snapshot(self.root, ["src/link/missing"], [])
            r = self.run_check()["receipt"]
            self.assertEqual(r["result"], "error")
            self.assertFalse(r["process_started"])
        finally:
            if link.is_symlink():
                link.unlink()
            else:
                link.rmdir()  # Remove only the junction itself, never its target.

    def test_wordpress_artifact_reuses_verified_version_and_exact_bytes(self):
        artifact = self.base / "plugin.zip"
        with zipfile.ZipFile(artifact, "w") as z:
            z.writestr("sample/sample.php", "<?php\n/*\nPlugin Name: Sample\nVersion: 1.2.3\n*/\n")
        self.c["evidence_requirements"][0]["artifact_paths"] = [str(artifact)]
        r = self.run_check(wordpress_artifacts=True)["receipt"]
        self.assertEqual(r["result"], "pass")
        self.assertEqual(r["artifacts"][0]["version"], "1.2.3")
        artifact.write_bytes(b"invalid ZIP")
        r = self.run_check(wordpress_artifacts=True)["receipt"]
        self.assertEqual(r["result"], "error")
        self.assertFalse(r["process_started"])

    def test_real_cli_and_unavailable_never_fabricate_an_attempt(self):
        supplied = self.base / "contract.json"
        supplied.write_text(json.dumps(self.c, ensure_ascii=False), encoding="utf-8")
        command = [sys.executable, "-X", "utf8", str(ROOT / "scripts/evidence_capture.py"), "run", "--root", str(self.root),
                   "--task-contract", str(supplied), "--requirement", "check", "--", sys.executable, "check.py"]
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertEqual(json.loads(completed.stdout)["receipt"]["task_id"], self.c["task_id"])
        unavailable = capture.unavailable(self.root, self.c, "check", "Runtime not available")["receipt"]
        self.assertEqual(unavailable["result"], "unavailable")
        self.assertNotIn("command", unavailable)
        self.assertNotIn("started_at", unavailable)
        self.assertNotIn("inputs", unavailable)
        self.assertIn("recorded_at", unavailable)



if __name__ == "__main__":
    unittest.main()
