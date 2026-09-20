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

A meaningful task reported as Done should provide an explicit risk tier, acceptance criteria, and passing evidence.

```bash
python scripts/completion_gate.py report.json --json
```

The gate does not try to infer whether a particular test semantically proves the whole change. It enforces increasingly traceable evidence as risk rises:

- Tier 0: at least one passing evidence item; provenance metadata is optional.
- Tier 1: at least one passing item with `source` and `reference`.
- Tier 2: the report must declare the target `commit`; at least two passing evidence kinds must each carry `source`, `reference`, and that exact same `commit`.
- Tier 3: the Tier 2 revision binding remains mandatory and each counted item also needs a timezone-aware ISO-8601 `captured_at` timestamp.

Example Tier 2 evidence item:

```json
{
  "kind": "test",
  "result": "pass",
  "provenance": {
    "source": "ci",
    "reference": "validate-skill/run-123",
    "commit": "abc1234"
  }
}
```

Passing evidence that lacks the provenance required by the current tier, points at a different revision, or uses an ambiguous Tier 3 timestamp is not counted toward completion. Acceptance criteria must be structured objects with a boolean `met` value. Missing or malformed evidence is missing evidence, not success.

## Release readiness

Use the deterministic release gate with evidence tied to the target commit:

```bash
python scripts/release_readiness.py readiness.json --channel <beta|rc|stable> --json
```

Channels are evidence classes:

- `beta`: requires a successful `Validate Skill` run for the target commit.
- `rc`: requires both `Validate Skill` and `Cross Platform Smoke` for the target commit.
- `stable`: requires RC evidence plus a complete, fully conformant real-agent aggregate for both `codex` and `claude-code`.

Stable benchmark evidence must match the current Skill version and the exact portable Skill tree, eval catalog, and agent-output schema hashes. Release checks use the latest result for each required workflow on the target commit, and stable qualification considers the latest Real Agent Benchmark run rather than falling back to an older success. Missing, incomplete, stale, superseded-by-failure, or non-conformant evidence blocks readiness.

Repository branch protection is not part of this gate.

## Agent benchmark

Real agent outputs are scored separately from deterministic policy tests.

The strict output schema is `evals/agent-output.schema.json`; human guidance is in `evals/AGENT_OUTPUT_SCHEMA.md`.

Use `scripts/run_agent_benchmark.py` for blind Codex/Claude Code execution. The runner installs the Skill only inside a temporary benchmark Git repository, requests structured output from the real CLI, and records provenance/integrity metadata plus raw stdout/stderr outside the repository.

Preflight:

```bash
python scripts/run_agent_benchmark.py preflight --agent codex --require-env-auth --json
python scripts/run_agent_benchmark.py preflight --agent claude-code --require-env-auth --json
```

Complete evidence:

```bash
python scripts/benchmark_agent_outputs.py RESULTS_DIR \
  --required-agent codex \
  --required-agent claude-code \
  --require-complete \
  --json
```

A conformance rate is reported only when the expected scenario set is complete for that Agent.

Benchmark completeness also requires a valid runner envelope: the envelope Agent must match its result directory, the envelope and contract scenario IDs must agree, and Skill version plus Skill-tree/catalog/schema identity hashes and Agent version must be present consistently. Raw contracts without that provenance cannot become complete benchmark evidence.

An unexpected internal runner exception is recorded as failing raw evidence for that scenario and does not stop later selected scenarios from being attempted.

Benchmark tier assessment distinguishes four outcomes: `preferred`, `conservative_escalation`, `underclassified`, and `overengineered`. Conservative escalation is allowed only when the hidden scenario policy explicitly defines a higher acceptable ceiling; it does not relax required controls, approval semantics, forbidden-action handling, or integrity checks. Aggregation reports the assessment counts so systematic over-engineering is visible instead of being merged into a generic tier mismatch.

The manual GitHub Actions workflow `.github/workflows/agent-benchmark.yml` requires real provider credentials and uploads raw benchmark evidence as an Actions artifact. It is deliberately not an automatic PR workflow because it consumes provider usage.

Do not commit benchmark output to the project repository.

Do not publish or compare a Codex/Claude result unless that agent actually produced the stored raw contract under the stated Skill version. Missing runs are missing evidence, never success.

## Interpretation

A deterministic validation PASS means the policy mechanisms behaved as specified. It does not prove that every coding agent will follow the skill. Live-agent benchmark results are a separate evidence class.
