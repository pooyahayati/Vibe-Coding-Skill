# Project Validation, Failure Injection, and Release Checks

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
- `stable`: requires the same complete baseline on the exact target commit.

For every channel, use the latest result for each required workflow. Missing, stale, failed, or different-commit checks block publication. Provider credentials, model versions, model comparison results, and real-agent benchmark aggregates are not release requirements. Credentialed automatic benchmark workflows have been removed.

Repository branch protection is not part of this gate.

## Deterministic delivery fixtures

Maintainer-only fixtures under `evals/delivery/` test tiny changes, regressions, CSV output, monorepo locality, and installable WordPress artifacts without calling a model. They remain separate from the portable runtime. The WordPress grader executes behavior from the exact ZIP with a trusted PHP harness; real install/upgrade coverage is provided by `WordPress Artifact Contract` CI.

## Release package

`scripts/build_release.py` builds the portable runtime, VERSION, and LICENSE into one installable ZIP, rejects unexpected/symlink paths, verifies the extracted package offline, and writes SHA-256 checksums. Source archives remain available separately on GitHub.

## Interpretation

Passing software tests verifies the documented mechanisms and tested fixtures. It does not establish a model's coding quality or guarantee correct delivery for every project. Independent engineering judgment and task-specific evidence remain necessary.
