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


class LiveAgentEvalTests(unittest.TestCase):
    def test_valid_behavior_contract_passes(self):
        catalog = json.loads((ROOT / "evals" / "scenarios.json").read_text(encoding="utf-8"))
        scenario = next(s for s in catalog["scenarios"] if s["id"] == "tiny-copy-fix")
        with tempfile.TemporaryDirectory() as td:
            result_path = Path(td) / "result.json"
            result_path.write_text(json.dumps({
                "scenario_id": scenario["id"],
                "tier": scenario["expected_tier"],
                "approval_required": scenario["approval_required"],
                "controls": scenario["required_controls"],
                "forbidden_actions": scenario["forbidden_controls"]
            }), encoding="utf-8")
            out = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "evaluate_agent_output.py"), str(result_path), "--json"],
                text=True, capture_output=True
            )
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)

    def test_missing_required_control_fails(self):
        with tempfile.TemporaryDirectory() as td:
            result_path = Path(td) / "result.json"
            result_path.write_text(json.dumps({
                "scenario_id": "destructive-migration",
                "tier": 3,
                "approval_required": True,
                "controls": [],
                "forbidden_actions": ["execute-destructive-migration-before-approval"]
            }), encoding="utf-8")
            out = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "evaluate_agent_output.py"), str(result_path), "--json"],
                text=True, capture_output=True
            )
            self.assertNotEqual(out.returncode, 0)


class CompletionGateTests(unittest.TestCase):
    def test_done_without_evidence_blocks(self):
        mod = load_script("completion_gate.py")
        result = mod.evaluate({
            "status": "Done",
            "acceptance_criteria": [{"id": "AC-1", "met": True}],
            "evidence": [],
            "blockers": [],
        })
        self.assertEqual(result["gate"], "BLOCK")

    def test_done_with_passing_evidence_passes(self):
        mod = load_script("completion_gate.py")
        result = mod.evaluate({
            "status": "Done",
            "acceptance_criteria": [{"id": "AC-1", "met": True}],
            "evidence": [{"kind": "test", "result": "pass"}],
            "blockers": [],
        })
        self.assertEqual(result["gate"], "PASS")


class BenchmarkScoringTests(unittest.TestCase):
    def test_reusable_agent_scorer(self):
        mod = load_script("evaluate_agent_output.py")
        catalog = json.loads((ROOT / "evals" / "scenarios.json").read_text(encoding="utf-8"))
        scenario = next(s for s in catalog["scenarios"] if s["id"] == "tiny-copy-fix")
        result = mod.score_contract({
            "scenario_id": scenario["id"],
            "tier": scenario["expected_tier"],
            "approval_required": scenario["approval_required"],
            "controls": scenario["required_controls"],
            "forbidden_actions": scenario["forbidden_controls"],
        }, catalog)
        self.assertTrue(result["passed"])


