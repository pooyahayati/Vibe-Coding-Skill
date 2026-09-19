# Real Project Validation, Failure Injection, and Agent Benchmarking

## Purpose

The skill is not considered reliable merely because its instructions read well. It must survive representative projects and deliberate failure conditions.

## Representative project validation

Run:

```bash
python scripts/run_project_validations.py
```

The validation pack covers tiny static changes, brownfield work, authentication, destructive production migration, and third-party payment integration.

Each fixture is initialized as a real temporary Git repository. The runner verifies risk tier, approval requirement, bootstrap profile, integration-gate behavior, and that read-only checks do not mutate the repository.

Fixtures are intentionally small. They test policy behavior, not framework performance.

## Pinned real-world repository validation

Run:

```bash
python scripts/run_real_world_validations.py
```

The catalog in `validation/real-world-projects.json` pins public repositories to exact commits. The runner verifies that local workspace initialization, repository purity, resume context, dry-run bootstrap, and risk classification behave safely on real Python, Node, and Go repository layouts.

This is a compatibility layer, not a claim that a coding agent successfully implemented a feature in those projects.

## Failure injection

Run:

```bash
python scripts/run_failure_injections.py
```

The suite deliberately injects prompt-injection language, a nonexistent package, a known-vulnerability signal, a stale graph, and a false Done claim with no evidence.

A new safety mechanism should normally receive at least one failure-injection case.

## Completion evidence gate

A meaningful task reported as Done should provide explicit acceptance criteria and passing evidence.

```bash
python scripts/completion_gate.py report.json --json
```

This gate prevents unsupported Done claims but does not attempt to judge whether a test itself is sufficient for every risk tier.

## Agent benchmark

Real agent outputs are scored separately from deterministic policy tests.

Use `evals/AGENT_OUTPUT_SCHEMA.md` for each blind run. Store raw outputs in the project's local Vibe Coding workspace, for example `~/.vibe-coding/projects/<project-id>/benchmarks/`, then aggregate that local directory.

Do not commit benchmark output to the project repository.

Do not publish or compare a Codex/Claude result unless that agent actually produced the stored raw contract under the stated skill version.

## Interpretation

A deterministic validation PASS means the policy mechanisms behaved as specified. It does not prove that every coding agent will follow the skill. Live-agent benchmark results are a separate evidence class.
