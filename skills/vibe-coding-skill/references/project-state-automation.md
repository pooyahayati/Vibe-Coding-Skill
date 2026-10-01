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

`--completion-report <report.json>` optionally imports schema-2 declared results. They are labeled `reported-met`, `unmet` or `unverified`; `execution_verified` stays false. Required failures remain visible and return exit code 2. Changes to the stored report's HEAD/working-tree/contract context make its outcomes unverified across subsequent captures and resume rendering. This conservative B2 guard is not E2's future scoped-input/artifact receipt verification and does not force automatic reruns.

Supplying a changed required outcome or protected behavior for the same task fails before overwriting the snapshot. For an already authorized, Head-reconciled material change, `--task-contract <replacement.json> --accept-contract-change "<reason>"` retains the previous contract/digest in the reconciliation record and invalidates old result binding. It cannot lower the known risk floor. For a different current task, use an explicit contract with a different `task_id` and `--new-task`; it clears prior task results/operating notes. These options record a caller decision, not permission or authenticated user approval. Protect independent baselines using host/writer controls.

Unreadable state or altered contract fingerprints require repair before replacement. Product requirements remain legitimate Git documents; operational snapshots stay in the existing local workspace. See [shared formats and trust limits](shared-improvement-contracts.md).

## Repository updates

Do not mechanically rewrite project documents after every command or commit.

Update durable Git documents only when semantic content changed: objective, architecture, milestone/status, blockers/risks, setup, deployment, or other handoff-relevant facts.

Operational timestamps, graph paths, scanner paths, and transient agent state stay local.

## Resume integration

For a fresh agent or after context loss, use `python scripts/resume_context.py --root . --write-local --json`. If local state is unreadable, inspect and repair it with `scripts/state_recovery.py` before trusting it. Repository evidence remains authoritative.