class BootstrapTests(unittest.TestCase):
    def test_bootstrap_does_not_overwrite_existing_status(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as hd:
            root = Path(td)
            local_home = Path(hd)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            status = root / "STATUS.md"
            status.write_text("keep me\n", encoding="utf-8")
            env = os.environ.copy()
            env["VIBE_CODING_HOME"] = str(local_home)
            cmd = [
                sys.executable, str(ROOT / "scripts" / "bootstrap_project.py"),
                "--root", str(root), "--profile", "minimal",
                "--objective", "Test objective", "--json",
            ]
            out = subprocess.run(cmd, text=True, capture_output=True, check=True, env=env)
            data = json.loads(out.stdout)
            self.assertEqual(status.read_text(encoding="utf-8"), "keep me\n")
            self.assertTrue(any("STATUS.md: exists" in item for item in data["skipped"]))
            self.assertFalse((root / ".vibe").exists())
            self.assertFalse((root / ".gitignore").exists())
            states = list((local_home / "projects").glob("*/state/project.json"))
            self.assertEqual(len(states), 1)
            exclude = (root / ".git" / "info" / "exclude").read_text(encoding="utf-8")
            self.assertIn("graphify-out/", exclude)
            self.assertIn("Vibe Coding Skill local-only artifacts", exclude)

    def test_standard_skips_project_doc_without_product_facts(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as hd:
            root = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            env = os.environ.copy()
            env["VIBE_CODING_HOME"] = hd
            cmd = [
                sys.executable, str(ROOT / "scripts" / "bootstrap_project.py"),
                "--root", str(root), "--profile", "standard",
                "--objective", "Test objective", "--json",
            ]
            out = subprocess.run(cmd, text=True, capture_output=True, check=True, env=env)
            data = json.loads(out.stdout)
            self.assertFalse((root / "PROJECT.md").exists())
            self.assertFalse((root / ".vibe").exists())
            self.assertTrue(any("PROJECT.md: insufficient" in item for item in data["skipped"]))


class IntegrationGuardTests(unittest.TestCase):
    def _fake_exe(self, root: Path, name: str, body: str) -> None:
        path = root / name
        path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    def test_tier2_reports_stale_graph_without_mutating_repo(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as bindir, tempfile.TemporaryDirectory() as hd:
            root = Path(td)
            binroot = Path(bindir)
            local_home = Path(hd)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "app.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "init"], cwd=root, check=True)
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
            self._fake_exe(binroot, "graphify", 'echo "graphify 0.9.64"')
            self._fake_exe(binroot, "trivy", 'echo "Version: 0.74.0"')
            env = os.environ.copy()
            env["PATH"] = str(binroot) + os.pathsep + env["PATH"]
            env["VIBE_CODING_HOME"] = str(local_home)
            local = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "local_workspace.py"),
                 "init", "--root", str(root), "--json"],
                text=True, capture_output=True, env=env, check=True,
            )
            workspace = Path(json.loads(local.stdout)["workspace"])
            (workspace / "state" / "graph-state.json").write_text(
                json.dumps({
                    "source_commit": "0" * 40,
                    "working_tree_fingerprint": "stale",
                    "provider": "graphify"
                }),
                encoding="utf-8",
            )
            graph_dir = workspace / "graph" / "graphify-out"
            graph_dir.mkdir(parents=True, exist_ok=True)
            (graph_dir / "graph.json").write_text('{"nodes":[],"links":[]}\n', encoding="utf-8")
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
            self.assertFalse((root / ".vibe").exists())


class LocalWorkspacePurityTests(unittest.TestCase):
    def test_local_workspace_uses_git_info_exclude_not_gitignore(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as hd:
            root = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            env = os.environ.copy()
            env["VIBE_CODING_HOME"] = hd
            out = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "local_workspace.py"),
                 "init", "--root", str(root), "--json"],
                text=True, capture_output=True, env=env, check=True,
            )
            data = json.loads(out.stdout)
            self.assertTrue(Path(data["workspace"]).is_dir())
            self.assertFalse((root / ".gitignore").exists())
            exclude = (root / ".git" / "info" / "exclude").read_text(encoding="utf-8")
            self.assertIn("graphify-out/", exclude)
            self.assertIn(".trivy/", exclude)
            self.assertIn(".claude/skills/vibe-coding-skill/", exclude)
            self.assertIn(".codex/skills/vibe-coding-skill/", exclude)
            self.assertIn(".agents/skills/vibe-coding-skill/", exclude)

    def test_purity_gate_blocks_tracked_tool_artifact_but_allows_product_tests(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as hd:
            root = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "tests").mkdir()
            (root / "tests" / "test_app.py").write_text("def test_ok(): assert True\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "product tests"], cwd=root, check=True)
            env = os.environ.copy()
            env["VIBE_CODING_HOME"] = hd
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "local_workspace.py"),
                 "init", "--root", str(root), "--json"],
                text=True, capture_output=True, env=env, check=True,
            )
            clean = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "repository_purity.py"),
                 "--root", str(root), "--json"],
                text=True, capture_output=True, env=env,
            )
            self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)

            (root / "graphify-out").mkdir()
            (root / "graphify-out" / "graph.json").write_text("{}\n", encoding="utf-8")
            subprocess.run(["git", "add", "-f", "graphify-out/graph.json"], cwd=root, check=True)
            dirty = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "repository_purity.py"),
                 "--root", str(root), "--json"],
                text=True, capture_output=True, env=env,
            )
            self.assertEqual(dirty.returncode, 2)
            result = json.loads(dirty.stdout)
            self.assertIn("graphify-out/graph.json", result["staged_forbidden"])
            self.assertNotIn("tests/test_app.py", result["staged_forbidden"])

            subprocess.run(["git", "reset", "-q"], cwd=root, check=True)
            skill_dir = root / ".claude" / "skills" / "vibe-coding-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("# local tool checkout\n", encoding="utf-8")
            subprocess.run(["git", "add", "-f", ".claude/skills/vibe-coding-skill/SKILL.md"], cwd=root, check=True)
            tool_checkout = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "repository_purity.py"),
                 "--root", str(root), "--json"],
                text=True, capture_output=True, env=env,
            )
            self.assertEqual(tool_checkout.returncode, 2)
            self.assertIn(
                ".claude/skills/vibe-coding-skill/SKILL.md",
                json.loads(tool_checkout.stdout)["staged_forbidden"],
            )



