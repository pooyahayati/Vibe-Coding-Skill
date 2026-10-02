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

Choose the supported route from retained task context, not a report's success flags:

| Route | What the gate establishes | Limits |
|---|---|---|
| New structured task: schema 3 | Retained criteria/obligations, qualifying local command/manual receipts, scoped input/artifact freshness and required specialist acceptance. | Head review still determines whether the checks prove the behavior. |
| In-flight legacy task: schema 2 | Declared criterion/evidence linkage, required failures and risk-appropriate provenance. | A PASS is declared evidence, never receipt-verified execution. |
| Tiny/manual work | A concrete relevant observation can satisfy an accepted manual obligation; no forced command or automated test. | An observation must actually have occurred; it cannot replace a required collected check. |

For a new structured task:

```bash
python scripts/completion_gate.py report.json --task-contract task.json --root /path/to/project --json
```

For an existing schema-2 task, the supported command remains `python scripts/completion_gate.py report.json --json`. Migration first reconciles retained criteria and obligations; it cannot turn old claims into receipts or downgrade an activated receipt workflow.

Failed, missing, stale or unavailable required evidence blocks Done; unrelated passing checks cannot cancel it. Local receipt checks do not resolve arbitrary remote CI claims or protect against an actor able to edit both source and records. Use the canonical [collection, manual observation and migration guidance](execution-and-verification.md#receipt-backed-completion-e2) and [format/trust contract](shared-improvement-contracts.md) rather than copying schemas here.

## Portable workflow integration (I1)

```bash
python -m unittest discover -s tests -p test_portable_integration.py
```

These three maintainer routes build/extract the current-source ZIP and use its installed entrypoints outside the source checkout: light legacy handoff/resume, actual failed/passing local receipts with scoped freshness, and a cross-boundary specialist return requiring separate Head acceptance. The existing Linux/macOS/Windows matrix runs them; offline specialist fixtures do not establish live upstream currency.

This is extracted-package/tooling evidence, not a public release, model evaluation or proof of every application's behavior. Run it for affected integration/packaging changes or existing required CI, not for every product task. [Route details and limits](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/main/docs/i1-integration-verification.md).

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
