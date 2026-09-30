#!/usr/bin/env python3
"""Lightweight repository validation without third-party Python dependencies."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
REQUIRED_REFS = [
    "references/operating-model.md",
    "references/risk-and-autonomy.md",
    "references/project-intelligence.md",
    "references/security-and-dependencies.md",
    "references/project-state-and-traceability.md",
    "references/execution-and-verification.md",
    "references/bootstrap-and-evals.md",
    "references/risk-classifier-and-integrations.md",
    "references/validation-and-benchmarking.md",
    "references/local-workspace-and-repository-purity.md",
    "references/graph-provider-contract.md",
    "references/github-traceability-automation.md",
    "references/project-state-automation.md",
    "references/recovery-and-resume.md",
    "references/installation-and-lifecycle.md",
    "references/context-routing-and-execution.md",
]
REQUIRED_SCRIPTS = [
    "doctor.py",
    "change_budget.py",
    "graphify_compat.py",
    "trivy_compat.py",
    "bootstrap_project.py",
    "dependency_guard.py",
    "risk_classifier.py",
    "integration_guard.py",
    "context_router.py",
    "execution_plan.py",
    "validate_evals.py",
    "run_evals.py",
    "evaluate_agent_output.py",
    "live_dependency_evals.py",
    "sync_package.py",
    "completion_gate.py",
    "run_project_validations.py",
    "run_real_world_validations.py",
    "run_failure_injections.py",
    "benchmark_agent_outputs.py",
    "run_agent_benchmark.py",
    "run_delivery_benchmark.py",
    "benchmark_delivery_outputs.py",
    "release_readiness.py",
    "local_workspace.py",
    "repository_purity.py",
    "graph_provider.py",
    "github_traceability.py",
    "project_state.py",
    "resume_context.py",
    "state_recovery.py",
    "install_check.py",
    "skill_lifecycle.py",
    "toolchain_runtime.py",
]
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def main() -> int:
    if not SKILL.exists():
        fail("SKILL.md is missing")

    text = SKILL.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail("SKILL.md must start with YAML frontmatter")

    parts = text.split("---", 2)
    if len(parts) != 3:
        fail("invalid frontmatter boundaries")
    _, fm, body = parts

    fields: dict[str, str] = {}
    for line in fm.splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"')

    name = fields.get("name", "")
    description = fields.get("description", "")
    if not NAME_RE.fullmatch(name):
        fail(f"invalid skill name: {name!r}")
    if len(name) > 64:
        fail("skill name exceeds 64 chars")
    if not description or len(description) > 1024:
        fail("description must be 1..1024 chars")
    if len(body.splitlines()) > 260:
        fail("SKILL.md exceeds the 260-line routed-core guard")
    if "\\n" in body:
        fail("SKILL.md contains literal escaped newline sequences; use real newlines")

    version_path = ROOT / "VERSION"
    if not version_path.exists():
        fail("VERSION is missing")
    version = version_path.read_text(encoding="utf-8").strip()
    if not SEMVER_RE.fullmatch(version):
        fail(f"VERSION is not semantic-version shaped: {version!r}")

    metadata_match = re.search(r'(?m)^  version:\s*"([^"]+)"\s*$', fm)
    if not metadata_match:
        fail("SKILL.md metadata.version is missing")
    if metadata_match.group(1) != version:
        fail(f"SKILL.md metadata.version {metadata_match.group(1)!r} != VERSION {version!r}")

    plugin_path = ROOT / "plugin.json"
    if not plugin_path.exists():
        fail("plugin.json is missing")
    plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
    if plugin.get("version") != version:
        fail(f"plugin.json version {plugin.get('version')!r} != VERSION {version!r}")
    if plugin.get("name") != name:
        fail(f"plugin.json name {plugin.get('name')!r} != skill name {name!r}")
    for key in ("description", "license", "repository"):
        if not plugin.get(key):
            fail(f"plugin.json is missing required project metadata: {key}")

    agent_yaml = ROOT / "agents" / "openai.yaml"
    if not agent_yaml.exists():
        fail("agents/openai.yaml is missing")
    agent_text = agent_yaml.read_text(encoding="utf-8")
    for token in ("interface:", "display_name:", "default_prompt:", "$vibe-coding-skill"):
        if token not in agent_text:
            fail(f"agents/openai.yaml is missing expected token: {token}")

    readme = ROOT / "README.md"
    if not readme.exists():
        fail("README.md is missing")
    readme_text = readme.read_text(encoding="utf-8")
    if f"version-{version}-" not in readme_text and f"Current version: `{version}`" not in readme_text:
        fail("README.md version marker does not match VERSION")

    updates = ROOT / "UPDATES.md"
    if not updates.exists():
        fail("UPDATES.md is missing")
    updates_text = updates.read_text(encoding="utf-8")
    if not re.search(rf"(?m)^## {re.escape(version)}(?:\s|$)", updates_text):
        fail(f"UPDATES.md does not contain a human-readable entry for {version}")

    install_guide = ROOT / "HOW_TO_INSTALL.md"
    if not install_guide.exists():
        fail("HOW_TO_INSTALL.md is missing")
    install_text = install_guide.read_text(encoding="utf-8")
    if f"Current Skill version: `{version}`" not in install_text:
        fail("HOW_TO_INSTALL.md version marker does not match VERSION")

    for required_link in ("HOW_TO_INSTALL.md", "UPDATES.md", "CHANGELOG.md"):
        if f"]({required_link})" not in readme_text:
            fail(f"README.md must link to {required_link}")

    for rel in REQUIRED_REFS:
        if not (ROOT / rel).exists():
            fail(f"missing reference: {rel}")
        if rel not in text:
            fail(f"SKILL.md does not reference {rel}")

    benchmark_schema = ROOT / "evals" / "agent-output.schema.json"
    benchmark_agents = ROOT / "config" / "agent-benchmarks.json"
    for path in (benchmark_schema, benchmark_agents):
        if not path.exists():
            fail(f"missing benchmark contract file: {path.relative_to(ROOT)}")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"invalid benchmark contract JSON {path.relative_to(ROOT)}: {exc}")
        if not isinstance(value, dict):
            fail(f"benchmark contract must be a JSON object: {path.relative_to(ROOT)}")

    delivery_catalog = ROOT / "evals" / "delivery" / "scenarios.json"
    delivery_schema = ROOT / "evals" / "delivery-result.schema.json"
    for path in (delivery_catalog, delivery_schema):
        if not path.exists():
            fail(f"missing delivery benchmark contract file: {path.relative_to(ROOT)}")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"invalid delivery benchmark JSON {path.relative_to(ROOT)}: {exc}")
        if not isinstance(value, dict):
            fail(
                "delivery benchmark contract must be a JSON object: "
                f"{path.relative_to(ROOT)}"
            )

    delivery = json.loads(delivery_catalog.read_text(encoding="utf-8"))
    if delivery.get("schema_version") != 1:
        fail("delivery benchmark catalog schema_version must be 1")
    if delivery.get("benchmark") != "real-delivery":
        fail("delivery benchmark catalog must identify real-delivery")
    if not isinstance(delivery.get("scenarios"), list):
        fail("delivery benchmark scenarios must be an array")
    delivery_scenarios = delivery.get("scenarios") or []
    required_delivery_ids = {
        "tiny-local-copy-fix",
        "brownfield-duplicate-filter",
        "contained-csv-export",
        "mixed-monorepo-api-normalization",
        "wordpress-installable-artifact",
    }
    observed_delivery_ids = {
        str(row.get("id") or "").strip()
        for row in delivery_scenarios
        if isinstance(row, dict)
    }
    missing_delivery_ids = sorted(required_delivery_ids - observed_delivery_ids)
    if missing_delivery_ids:
        fail(
            "delivery benchmark is missing representative scenarios: "
            + ",".join(missing_delivery_ids)
        )
    if len(observed_delivery_ids) != len(delivery_scenarios):
        fail("delivery benchmark scenario IDs must be non-empty and unique")

    delivery_root = ROOT / "evals" / "delivery"
    fixtures_root = delivery_root / "fixtures"
    graders_root = delivery_root / "graders"
    for scenario in delivery_scenarios:
        if not isinstance(scenario, dict):
            fail("delivery benchmark scenarios must contain objects")
        scenario_id = str(scenario.get("id") or "").strip()
        fixture_rel = str(scenario.get("fixture") or "").strip()
        grader_rel = str(scenario.get("grader") or "").strip()
        if not str(scenario.get("prompt") or "").strip():
            fail(f"delivery scenario {scenario_id!r} is missing prompt")
        if scenario.get("network_policy") not in {"disabled", "scenario-required"}:
            fail(f"delivery scenario {scenario_id!r} has invalid network_policy")
        if not fixture_rel or not grader_rel:
            fail(f"delivery scenario {scenario_id!r} requires fixture and grader")
        fixture_path = (delivery_root / fixture_rel).resolve()
        grader_path = (delivery_root / grader_rel).resolve()
        try:
            fixture_path.relative_to(fixtures_root.resolve())
            grader_path.relative_to(graders_root.resolve())
        except ValueError:
            fail(
                f"delivery scenario {scenario_id!r} must keep fixtures/graders "
                "under their dedicated hidden-contract roots"
            )
        if not fixture_path.is_dir():
            fail(f"delivery fixture is missing for {scenario_id}: {fixture_rel}")
        if not grader_path.is_file():
            fail(f"delivery grader is missing for {scenario_id}: {grader_rel}")
        compile(
            grader_path.read_text(encoding="utf-8"),
            str(grader_path),
            "exec",
        )

    repetitions = delivery.get("default_repetitions")
    if (
        not isinstance(repetitions, int)
        or isinstance(repetitions, bool)
        or repetitions < 1
    ):
        fail("delivery benchmark default_repetitions must be a positive integer")

    portable_delivery = ROOT / "skills" / "vibe-coding-skill" / "evals" / "delivery"
    if portable_delivery.exists():
        fail(
            "hidden delivery benchmark scenarios/graders must not be packaged "
            "inside the portable Skill"
        )

    toolchain_config = ROOT / "config" / "toolchain.json"
    if not toolchain_config.exists():
        fail("config/toolchain.json is missing")
    try:
        toolchain = json.loads(toolchain_config.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid toolchain JSON: {exc}")
    if toolchain.get("schema_version") != 2:
        fail("toolchain schema_version must be 2")
    for tool_name in ("graphify", "trivy"):
        entry = toolchain.get(tool_name)
        if not isinstance(entry, dict):
            fail(f"missing toolchain entry: {tool_name}")
        if entry.get("channel") != "stable":
            fail(f"{tool_name} toolchain channel must be stable")
        if entry.get("resolution") != "latest-compatible-stable":
            fail(f"{tool_name} toolchain resolution must be latest-compatible-stable")
        if not entry.get("last_known_good"):
            fail(f"{tool_name} toolchain last_known_good is missing")
        if "approved" in entry or "latest_seen" in entry:
            fail(f"{tool_name} toolchain must not use approved/latest_seen operating pins")

    routing_config = ROOT / "config" / "context-routing.json"
    if not routing_config.exists():
        fail("config/context-routing.json is missing")
    try:
        routing = json.loads(routing_config.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid context routing JSON: {exc}")
    if routing.get("schema_version") != 1:
        fail("context routing schema_version must be 1")
    packs = routing.get("packs")
    if not isinstance(packs, dict) or not packs:
        fail("context routing must define capability packs")
    for pack_name, pack in packs.items():
        if not isinstance(pack, dict) or not pack.get("path"):
            fail(f"invalid capability pack config: {pack_name}")
        pack_path = ROOT / str(pack["path"])
        if not pack_path.exists():
            fail(f"missing capability pack: {pack['path']}")
        activation_requires = pack.get("activation_requires", [])
        if not isinstance(activation_requires, list):
            fail(f"{pack_name} activation_requires must be an array")
        for required_pack in activation_requires:
            if (
                not isinstance(required_pack, str)
                or not required_pack.strip()
                or required_pack not in packs
            ):
                fail(
                    f"{pack_name} has invalid activation requirement: "
                    f"{required_pack!r}"
                )

    pack_reference_pattern = re.compile(r"references/([A-Za-z0-9_.-]+\.md)")
    for pack_file in sorted((ROOT / "packs").glob("*.md")):
        pack_text = pack_file.read_text(encoding="utf-8")
        for ref_name in pack_reference_pattern.findall(pack_text):
            ref_path = ROOT / "references" / ref_name
            if not ref_path.exists():
                fail(
                    f"{pack_file.relative_to(ROOT)} references missing file: "
                    f"references/{ref_name}"
                )

    reference_sources = [SKILL, *sorted((ROOT / "packs").glob("*.md"))]
    reference_sources.extend(sorted((ROOT / "references").glob("*.md")))
    reference_text = {
        path: path.read_text(encoding="utf-8")
        for path in reference_sources
        if path.exists()
    }
    for ref_path in sorted((ROOT / "references").glob("*.md")):
        token = f"references/{ref_path.name}"
        incoming = [
            source
            for source, source_text in reference_text.items()
            if source != ref_path and token in source_text
        ]
        if not incoming:
            fail(
                "orphan reference is unreachable from SKILL, packs, or other "
                f"references: references/{ref_path.name}"
            )

    agents_config = json.loads(benchmark_agents.read_text(encoding="utf-8"))
    if set((agents_config.get("agents") or {}).keys()) != {"codex", "claude-code"}:
        fail("config/agent-benchmarks.json must define codex and claude-code adapters")

    workflow = ROOT / ".github" / "workflows" / "agent-benchmark.yml"
    if not workflow.exists():
        fail("missing .github/workflows/agent-benchmark.yml")

    delivery_workflow = (
        ROOT / ".github" / "workflows" / "real-delivery-benchmark.yml"
    )
    if not delivery_workflow.exists():
        fail("missing .github/workflows/real-delivery-benchmark.yml")
    delivery_workflow_text = delivery_workflow.read_text(encoding="utf-8")
    for token in (
        "workflow_dispatch:",
        "run_delivery_benchmark.py",
        "benchmark_delivery_outputs.py",
        "vibe-real-delivery-benchmark-",
    ):
        if token not in delivery_workflow_text:
            fail(
                "real delivery benchmark workflow is missing expected token: "
                + token
            )

    real_world = ROOT / "validation" / "real-world-projects.json"
    if not real_world.exists():
        fail("validation/real-world-projects.json is missing")
    try:
        catalog = json.loads(real_world.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"real-world validation catalog is invalid JSON: {exc}")
    if not catalog.get("projects"):
        fail("real-world validation catalog has no projects")

    for script in REQUIRED_SCRIPTS:
        path = ROOT / "scripts" / script
        if not path.exists():
            fail(f"missing script: scripts/{script}")
        compile(path.read_text(encoding="utf-8"), str(path), "exec")

    print("Vibe Coding Skill validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