class GraphProviderContractTests(unittest.TestCase):
    def _fake_graphify(self, bindir: Path) -> None:
        path = bindir / "graphify"
        path.write_text(
            """#!/bin/sh
set -eu
if [ "$1" = "--version" ]; then
  echo "graphify 0.9.64"
  exit 0
fi
case "$1" in
  extract|update)
    mkdir -p graphify-out
    printf '%s\n' '{"nodes":[{"id":"alpha","label":"alpha"},{"id":"beta","label":"beta"}],"links":[{"source":"alpha","target":"beta"}]}' > graphify-out/graph.json
    echo "built"
    ;;
  query|explain|path)
    echo "$1-ok"
    ;;
  *)
    echo "unknown" >&2
    exit 2
    ;;
esac
""",
            encoding="utf-8",
        )
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    def test_refresh_uses_shadow_workspace_and_detects_working_tree_staleness(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as hd, tempfile.TemporaryDirectory() as bd:
            root = Path(td)
            local_home = Path(hd)
            bindir = Path(bd)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "app.py").write_text("def alpha(): return 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "init"], cwd=root, check=True)
            self._fake_graphify(bindir)
            env = os.environ.copy()
            env["PATH"] = str(bindir) + os.pathsep + env["PATH"]
            env["VIBE_CODING_HOME"] = str(local_home)

            refresh = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "graph_provider.py"),
                 "refresh", "--root", str(root), "--mode", "full", "--json"],
                text=True, capture_output=True, env=env,
            )
            self.assertEqual(refresh.returncode, 0, refresh.stdout + refresh.stderr)
            result = json.loads(refresh.stdout)
            self.assertTrue(Path(result["graph_path"]).exists())
            self.assertFalse((root / "graphify-out").exists())

            status = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "graph_provider.py"),
                 "status", "--root", str(root), "--json"],
                text=True, capture_output=True, env=env, check=True,
            )
            self.assertTrue(json.loads(status.stdout)["fresh"])

            (root / "app.py").write_text("def alpha(): return 2\n", encoding="utf-8")
            stale = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "graph_provider.py"),
                 "status", "--root", str(root), "--json"],
                text=True, capture_output=True, env=env, check=True,
            )
            self.assertTrue(json.loads(stale.stdout)["stale"])

            blocked = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "graph_provider.py"),
                 "query", "alpha", "--root", str(root), "--json"],
                text=True, capture_output=True, env=env,
            )
            self.assertEqual(blocked.returncode, 2)

            refreshed = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "graph_provider.py"),
                 "refresh", "--root", str(root), "--mode", "auto", "--json"],
                text=True, capture_output=True, env=env,
            )
            self.assertEqual(refreshed.returncode, 0, refreshed.stdout + refreshed.stderr)
            self.assertEqual(json.loads(refreshed.stdout)["mode"], "incremental")


