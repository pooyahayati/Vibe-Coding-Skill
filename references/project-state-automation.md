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

## Repository updates

Do not mechanically rewrite project documents after every command or commit.

Update durable Git documents only when semantic content changed: objective, architecture, milestone/status, blockers/risks, setup, deployment, or other handoff-relevant facts.

Operational timestamps, graph paths, scanner paths, and transient agent state stay local.

## Resume integration

For a fresh agent or after context loss, use `python scripts/resume_context.py --root . --write-local --json`. If local state is unreadable, inspect and repair it with `scripts/state_recovery.py` before trusting it. Repository evidence remains authoritative.
