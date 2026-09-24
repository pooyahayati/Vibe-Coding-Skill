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
    if len(body.splitlines()) > 500:
        fail("SKILL.md exceeds recommended 500 lines")
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

    agents_config = json.loads(benchmark_agents.read_text(encoding="utf-8"))
    if set((agents_config.get("agents") or {}).keys()) != {"codex", "claude-code"}:
        fail("config/agent-benchmarks.json must define codex and claude-code adapters")

    workflow = ROOT / ".github" / "workflows" / "agent-benchmark.yml"
    if not workflow.exists():
        fail("missing .github/workflows/agent-benchmark.yml")

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
