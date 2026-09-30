from __future__ import annotations

import importlib.util
import copy
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(
        "test_delivery_" + name.replace(".py", ""),
        path,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def write_grader(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "import argparse,json\n"
        "from pathlib import Path\n"
        "ap=argparse.ArgumentParser()\n"
        "ap.add_argument('--workspace',required=True)\n"
        "ap.add_argument('--json',action='store_true')\n"
        "ns=ap.parse_args()\n"
        "ok=(Path(ns.workspace)/'message.txt').read_text()=="
        "'implemented\\n'\n"
        "print(json.dumps({'schema_version':1,'checks':["
        "{'id':'message-updated','category':'functional',"
        "'required':True,'passed':ok}],'metrics':{}}))\n",
        encoding="utf-8",
    )


def setup_contract(base: Path):
    delivery_root = base / "delivery"
    fixture = delivery_root / "fixtures" / "demo"
    grader = delivery_root / "graders" / "demo.py"
    fixture.mkdir(parents=True, exist_ok=True)
    (fixture / "message.txt").write_text(
        "baseline\n",
        encoding="utf-8",
    )
    write_grader(grader)
    scenario = {
        "id": "demo",
        "prompt": "Update message.txt.",
        "fixture": "fixtures/demo",
        "grader": "graders/demo.py",
        "network_policy": "disabled",
        "forbidden_paths": ["secrets/**"],
        "repetitions": 1,
    }
    catalog = {
        "schema_version": 1,
        "benchmark": "real-delivery",
        "default_repetitions": 1,
        "scenarios": [scenario],
    }
    catalog_path = base / "scenarios.json"
    catalog_path.write_text(
        json.dumps(catalog),
        encoding="utf-8",
    )
    schema_path = base / "schema.json"
    schema_path.write_text(
        "{}",
        encoding="utf-8",
    )
    portable_skill = base / "portable-skill"
    portable_skill.mkdir()
    (portable_skill / "SKILL.md").write_text(
        "# Test Skill\n",
        encoding="utf-8",
    )
    return (
        delivery_root,
        scenario,
        catalog,
        catalog_path,
        schema_path,
        portable_skill,
    )


def good_executor(
    workspace,
    prompt,
    arm,
    scenario,
    timeout,
    env,
):
    (workspace / "message.txt").write_text(
        "implemented\n",
        encoding="utf-8",
    )
    return {
        "exit_code": 0,
        "stdout": "ok",
        "stderr": "",
        "agent_version": "fake-1",
        "model": "fake-model",
        "executor_id": "fake",
        "usage": {"turns": 1},
    }


def noop_executor(
    workspace,
    prompt,
    arm,
    scenario,
    timeout,
    env,
):
    return {
        "exit_code": 0,
        "stdout": "no change",
        "stderr": "",
        "agent_version": "fake-1",
        "model": "fake-model",
        "executor_id": "fake",
        "usage": {"turns": 1},
    }


class DeliveryRunnerTests(unittest.TestCase):
    def setUp(self):
        self.runner = load_script(
            "run_delivery_benchmark.py"
        )

    def test_catalog_rejects_grader_outside_hidden_grader_root(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            delivery_root = base / "delivery"
            fixture = (
                delivery_root
                / "fixtures"
                / "demo"
            )
            fixture.mkdir(parents=True)
            (fixture / "grader.py").write_text(
                "print('{}')\n",
                encoding="utf-8",
            )
            catalog = {
                "schema_version": 1,
                "benchmark": "real-delivery",
                "default_repetitions": 1,
                "scenarios": [
                    {
                        "id": "demo",
                        "prompt": "Change it.",
                        "fixture": "fixtures/demo",
                        "grader": (
                            "fixtures/demo/grader.py"
                        ),
                        "network_policy": "disabled",
                        "forbidden_paths": [],
                    }
                ],
            }
            failures = self.runner.validate_catalog(
                catalog,
                delivery_root=delivery_root,
            )
        self.assertTrue(failures)
        self.assertTrue(
            any(
                "must stay under" in failure
                for failure in failures
            )
        )

    def test_control_and_treatment_record_same_product_change(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (
                delivery_root,
                scenario,
                _catalog,
                catalog_path,
                schema_path,
                portable_skill,
            ) = setup_contract(base)

            rows = {}
            for arm in ("control", "treatment"):
                rows[arm] = self.runner.run_one(
                    agent="fake",
                    scenario=scenario,
                    arm=arm,
                    repetition=1,
                    result_dir=(
                        base
                        / "results"
                        / arm
                    ),
                    executor=good_executor,
                    timeout=5,
                    grader_timeout=5,
                    delivery_root=delivery_root,
                    portable_skill=portable_skill,
                    catalog_path=catalog_path,
                    result_schema_path=schema_path,
                )

        self.assertTrue(
            rows["control"]["grader"][
                "delivery_success"
            ]
        )
        self.assertTrue(
            rows["treatment"]["grader"][
                "delivery_success"
            ]
        )
        self.assertEqual(
            rows["control"]["workspace"][
                "changed_paths"
            ],
            ["message.txt"],
        )
        self.assertEqual(
            rows["treatment"]["workspace"][
                "changed_paths"
            ],
            ["message.txt"],
        )
        self.assertFalse(
            rows["control"]["integrity"][
                "skill_installed"
            ]
        )
        self.assertTrue(
            rows["treatment"]["integrity"][
                "skill_installed"
            ]
        )
        self.assertTrue(
            rows["treatment"]["integrity"][
                "hidden_grader_outside_workspace"
            ]
        )

    def test_executor_environment_strips_provider_secrets(self):
        observed = {}

        def inspect_executor(
            workspace,
            prompt,
            arm,
            scenario,
            timeout,
            env,
        ):
            observed.update(env)
            return good_executor(
                workspace,
                prompt,
                arm,
                scenario,
                timeout,
                env,
            )

        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (
                delivery_root,
                scenario,
                _catalog,
                catalog_path,
                schema_path,
                portable_skill,
            ) = setup_contract(base)
            with mock.patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "secret-openai",
                    "ANTHROPIC_API_KEY": (
                        "secret-anthropic"
                    ),
                },
                clear=False,
            ):
                self.runner.run_one(
                    agent="fake",
                    scenario=scenario,
                    arm="control",
                    repetition=1,
                    result_dir=base / "results",
                    executor=inspect_executor,
                    timeout=5,
                    grader_timeout=5,
                    delivery_root=delivery_root,
                    portable_skill=portable_skill,
                    catalog_path=catalog_path,
                    result_schema_path=schema_path,
                )

        self.assertNotIn(
            "OPENAI_API_KEY",
            observed,
        )
        self.assertNotIn(
            "ANTHROPIC_API_KEY",
            observed,
        )

    def test_forbidden_path_mutation_blocks_delivery(self):
        def bad_executor(
            workspace,
            prompt,
            arm,
            scenario,
            timeout,
            env,
        ):
            result = good_executor(
                workspace,
                prompt,
                arm,
                scenario,
                timeout,
                env,
            )
            path = workspace / "secrets" / "config.txt"
            path.parent.mkdir()
            path.write_text(
                "mutated\n",
                encoding="utf-8",
            )
            return result

        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (
                delivery_root,
                scenario,
                _catalog,
                catalog_path,
                schema_path,
                portable_skill,
            ) = setup_contract(base)
            row = self.runner.run_one(
                agent="fake",
                scenario=scenario,
                arm="control",
                repetition=1,
                result_dir=base / "results",
                executor=bad_executor,
                timeout=5,
                grader_timeout=5,
                delivery_root=delivery_root,
                portable_skill=portable_skill,
                catalog_path=catalog_path,
                result_schema_path=schema_path,
            )

        self.assertFalse(
            row["grader"]["delivery_success"]
        )
        self.assertEqual(
            row["workspace"][
                "forbidden_path_hits"
            ],
            ["secrets/config.txt"],
        )
        self.assertTrue(
            any(
                failure.startswith(
                    "forbidden_path_mutation:"
                )
                for failure in row[
                    "grader"
                ]["failures"]
            )
        )

    def test_grader_mutations_do_not_contaminate_agent_tree_hash(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            delivery_root = base / "delivery"
            fixture = delivery_root / "fixtures" / "snapshot"
            grader = delivery_root / "graders" / "snapshot.py"
            fixture.mkdir(parents=True)
            grader.parent.mkdir(parents=True)
            (fixture / "message.txt").write_text(
                "baseline\n",
                encoding="utf-8",
            )
            grader.write_text(
                "import argparse,json\n"
                "from pathlib import Path\n"
                "ap=argparse.ArgumentParser()\n"
                "ap.add_argument('--workspace',required=True)\n"
                "ap.add_argument('--json',action='store_true')\n"
                "ns=ap.parse_args()\n"
                "(Path(ns.workspace)/'grader-artifact.txt').write_text('built')\n"
                "print(json.dumps({'schema_version':1,'checks':["
                "{'id':'artifact','category':'artifact',"
                "'required':True,'passed':True}],'metrics':{}}))\n",
                encoding="utf-8",
            )
            scenario = {
                "id": "snapshot",
                "prompt": "Do nothing.",
                "fixture": "fixtures/snapshot",
                "grader": "graders/snapshot.py",
                "network_policy": "disabled",
                "forbidden_paths": [],
            }
            catalog_path = base / "scenarios.json"
            catalog_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "benchmark": "real-delivery",
                        "default_repetitions": 1,
                        "scenarios": [scenario],
                    }
                ),
                encoding="utf-8",
            )
            schema_path = base / "schema.json"
            schema_path.write_text("{}", encoding="utf-8")
            portable = base / "portable"
            portable.mkdir()
            (portable / "SKILL.md").write_text("# test\n", encoding="utf-8")

            row = self.runner.run_one(
                agent="fake",
                scenario=scenario,
                arm="control",
                repetition=1,
                result_dir=base / "results",
                executor=noop_executor,
                timeout=5,
                grader_timeout=5,
                delivery_root=delivery_root,
                portable_skill=portable,
                catalog_path=catalog_path,
                result_schema_path=schema_path,
            )

            self.assertEqual(row["workspace"]["changed_paths"], [])
            self.assertEqual(
                row["workspace"]["final_tree_sha256"],
                self.runner.tree_hash(fixture),
            )
            self.assertTrue(row["grader"]["delivery_success"])

    def test_framework_self_test_passes(self):
        result = self.runner.self_test()
        self.assertTrue(
            result["passed"],
            result,
        )
        self.assertFalse(
            result["arms"]["control"][
                "skill_installed"
            ]
        )
        self.assertTrue(
            result["arms"]["treatment"][
                "skill_installed"
            ]
        )

    def test_local_commit_cannot_hide_changes_or_forbidden_rename(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            delivery_root, scenario, _, _, _, portable = setup_contract(base)
            workspace = base / "workspace"
            fixture, _ = self.runner.scenario_paths(scenario, delivery_root)
            info = self.runner.prepare_workspace(fixture, workspace, arm="control",
                agent="fake", portable_skill=portable)
            baseline = info["baseline_commit"]
            (workspace / "secrets").mkdir()
            (workspace / "message.txt").rename(workspace / "secrets/message.txt")
            paths = self.runner.changed_paths(workspace, baseline)
            digest = self.runner.diff_hash(workspace, paths, baseline)
            self.runner.git(workspace, "add", "-A")
            committed = self.runner.git(workspace, "commit", "-qm", "agent local commit")
            self.assertEqual(committed.returncode, 0, committed.stderr)
            self.assertEqual(self.runner.changed_paths(workspace, baseline), paths)
            self.assertEqual(self.runner.diff_hash(workspace, paths, baseline), digest)
            self.assertEqual(paths, ["message.txt", "secrets/message.txt"])
            self.assertEqual(self.runner.forbidden_path_hits(paths, ["secrets/**"]),
                             ["secrets/message.txt"])


class RealDeliveryAdapterTests(unittest.TestCase):
    def setUp(self):
        self.runner = load_script("run_delivery_benchmark.py")

    def test_codex_delivery_command_is_workspace_bounded(self):
        command = self.runner.build_real_command(
            "codex",
            {"binary": "codex"},
            "implement",
            model=None,
            max_turns=8,
            max_budget_usd=None,
        )
        self.assertIn("workspace-write", command)
        self.assertIn("never", command)
        self.assertNotIn("danger-full-access", command)

    def test_claude_delivery_command_allows_only_sandboxed_shell(self):
        command = self.runner.build_real_command(
            "claude-code",
            {"binary": "claude"},
            "implement",
            model=None,
            max_turns=8,
            max_budget_usd=1.0,
        )
        joined = " ".join(command)
        self.assertIn("--permission-mode acceptEdits", joined)
        self.assertIn("Read,Edit,Write,Glob,Grep", joined)
        self.assertIn("WebFetch,WebSearch,mcp__*", joined)
        self.assertIn("Bash", command[command.index("--tools") + 1].split(","))
        settings = json.loads(command[command.index("--settings") + 1])
        self.assertTrue(settings["sandbox"]["enabled"])
        self.assertTrue(settings["sandbox"]["failIfUnavailable"])
        self.assertFalse(settings["sandbox"]["allowUnsandboxedCommands"])
        self.assertEqual(settings["sandbox"]["network"]["allowedDomains"], [])

    def test_real_executor_redacts_credentials_and_flags_workspace_leak(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            secret = "benchmark-secret-value"

            def fake_run(command, cwd, env, text, capture_output, timeout):
                (cwd / "leak.txt").write_text(secret, encoding="utf-8")
                return self.runner.subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=f"token={secret}",
                    stderr=f"error={secret}",
                )

            spec = {
                "display_name": "Fake",
                "binary": "codex",
                "version_args": ["--version"],
                "auth_env": ["OPENAI_API_KEY"],
            }
            with mock.patch.dict(
                os.environ,
                {"OPENAI_API_KEY": secret},
                clear=False,
            ), mock.patch.object(
                self.runner,
                "load_agent",
                return_value=spec,
            ), mock.patch.object(
                self.runner.subprocess,
                "run",
                side_effect=fake_run,
            ), mock.patch.object(
                self.runner,
                "cli_version",
                return_value="fake-1",
            ):
                executor = self.runner.real_executor(
                    "codex",
                    model=None,
                    max_turns=8,
                    max_budget_usd=None,
                )
                result = executor(
                    workspace,
                    "implement",
                    "control",
                    {"id": "demo"},
                    10,
                    {"PATH": os.environ.get("PATH", "")},
                )

        self.assertNotIn(secret, result["stdout"])
        self.assertNotIn(secret, result["stderr"])
        self.assertTrue(result["security_failures"])
        self.assertIn("leak.txt", result["security_failures"][0])


class DeliveryAggregatorTests(unittest.TestCase):
    def setUp(self):
        self.runner = load_script(
            "run_delivery_benchmark.py"
        )
        self.aggregator = load_script(
            "benchmark_delivery_outputs.py"
        )

    def test_missing_treatment_run_is_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (
                delivery_root,
                scenario,
                catalog,
                catalog_path,
                schema_path,
                portable_skill,
            ) = setup_contract(base)
            results = base / "results"
            self.runner.run_one(
                agent="fake",
                scenario=scenario,
                arm="control",
                repetition=1,
                result_dir=results,
                executor=good_executor,
                timeout=5,
                grader_timeout=5,
                delivery_root=delivery_root,
                portable_skill=portable_skill,
                catalog_path=catalog_path,
                result_schema_path=schema_path,
            )

            aggregate = (
                self.aggregator.aggregate(
                    results,
                    catalog,
                    required_agents=["fake"],
                    delivery_root=delivery_root,
                )
            )

        self.assertFalse(
            aggregate["evidence_complete"]
        )
        self.assertEqual(
            len(aggregate["missing_runs"]),
            1,
        )
        self.assertEqual(
            aggregate["missing_runs"][0][
                "arm"
            ],
            "treatment",
        )

    def test_pairwise_aggregation_reports_improvement(self):
        def arm_executor(
            workspace,
            prompt,
            arm,
            scenario,
            timeout,
            env,
        ):
            if arm == "treatment":
                return good_executor(
                    workspace,
                    prompt,
                    arm,
                    scenario,
                    timeout,
                    env,
                )
            return noop_executor(
                workspace,
                prompt,
                arm,
                scenario,
                timeout,
                env,
            )

        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (
                delivery_root,
                scenario,
                catalog,
                catalog_path,
                schema_path,
                portable_skill,
            ) = setup_contract(base)
            results = base / "results"
            for arm in (
                "control",
                "treatment",
            ):
                self.runner.run_one(
                    agent="fake",
                    scenario=scenario,
                    arm=arm,
                    repetition=1,
                    result_dir=results,
                    executor=arm_executor,
                    timeout=5,
                    grader_timeout=5,
                    delivery_root=delivery_root,
                    portable_skill=portable_skill,
                    catalog_path=catalog_path,
                    result_schema_path=schema_path,
                )

            aggregate = (
                self.aggregator.aggregate(
                    results,
                    catalog,
                    required_agents=["fake"],
                    delivery_root=delivery_root,
                )
            )

        self.assertTrue(
            aggregate["framework_complete"],
            aggregate,
        )
        self.assertFalse(aggregate["evidence_complete"])
        self.assertEqual(aggregate["execution_class"], "framework")
        comparison = aggregate[
            "comparisons"
        ][0]
        self.assertEqual(
            comparison["effect"],
            "improved",
        )
        self.assertEqual(
            comparison["control"][
                "success_rate"
            ],
            0.0,
        )
        self.assertEqual(
            comparison["treatment"][
                "success_rate"
            ],
            1.0,
        )
        self.assertEqual(
            comparison[
                "success_rate_delta"
            ],
            1.0,
        )

    def test_contradictory_or_unidentifiable_envelopes_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            delivery_root, scenario, _, catalog_path, schema_path, portable = setup_contract(base)
            row = self.runner.run_one(agent="fake", scenario=scenario, arm="control",
                repetition=1, result_dir=base / "results", executor=good_executor,
                timeout=5, grader_timeout=5, delivery_root=delivery_root,
                portable_skill=portable, catalog_path=catalog_path, result_schema_path=schema_path)
        self.assertEqual(self.aggregator.envelope_issues(row), [])
        mutations = [
            ("runtime", "exit_code", 9), ("runtime", "timed_out", True),
            ("runtime", "duration_ms", -1), ("runtime", "exit_code", False),
            ("grader", "failures", ["failed"]), ("grader", "timed_out", True),
            ("workspace", "diff_sha256", "z" * 64), ("workspace", "changed_file_count", 99),
            ("integrity", "skill_installed", True),
            (None, "model", None), (None, "agent_version", ""),
            (None, "completed_at", "2000-01-01T00:00:00Z"),
        ]
        for section, key, value in mutations:
            with self.subTest(section=section, key=key):
                changed = copy.deepcopy(row)
                (changed[section] if section else changed)[key] = value
                self.assertTrue(self.aggregator.envelope_issues(changed))
        for checks in ([], [dict(row["grader"]["checks"][0], required=False)],
                       [dict(row["grader"]["checks"][0], passed=False)]):
            changed = copy.deepcopy(row)
            changed["grader"]["checks"] = checks
            self.assertTrue(self.aggregator.envelope_issues(changed))
        failed = copy.deepcopy(row)
        failed["runtime"]["exit_code"] = 9
        failed["grader"]["delivery_success"] = False
        self.assertEqual(self.aggregator.envelope_issues(failed), [])

    def test_injected_executor_cannot_self_declare_real_execution(self):
        def spoof_executor(*args):
            return dict(good_executor(*args), executor_id="real-codex")
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            delivery_root, scenario, _, catalog_path, schema_path, portable = setup_contract(base)
            row = self.runner.run_one(agent="codex", scenario=scenario, arm="control",
                repetition=1, result_dir=base / "results", executor=spoof_executor,
                timeout=5, grader_timeout=5, delivery_root=delivery_root,
                portable_skill=portable, catalog_path=catalog_path, result_schema_path=schema_path)
        self.assertEqual(row["integrity"]["executor_id"], "injected-executor")

    def test_scenario_identity_and_required_checks_are_bound_to_catalog(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            delivery_root, scenario, catalog, catalog_path, schema_path, portable = setup_contract(base)
            results = base / "results"
            row = self.runner.run_one(agent="fake", scenario=scenario, arm="control",
                repetition=1, result_dir=results, executor=good_executor,
                timeout=5, grader_timeout=5, delivery_root=delivery_root,
                portable_skill=portable, catalog_path=catalog_path, result_schema_path=schema_path)
            envelope = next(results.rglob("*.json"))
            row["integrity"]["grader_sha256"] = "0" * 64
            envelope.write_text(json.dumps(row), encoding="utf-8")
            aggregate = self.aggregator.aggregate(results, catalog, required_agents=["fake"],
                                                 delivery_root=delivery_root)
            self.assertTrue(aggregate["invalid_files"])
            self.assertFalse(aggregate["framework_complete"])
            catalog["scenarios"][0]["required_check_ids"] = ["independent-outcome"]
            row["integrity"]["grader_sha256"] = self.runner.sha256_file(delivery_root / "graders/demo.py")
            envelope.write_text(json.dumps(row), encoding="utf-8")
            aggregate = self.aggregator.aggregate(results, catalog, required_agents=["fake"],
                                                 delivery_root=delivery_root)
            self.assertIn("catalog-required", aggregate["invalid_files"][0]["error"])



class RepresentativeDeliveryFixtureTests(unittest.TestCase):
    def setUp(self):
        self.runner = load_script("run_delivery_benchmark.py")
        self.delivery_root = ROOT / "evals" / "delivery"
        self.catalog = json.loads(
            (self.delivery_root / "scenarios.json").read_text(encoding="utf-8")
        )
        self.scenarios = {
            row["id"]: row
            for row in self.catalog["scenarios"]
        }

    def grade(self, scenario_id, mutate=None):
        import shutil

        scenario = self.scenarios[scenario_id]
        fixture, grader = self.runner.scenario_paths(
            scenario,
            self.delivery_root,
        )
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            workspace = base / "workspace"
            shutil.copytree(fixture, workspace)
            if mutate is not None:
                mutate(workspace)
            result = self.runner.run_hidden_grader(
                grader,
                workspace,
                timeout=10,
                env=os.environ.copy(),
            )
        self.assertFalse(result["failures"], result)
        return result["parsed"]["checks"]

    @staticmethod
    def required_passed(checks):
        return all(
            check["passed"]
            for check in checks
            if check["required"]
        )

    def test_catalog_contains_five_representative_scenarios(self):
        self.assertEqual(
            set(self.scenarios),
            {
                "tiny-local-copy-fix",
                "brownfield-duplicate-filter",
                "contained-csv-export",
                "mixed-monorepo-api-normalization",
                "wordpress-installable-artifact",
            },
        )
        self.assertEqual(
            self.runner.validate_catalog(self.catalog),
            [],
        )

    def test_tiny_fixture_good_passes_and_baseline_fails(self):
        broken = self.grade("tiny-local-copy-fix")
        self.assertFalse(self.required_passed(broken))

        def fix(workspace):
            path = workspace / "app.py"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "Welcomme",
                    "Welcome",
                ),
                encoding="utf-8",
            )

        good = self.grade("tiny-local-copy-fix", fix)
        self.assertTrue(self.required_passed(good))

    def test_brownfield_fixture_good_passes_and_baseline_fails(self):
        broken = self.grade("brownfield-duplicate-filter")
        self.assertFalse(self.required_passed(broken))

        def fix(workspace):
            filters = workspace / "app" / "filters.py"
            filters.write_text(
                filters.read_text(encoding="utf-8").replace(
                    "        self._filters.append(name)\n",
                    "        if name not in self._filters:\n"
                    "            self._filters.append(name)\n",
                ),
                encoding="utf-8",
            )
            tests = workspace / "tests" / "test_filters.py"
            source = tests.read_text(encoding="utf-8")
            source = source.replace(
                "\n\nif __name__ == \"__main__\":\n",
                "\n"
                "    def test_duplicate_save_is_idempotent(self):\n"
                "        store = FilterStore()\n"
                "        store.save(\"open-orders\")\n"
                "        store.save(\"open-orders\")\n"
                "        self.assertEqual(store.all(), [\"open-orders\"])\n"
                "\n\nif __name__ == \"__main__\":\n",
            )
            tests.write_text(source, encoding="utf-8")

        good = self.grade("brownfield-duplicate-filter", fix)
        self.assertTrue(self.required_passed(good))

    def test_contained_feature_good_passes_and_baseline_fails(self):
        broken = self.grade("contained-csv-export")
        self.assertFalse(self.required_passed(broken))

        def fix(workspace):
            path = workspace / "reports.py"
            path.write_text(
                "import csv\n"
                "import io\n\n"
                "def summarize(rows: list[dict[str, str]]) -> int:\n"
                "    return len(rows)\n\n"
                "def export_csv(rows: list[dict[str, str]]) -> str:\n"
                "    output = io.StringIO()\n"
                "    writer = csv.writer(output)\n"
                "    writer.writerow([\"id\", \"name\"])\n"
                "    for row in rows:\n"
                "        writer.writerow([row[\"id\"], row[\"name\"]])\n"
                "    return output.getvalue()\n",
                encoding="utf-8",
            )

        good = self.grade("contained-csv-export", fix)
        self.assertTrue(self.required_passed(good))

    def test_mixed_monorepo_good_passes_and_baseline_fails(self):
        broken = self.grade("mixed-monorepo-api-normalization")
        self.assertFalse(self.required_passed(broken))

        def fix(workspace):
            path = workspace / "apps" / "api" / "service.py"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    '    customer = {"email": email}\n',
                    '    customer = {"email": email.strip().lower()}\n',
                ),
                encoding="utf-8",
            )

        good = self.grade("mixed-monorepo-api-normalization", fix)
        self.assertTrue(self.required_passed(good))

    @unittest.skipUnless(shutil.which("php"), "PHP CLI required for executed WordPress behavior")
    def test_wordpress_artifact_good_passes_and_baseline_fails(self):
        broken = self.grade("wordpress-installable-artifact")
        self.assertFalse(self.required_passed(broken))

        def fix(workspace):
            path = (
                workspace
                / "sample-plugin"
                / "includes"
                / "admin.php"
            )
            path.write_text(
                "<?php\n\n"
                "if (!defined('ABSPATH')) { exit; }\n\n"
                "function sample_plugin_register_settings(): void {\n"
                "    register_setting('general', 'sample_label', [\n"
                "        'type' => 'string',\n"
                "        'sanitize_callback' => 'sanitize_text_field',\n"
                "        'default' => '',\n"
                "    ]);\n"
                "}\n"
                "add_action('admin_init', 'sample_plugin_register_settings');\n\n"
                "function sample_plugin_render_label_field(): void {\n"
                "    $value = get_option('sample_label', '');\n"
                "    printf(\n"
                "        '<input type=\"text\" name=\"sample_label\" value=\"%s\" />',\n"
                "        esc_attr($value)\n"
                "    );\n"
                "}\n",
                encoding="utf-8",
            )

        good = self.grade("wordpress-installable-artifact", fix)
        self.assertTrue(self.required_passed(good))

    def test_wordpress_comment_only_feature_is_rejected(self):
        def fake_fix(workspace):
            (workspace / "sample-plugin/includes/admin.php").write_text(
                "<?php\n// sample_label register_setting sanitize_text_field esc_attr\n"
                "function sample_plugin_render_label_field(): void {}\n", encoding="utf-8")
        checks = self.grade("wordpress-installable-artifact", fake_fix)
        self.assertFalse(self.required_passed(checks))
        self.assertFalse(next(row for row in checks if row["id"] == "setting-registered-and-sanitized")["passed"])

    @unittest.skipUnless(shutil.which("php"), "PHP CLI required for executed WordPress behavior")
    def test_wordpress_registered_but_unsafe_output_is_rejected(self):
        def unsafe_fix(workspace):
            (workspace / "sample-plugin/includes/admin.php").write_text(
                "<?php\nadd_action('admin_init', function() { register_setting('general', 'sample_label', "
                "['sanitize_callback' => 'sanitize_text_field']); });\n"
                "function sample_plugin_render_label_field(): void { "
                "echo '<input type=\"text\" name=\"sample_label\" value=\"' . get_option('sample_label') . '\" />'; }\n",
                encoding="utf-8")
        checks = self.grade("wordpress-installable-artifact", unsafe_fix)
        self.assertTrue(next(row for row in checks if row["id"] == "setting-registered-and-sanitized")["passed"])
        self.assertFalse(next(row for row in checks if row["id"] == "setting-input-escaped")["passed"])


if __name__ == "__main__":
    unittest.main()
