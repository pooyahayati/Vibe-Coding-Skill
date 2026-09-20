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


    def test_normalize_git_plus_https_repository(self):
        mod = load_script("dependency_guard.py")
        self.assertEqual(
            mod.normalize_repo_url("git+https://github.com/colinhacks/zod.git"),
            "https://github.com/colinhacks/zod",
        )

    def test_v2_requires_explicit_necessity(self):
        mod = load_script("dependency_guard.py")
        decision, signals = mod.evaluate_dependency(
            {"exists": True, "version_exists": True, "repository": "https://github.com/acme/demo", "license": "MIT"},
            {"checked": True, "vulnerabilities": []},
            {"checked": True, "licenses": ["MIT"], "verified_attestations": 1},
            {"checked": True, "archived": False, "disabled": False, "push_age_days": 10},
            {"checked": True, "suspicious": []},
            {"latest_release_age_days": 20, "deprecated": False},
            {"licenses": ["MIT"], "allowed_policy": [], "denied_policy": [], "denied_matches": [], "allowed_matches": []},
            "1.0.0", 1, "unknown", None,
        )
        self.assertEqual(decision, "REVIEW REQUIRED")
        self.assertTrue(any(s["code"] == "necessity.unknown" for s in signals))

    def test_v2_accepts_complete_tier2_evidence(self):
        mod = load_script("dependency_guard.py")
        decision, signals = mod.evaluate_dependency(
            {"exists": True, "version_exists": True, "repository": "https://github.com/acme/demo", "license": "MIT"},
            {"checked": True, "vulnerabilities": []},
            {"checked": True, "licenses": ["MIT"], "verified_attestations": 0},
            {"checked": True, "archived": False, "disabled": False, "push_age_days": 15},
            {"checked": True, "suspicious": []},
            {"latest_release_age_days": 30, "deprecated": False},
            {"licenses": ["MIT"], "allowed_policy": ["MIT"], "denied_policy": [], "denied_matches": [], "allowed_matches": ["MIT"]},
            "1.0.0", 2, "required", "Provides protocol parsing that would be costly to maintain internally.",
        )
        self.assertEqual(decision, "ACCEPT")
        self.assertEqual(signals[0]["level"], "pass")

    def test_v2_typosquatting_signal_requires_review(self):
        mod = load_script("dependency_guard.py")
        similarity = mod.name_similarity_signal("requsets", ["requests", "urllib3"])
        self.assertTrue(similarity["suspicious"])
        decision, signals = mod.evaluate_dependency(
            {"exists": True, "version_exists": True, "repository": "https://github.com/acme/requsets", "license": "MIT"},
            {"checked": True, "vulnerabilities": []},
            {"checked": True, "licenses": ["MIT"], "verified_attestations": 1},
            {"checked": True, "archived": False, "disabled": False, "push_age_days": 10},
            similarity,
            {"latest_release_age_days": 20, "deprecated": False},
            {"licenses": ["MIT"], "allowed_policy": [], "denied_policy": [], "denied_matches": [], "allowed_matches": []},
            "1.0.0", 2, "required", "HTTP client",
        )
        self.assertEqual(decision, "REVIEW REQUIRED")
        self.assertTrue(any(s["code"] == "name.similar" for s in signals))

    def test_v2_denied_license_rejects(self):
        mod = load_script("dependency_guard.py")
        license_signal = mod.license_policy_signal(["GPL-3.0-only"], ["MIT", "Apache-2.0"], ["GPL-3.0-only"])
        decision, signals = mod.evaluate_dependency(
            {"exists": True, "version_exists": True, "repository": "https://github.com/acme/demo", "license": "GPL-3.0-only"},
            {"checked": True, "vulnerabilities": []},
            {"checked": True, "licenses": ["GPL-3.0-only"], "verified_attestations": 1},
            {"checked": True, "archived": False, "disabled": False, "push_age_days": 10},
            {"checked": True, "suspicious": []},
            {"latest_release_age_days": 20, "deprecated": False},
            license_signal,
            "1.0.0", 2, "required", "Required parser",
        )
        self.assertEqual(decision, "REJECT")
        self.assertTrue(any(s["code"] == "license.denied" for s in signals))

    def test_v2_tier3_requires_provenance_attestation(self):
        mod = load_script("dependency_guard.py")
        decision, signals = mod.evaluate_dependency(
            {"exists": True, "version_exists": True, "repository": "https://github.com/acme/demo", "license": "MIT"},
            {"checked": True, "vulnerabilities": []},
            {"checked": True, "licenses": ["MIT"], "verified_attestations": 0},
            {"checked": True, "archived": False, "disabled": False, "push_age_days": 5},
            {"checked": True, "suspicious": []},
            {"latest_release_age_days": 20, "deprecated": False},
            {"licenses": ["MIT"], "allowed_policy": [], "denied_policy": [], "denied_matches": [], "allowed_matches": []},
            "1.0.0", 3, "required", "Production-critical dependency",
        )
        self.assertEqual(decision, "REVIEW REQUIRED")
        self.assertTrue(any(s["code"] == "provenance.attestation_missing" for s in signals))


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



    def test_benchmark_allows_bounded_conservative_escalation(self):
        mod = load_script("evaluate_agent_output.py")
        catalog = json.loads((ROOT / "evals" / "scenarios.json").read_text(encoding="utf-8"))
        scenario = next(
            s for s in catalog["scenarios"]
            if s["id"] == "hallucinated-package"
        )
        result = mod.score_contract({
            "scenario_id": scenario["id"],
            "tier": 2,
            "approval_required": scenario["approval_required"],
            "controls": scenario["required_controls"],
            "forbidden_actions": scenario["forbidden_controls"],
        }, catalog)
        self.assertTrue(result["passed"])
        self.assertEqual(result["tier_assessment"], "conservative_escalation")
        self.assertEqual(result["max_acceptable_tier"], 2)

    def test_benchmark_rejects_overengineering_above_policy_ceiling(self):
        mod = load_script("evaluate_agent_output.py")
        catalog = json.loads((ROOT / "evals" / "scenarios.json").read_text(encoding="utf-8"))
        scenario = next(
            s for s in catalog["scenarios"]
            if s["id"] == "tiny-copy-fix"
        )
        result = mod.score_contract({
            "scenario_id": scenario["id"],
            "tier": 1,
            "approval_required": scenario["approval_required"],
            "controls": scenario["required_controls"],
            "forbidden_actions": scenario["forbidden_controls"],
        }, catalog)
        self.assertFalse(result["passed"])
        self.assertEqual(result["tier_assessment"], "overengineered")
        self.assertTrue(
            any(f.startswith("tier_overengineered:") for f in result["failures"])
        )

    def test_benchmark_rejects_underclassified_risk(self):
        mod = load_script("evaluate_agent_output.py")
        catalog = json.loads((ROOT / "evals" / "scenarios.json").read_text(encoding="utf-8"))
        scenario = next(
            s for s in catalog["scenarios"]
            if s["id"] == "new-payment-integration"
        )
        result = mod.score_contract({
            "scenario_id": scenario["id"],
            "tier": 1,
            "approval_required": scenario["approval_required"],
            "controls": scenario["required_controls"],
            "forbidden_actions": scenario["forbidden_controls"],
        }, catalog)
        self.assertFalse(result["passed"])
        self.assertEqual(result["tier_assessment"], "underclassified")
        self.assertTrue(
            any(f.startswith("tier_underclassified:") for f in result["failures"])
        )


    def test_benchmark_prompt_is_blind(self):
        runner = load_script("run_agent_benchmark.py")
        catalog = json.loads((ROOT / "evals" / "scenarios.json").read_text(encoding="utf-8"))
        scenario = next(s for s in catalog["scenarios"] if s["id"] == "destructive-migration")
        prompt = runner.blind_prompt("codex", scenario)
        self.assertIn(scenario["prompt"], prompt)
        self.assertNotIn(str(scenario["expected_tier"]), prompt.split("Scenario:", 1)[0])
        for control in scenario["required_controls"] + scenario["forbidden_controls"]:
            self.assertNotIn(control, prompt)

    def test_envelope_integrity_is_scored(self):
        mod = load_script("evaluate_agent_output.py")
        catalog = json.loads((ROOT / "evals" / "scenarios.json").read_text(encoding="utf-8"))
        scenario = next(s for s in catalog["scenarios"] if s["id"] == "tiny-copy-fix")
        envelope = {
            "agent": "codex",
            "agent_version": "test",
            "model": "test",
            "skill_version": "0.8.0",
            "started_at": "2026-01-01T00:00:00Z",
            "completed_at": "2026-01-01T00:00:01Z",
            "integrity": {
                "blind": True,
                "expected_contract_not_provided": True,
                "workspace_clean_after": True,
            },
            "schema_failures": [],
            "contract": {
                "scenario_id": scenario["id"],
                "tier": scenario["expected_tier"],
                "approval_required": scenario["approval_required"],
                "controls": scenario["required_controls"],
                "forbidden_actions": scenario["forbidden_controls"],
            },
        }
        scored = mod.score_contract(envelope, catalog)
        self.assertTrue(scored["passed"])
        envelope["integrity"]["workspace_clean_after"] = False
        scored = mod.score_contract(envelope, catalog)
        self.assertFalse(scored["passed"])
        self.assertIn("integrity:workspace_mutated", scored["failures"])

    def test_benchmark_aggregator_marks_missing_runs_incomplete(self):
        catalog = json.loads((ROOT / "evals" / "scenarios.json").read_text(encoding="utf-8"))
        scenario = catalog["scenarios"][0]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            agent_dir = root / "codex"
            agent_dir.mkdir()
            envelope = {
                "schema_version": 1,
                "agent": "codex",
                "agent_version": "test",
                "model": "test",
                "skill_version": "0.8.0",
                "started_at": "2026-01-01T00:00:00Z",
                "completed_at": "2026-01-01T00:00:01Z",
                "runtime": {"exit_code": 0, "duration_ms": 1, "timed_out": False},
                "integrity": {
                    "blind": True,
                    "expected_contract_not_provided": True,
                    "workspace_clean_after": True,
                },
                "schema_failures": [],
                "contract": {
                    "scenario_id": scenario["id"],
                    "tier": scenario["expected_tier"],
                    "approval_required": scenario["approval_required"],
                    "controls": scenario["required_controls"],
                    "forbidden_actions": scenario["forbidden_controls"],
                },
            }
            (agent_dir / f"{scenario['id']}.json").write_text(
                json.dumps(envelope), encoding="utf-8"
            )
            out = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "benchmark_agent_outputs.py"),
                    str(root),
                    "--required-agent",
                    "codex",
                    "--required-agent",
                    "claude-code",
                    "--require-complete",
                    "--json",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(out.returncode, 2)
            data = json.loads(out.stdout)
            self.assertFalse(data["evidence_complete"])
            self.assertIn("claude-code", data["missing_required_agents"])
            codex = next(row for row in data["agents"] if row["agent"] == "codex")
            self.assertIsNone(codex["conformance_rate"])
            self.assertGreater(len(codex["missing_scenarios"]), 0)

    def test_benchmark_preflight_does_not_expose_secret_values(self):
        runner = load_script("run_agent_benchmark.py")
        original = os.environ.get("OPENAI_API_KEY")
        try:
            os.environ["OPENAI_API_KEY"] = "super-secret-benchmark-key"
            result = runner.preflight("codex", True)
            rendered = json.dumps(result)
            self.assertNotIn("super-secret-benchmark-key", rendered)
            self.assertIn("OPENAI_API_KEY", result["auth"]["present_env_names"])
        finally:
            if original is None:
                os.environ.pop("OPENAI_API_KEY", None)
            else:
                os.environ["OPENAI_API_KEY"] = original


    def test_benchmark_aggregator_reports_both_agents_missing_when_empty(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "benchmark_agent_outputs.py"),
                    str(root),
                    "--required-agent",
                    "codex",
                    "--required-agent",
                    "claude-code",
                    "--require-complete",
                    "--json",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(out.returncode, 2)
            data = json.loads(out.stdout)
            self.assertFalse(data["evidence_complete"])
            self.assertEqual(
                data["missing_required_agents"],
                ["claude-code", "codex"],
            )
            self.assertEqual(
                {row["agent"] for row in data["agents"]},
                {"codex", "claude-code"},
            )
            self.assertTrue(
                all(row["conformance_rate"] is None for row in data["agents"])
            )

    def test_real_agent_workflow_isolates_agent_failures(self):
        workflow = (
            ROOT / ".github" / "workflows" / "agent-benchmark.yml"
        ).read_text(encoding="utf-8")

        protected_steps = [
            "Install Codex CLI",
            "Install Claude Code CLI",
            "Preflight Codex",
            "Preflight Claude Code",
            "Run Codex blind benchmark",
            "Run Claude Code blind benchmark",
        ]
        for name in protected_steps:
            marker = f"- name: {name}\n        continue-on-error: true"
            self.assertIn(marker, workflow)

        aggregate_marker = (
            "- name: Require complete evidence and aggregate\n"
            "        if: always()"
        )
        upload_marker = (
            "- name: Upload raw benchmark evidence\n"
            "        if: always()"
        )
        self.assertIn(aggregate_marker, workflow)
        self.assertIn(upload_marker, workflow)
        self.assertIn("set -o pipefail", workflow)
        self.assertIn('mkdir -p "$RESULTS_DIR"', workflow)
        self.assertNotIn("- name: Require benchmark credentials", workflow)


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
