# Project State Automation

## Purpose

Automate operational state capture without generating noisy repository commits.

Stable project knowledge may live in Git: PROJECT.md, STATUS.md, ARCHITECTURE.md, PROJECT_GRAPH.md, ROADMAP.md, AGENTS.md, and README.md. Machine/session state remains local.

## Capture

```bash
python scripts/project_state.py capture --root . --json
```

Captures branch, HEAD, origin, dirty state, working-tree fingerprint, graph provider status/freshness, GitHub adapter status, durable-document hashes/presence, and current objective from local bootstrap state when available.

State is written to:

`~/.vibe-coding/projects/<id>/state/project-state.json`

## Drift

```bash
python scripts/project_state.py drift --root . --json
```

Reports differences from the last local snapshot without writing to the repository.

## Handoff

```bash
python scripts/project_state.py handoff --root . --write-local
```

Produces a concise local handoff snapshot and preserves the resume order:

`STATUS -> PROJECT -> ROADMAP -> ARCHITECTURE -> PROJECT_GRAPH -> AGENTS -> GitHub -> source/tests`

### Preserve task behavior and useful delivery details (B2)

For the optional structured route, capture an accepted task contract once; later capture/drift/handoff commands reuse it without needing the original input path:

```bash
python scripts/project_state.py capture --root <project> --task-contract <accepted-contract.json> --json
python scripts/project_state.py handoff --root <project> --write-local \
  --how-to-use "<how to start/use the delivered behavior>" \
  --how-to-check "<relevant observable check>" --next-action "<next useful action>"
```

State/handoff retains the task ID, full acceptance/behavior fields, evidence obligations and fingerprint. It lists expected outcomes, what remains unverified, how to use/check the result, limitations and next action. Missing operating details are explicitly not supplied; the tool does not invent launch commands or test success. Use repeated `--limitation` options only for material limits. Tiny tasks can keep the legacy/inline route with no new contract file or written plan.

`--completion-report <report.json>` imports results using the retained workflow. New structured contracts and `--new-task` use schema 3 automatically, without an activation flag. Only an already retained task can keep schema-2 declared results (`reported-met`, `unmet`, `unverified`; never receipt-verified), including older task snapshots without a `completion_schema` field. `--receipt-completion` explicitly migrates such a task; omitting it later cannot downgrade. Supply independent `--delivery-context` when relevant. Missing/stale/failed receipts or schema-2 downgrade cannot qualify. [E2 usage and migration](execution-and-verification.md#receipt-backed-completion-e2). Required failures return exit code 2; no automatic rerun or permission follows.

Supplying a changed required outcome or protected behavior, or removing a retained `specialist_assignment_ids` entry, fails before overwriting the snapshot. This includes unstarted assignments; reordering IDs or adding a commitment does not remove an existing one. For an already authorized, Head-reconciled material change, `--task-contract <replacement.json> --accept-contract-change "<reason>"` retains the previous contract/digest in the reconciliation record and invalidates old result binding. It cannot lower the known risk floor. For a different current task, use an explicit contract with a different `task_id` and `--new-task`; it clears prior task results/operating notes and does not inherit legacy completion. These options record a caller decision, not permission or authenticated user approval. Protect independent baselines using host/writer controls.

Each contract revision retains its previous contract/digest, next digest and Head reason in `contract_revisions`. Existing specialist assignments do not automatically inherit that revision: use the explicit [assignment reconciliation route](specialist-composition.md#contract-revisions) before renewed acceptance.

Snapshots are atomically replaced with a retained recovery copy. Unreadable state, mismatched copies or altered contract fingerprints require [repair or explicit obligation reconstruction](recovery-and-resume.md#corrupt-local-state) before replacement. Product requirements remain legitimate Git documents; operational snapshots stay in the existing local workspace. See [shared formats and trust limits](shared-improvement-contracts.md).

Completion uses the [outcome policy](shared-improvement-contracts.md#outcome-policy-compatibility-t3). Capture/resume re-evaluates required evidence; the policy identifier does not turn old success into new proof. A planning/activity-stage transition alone leaves scoped receipt validity intact. Preserve the contract when only activity changes; new delivery outcomes still require explicit reconciliation and cannot reuse old contract bindings.

### Correcting an incidental risk floor

For an existing structured task whose tier was raised only by incidental words/paths, the Head may supply a replacement contract with a lower `risk_tier` and optional `risk_facts` containing the [reviewed non-runtime assessment](risk-classifier-and-integrations.md#resolving-incidental-signals):

```bash
python scripts/project_state.py capture --root <project> --task-contract <reviewed-contract.json> \
  --reclassify-risk "<why the previous tier was incidental; evidence inspected>" --json
```

This separate route requires a retained contract, nonempty reason and consistent inspected scope. Current routing must also support the proposed tier; missing/incomplete affected inputs block reclassification. Only `risk_tier` and `risk_facts` may change: task identity, scope, acceptance/protected behavior, evidence obligations and specialist commitments must remain identical. It cannot be combined with `--new-task` or `--accept-contract-change`. Known material facts cannot be weakened or removed, including through general contract reconciliation. Legacy integer-only floors have no automated provenance; the Head must inspect the retained requirements and actual edit before declaring them incidental. The helper does not establish the truth of that review or grant permission.

The existing revision ledger retains the prior contract/digest and reason; handoff/resume retain the reviewed facts. The new contract digest invalidates old completion/receipt bindings and follows the existing specialist revision rules. Normal capture/plan/resume still cannot lower a retained tier. Tiny inline work needs no structured contract merely to use the reviewed scope route.

## Repository updates

Do not mechanically rewrite project documents after every command or commit.

Update durable Git documents only when semantic content changed: objective, architecture, milestone/status, blockers/risks, setup, deployment, or other handoff-relevant facts.

Operational timestamps, graph paths, scanner paths, and transient agent state stay local.

## Resume integration

For a fresh agent or after context loss, use `python scripts/resume_context.py --root . --write-local --json`. If local state is unreadable, inspect and repair it with `scripts/state_recovery.py` before trusting it. Repository evidence remains authoritative.
