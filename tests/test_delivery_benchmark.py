from __future__ import annotations

import importlib.util
import json
import os
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
                )
            )

        self.assertTrue(
            aggregate["evidence_complete"],
            aggregate,
        )
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


if __name__ == "__main__":
    unittest.main()
