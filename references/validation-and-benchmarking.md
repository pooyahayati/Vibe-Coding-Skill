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

The catalog in `validation/real-world-projects.json` pins public repositories to exact commits. The runner verifies local workspace/repository purity plus real Context Router and Execution Plan behavior, including project complexity, task scope/risk, capability-pack selectivity, context-reduction metrics, project-intelligence preservation, integration points, and whether planning is actually required.

This is a compatibility/routing layer, not a claim that a coding agent successfully implemented a feature in those projects.

## Failure injection

Run:

```bash
python scripts/run_failure_injections.py
```

The suite deliberately injects prompt-injection language, a nonexistent package, a known-vulnerability signal, a stale graph, and a false Done claim with no evidence.

A new safety mechanism should normally receive at least one failure-injection case.

## Completion evidence gate

A meaningful task reported as Done uses completion-report schema version 2. The report must explicitly connect acceptance criteria to the evidence that supports them.

```bash
python scripts/completion_gate.py report.json --json
```

Each acceptance criterion must include:

- a stable `id`;
- a human-readable `description`;
- boolean `required`;
- boolean `met`;
- one or more `evidence_ids`.

Each evidence item must include:

- a stable `id`;
- `kind`;
- `result`;
- boolean `required`;
- risk-appropriate provenance when it is counted toward completion.

A failed or not-run required evidence item blocks Done even when other checks pass. A failed optional item requires an explicit justification. Unrelated passing evidence does not satisfy a criterion unless that criterion links to it.

Example Tier 1 report:

```json
{
  "schema_version": 2,
  "status": "Done",
  "risk_tier": 1,
  "acceptance_criteria": [
    {
      "id": "AC-1",
      "description": "The requested behavior works for the supported path.",
      "required": true,
      "met": true,
      "evidence_ids": ["E-1"]
    }
  ],
  "evidence": [
    {
      "id": "E-1",
      "kind": "test",
      "result": "pass",
      "required": true,
      "provenance": {
        "source": "local",
        "reference": "python -m unittest"
      }
    }
  ],
  "blockers": []
}
```

Provenance requirements scale with risk:

- Tier 0: provenance metadata is optional.
- Tier 1: counted evidence needs `source` and `reference`.
- Tier 2: the report declares the target `commit`; at least two distinct passing semantic evidence families carry `source`, `reference`, and that exact `commit`.
- Tier 3: Tier 2 revision binding plus timezone-aware ISO-8601 `captured_at` on every counted item.

The gate validates structure, required failures, linkage, and provenance. It does not infer whether a test semantically proves a product requirement; evidence selection still requires engineering judgment.

## Release readiness

Use the deterministic release gate with evidence tied to the target commit:

```bash
python scripts/release_readiness.py readiness.json --channel <beta|rc|stable> --json
```

Channels are evidence classes:

- `beta`: requires a successful `Validate Skill` run for the target commit.
- `rc`: requires the complete baseline on the target commit: `Validate Skill`, `Cross Platform Smoke`, `Real World Repository Validation`, `Agent Skills Spec Compatibility`, `Tool Contract Tests`, and `WordPress Artifact Contract`.
- `stable`: requires the same baseline plus a complete, fully conformant real-agent aggregate for both `codex` and `claude-code`.

Stable benchmark evidence must match the current Skill version and the exact portable Skill tree, eval catalog, and agent-output schema hashes. The aggregate's scenario ID list and each Agent's expected/completed/passed scenario counts must exactly match the current eval catalog. Release checks use the latest result for each required workflow on the target commit, and stable qualification considers the latest Real Agent Benchmark run rather than falling back to an older success. Completion of the Real Agent Benchmark itself re-triggers release evaluation, so a valid benchmark produced after the base CI checks can unlock a stable release without re-running those checks. Missing, incomplete, stale, superseded-by-failure, or non-conformant evidence blocks readiness.

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

## Real delivery benchmark

The behavior benchmark above measures whether an Agent selects the expected risk/process contract. It intentionally does not prove that the Agent can implement a correct product change.

The Real Delivery Benchmark is a separate evidence layer for implementation efficacy. Its Phase 9A contract lives in:

- `evals/delivery/scenarios.json`;
- `evals/delivery-result.schema.json`;
- `scripts/run_delivery_benchmark.py`;
- `scripts/benchmark_delivery_outputs.py`.

The experimental unit is `Agent × scenario × arm × repetition`. Each scenario has two arms:

- `control`: the Agent receives the same visible fixture/task without the Vibe Coding Skill;
- `treatment`: the Agent receives the same visible fixture/task with the portable Skill installed.

Compare the Skill against the same Agent, not one Agent against another. Delivery success is a hard correctness signal from required hidden-grader checks; duration, changed-file count, dependency-file changes, and provider usage/cost are observational metrics.

The visible fixture and hidden grader are separate roots. Hidden graders are maintainer-only benchmark assets and MUST NOT be copied into the temporary Agent workspace or packaged inside the portable Skill. The runner records fixture/grader/catalog/schema/Skill hashes, baseline commit, final tree hash, diff hash, changed paths, and raw executor/grader output. Missing runs are missing evidence, never success.

Phase 9A deliberately has no real Codex/Claude delivery adapter and consumes no provider credentials. It provides deterministic contract validation and a fake-executor self-test:

```bash
python scripts/run_delivery_benchmark.py validate --json
python scripts/run_delivery_benchmark.py self-test --json
```

Phase 9B provides five representative product fixtures/graders: tiny local change, brownfield bug regression, contained feature, mixed-monorepo locality, and WordPress installable artifact. Every grader is deterministically proven to reject its broken baseline and accept a known-good implementation. Graders execute against a snapshot copy of the Agent workspace so grader-side build artifacts cannot contaminate captured final-tree/diff evidence.

Real Codex/Claude workspace-write adapters, OS/network sandbox enforcement, and credentialed repetitions belong to Phase 9C. Do not describe Phase 9A or 9B as real-Agent delivery evidence.

Aggregate completed delivery runs with:

```bash
python scripts/benchmark_delivery_outputs.py RESULTS_DIR \
  --catalog evals/delivery/scenarios.json \
  --required-agent codex \
  --required-agent claude-code \
  --require-complete \
  --json
```

The aggregate reports `improved`, `neutral`, `regressed`, or `incomplete` per Agent/scenario based on treatment-vs-control delivery success rate. Correctness is primary; efficiency metrics do not override failed required checks.

Real Delivery Benchmark evidence is not yet part of the release-readiness gate. A future stable-gate change requires complete Phase 9B/9C evidence and must be made explicitly rather than inferred from deterministic self-tests.

## Interpretation

A deterministic validation PASS means the policy mechanisms behaved as specified. It does not prove that every coding agent will follow the skill or deliver a correct implementation. Live behavior-benchmark and real-delivery results are separate evidence classes.