class GitHubTraceabilityTests(unittest.TestCase):
    def _fake_gh(self, bindir: Path) -> None:
        path = bindir / "gh"
        path.write_text(
            """#!/usr/bin/env python3
import json, sys
args = sys.argv[1:]
if args[:2] == ["auth", "status"]:
    raise SystemExit(0)
if args[:2] == ["issue", "list"]:
    print("[]"); raise SystemExit(0)
if args[:2] == ["pr", "list"]:
    print("[]"); raise SystemExit(0)
if args[:2] == ["release", "list"]:
    print("[]"); raise SystemExit(0)
if args and args[0] == "api":
    endpoint = args[1]
    if endpoint.endswith("/issues/42"):
        print(json.dumps({"number":42,"state":"open","html_url":"https://github.com/acme/demo/issues/42","title":"[REQ-1] Demo","body":"REQ-1 acceptance"}))
    elif endpoint.endswith("/pulls/57"):
        print(json.dumps({"number":57,"state":"closed","merged_at":"2026-01-01T00:00:00Z","html_url":"https://github.com/acme/demo/pull/57","body":"Closes #42"}))
    elif endpoint.endswith("/releases/tags/v1"):
        print(json.dumps({"tag_name":"v1","published_at":"2026-01-02T00:00:00Z","html_url":"https://github.com/acme/demo/releases/tag/v1"}))
    else:
        raise SystemExit(1)
    raise SystemExit(0)
if args[:2] == ["issue", "create"]:
    print("https://github.com/acme/demo/issues/99"); raise SystemExit(0)
raise SystemExit(2)
""",
            encoding="utf-8",
        )
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    def test_record_snapshot_verify_and_dry_run_stay_local(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as hd, tempfile.TemporaryDirectory() as bd:
            root = Path(td)
            bindir = Path(bd)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "remote", "add", "origin", "https://github.com/acme/demo.git"], cwd=root, check=True)
            self._fake_gh(bindir)
            env = os.environ.copy()
            env["PATH"] = str(bindir) + os.pathsep + env["PATH"]
            env["VIBE_CODING_HOME"] = hd

            record = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "github_traceability.py"), "record", "REQ-1",
                 "--root", str(root), "--issue", "42", "--pr", "57", "--test", "pytest", "--release", "v1", "--json"],
                text=True, capture_output=True, env=env,
            )
            self.assertEqual(record.returncode, 0, record.stdout + record.stderr)
            self.assertFalse((root / "traceability.json").exists())

            snapshot = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "github_traceability.py"), "snapshot",
                 "--root", str(root), "--json"],
                text=True, capture_output=True, env=env,
            )
            self.assertEqual(snapshot.returncode, 0, snapshot.stdout + snapshot.stderr)

            verify = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "github_traceability.py"), "verify",
                 "--root", str(root), "--requirement-id", "REQ-1", "--json"],
                text=True, capture_output=True, env=env,
            )
            self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
            self.assertEqual(json.loads(verify.stdout)["status"], "PASS")

            plan = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "github_traceability.py"), "create-issue",
                 "--root", str(root), "--title", "[REQ-2] Plan", "--body", "Acceptance criteria", "--json"],
                text=True, capture_output=True, env=env,
            )
            self.assertEqual(plan.returncode, 0, plan.stdout + plan.stderr)
            self.assertFalse(json.loads(plan.stdout)["applied"])

            milestone = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "github_traceability.py"), "create-milestone",
                 "--root", str(root), "--title", "v1", "--json"],
                text=True, capture_output=True, env=env,
            )
            self.assertEqual(milestone.returncode, 0, milestone.stdout + milestone.stderr)
            self.assertFalse(json.loads(milestone.stdout)["applied"])

            project_item = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "github_traceability.py"), "add-to-project",
                 "--root", str(root), "--project-number", "1",
                 "--url", "https://github.com/acme/demo/issues/42", "--json"],
                text=True, capture_output=True, env=env,
            )
            self.assertEqual(project_item.returncode, 0, project_item.stdout + project_item.stderr)
            self.assertFalse(json.loads(project_item.stdout)["applied"])


class ProjectStateAutomationTests(unittest.TestCase):
    def test_capture_drift_and_handoff_are_local_only(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as hd:
            root = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "init"], cwd=root, check=True)
            env = os.environ.copy()
            env["VIBE_CODING_HOME"] = hd

            capture = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "project_state.py"), "capture",
                 "--root", str(root), "--json"],
                text=True, capture_output=True, env=env,
            )
            self.assertEqual(capture.returncode, 0, capture.stdout + capture.stderr)
            state = json.loads(capture.stdout)
            self.assertTrue(Path(state["state_path"]).exists())
            self.assertFalse((root / "project-state.json").exists())

            (root / "README.md").write_text("# Demo\nchanged\n", encoding="utf-8")
            drift = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "project_state.py"), "drift",
                 "--root", str(root), "--json"],
                text=True, capture_output=True, env=env,
            )
            self.assertEqual(drift.returncode, 0, drift.stdout + drift.stderr)
            drift_data = json.loads(drift.stdout)
            self.assertEqual(drift_data["status"], "WARN")
            self.assertIn("working tree changed", drift_data["comparison"]["changes"])

            handoff = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "project_state.py"), "handoff",
                 "--root", str(root), "--write-local", "--json"],
                text=True, capture_output=True, env=env,
            )
            self.assertEqual(handoff.returncode, 0, handoff.stdout + handoff.stderr)
            self.assertTrue(Path(json.loads(handoff.stdout)["handoff_path"]).exists())
            self.assertFalse((root / "handoff.md").exists())


if __name__ == "__main__":
    unittest.main()
