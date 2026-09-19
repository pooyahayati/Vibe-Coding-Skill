# Project State and Traceability

## Repository as persistent project memory

Conversation history is not the project database.

Keep durable **project knowledge** in the repository and Git/GitHub when another developer needs it: requirements, architecture decisions, meaningful status, tests, migrations, setup, and release history.

Keep **tool operational state** outside the repository: graph caches/state, security reports, coverage reports, agent scratch state, benchmarks, and Vibe Coding runtime metadata.

Default local operational state lives under:

`~/.vibe-coding/projects/<project-id>/`

This separation keeps the GitHub repository clean without sacrificing resumability.

## Adaptive documentation

Create only documents that earn their maintenance cost.

### PROJECT.md

Use for stable product context: problem, users, core outcome, requirements, MVP, success criteria, stable constraints.

### STATUS.md

Use for multi-step work or handoff.

Keep it concise: date/version, current objective, completed, in progress, next, blockers, pending decisions, top risks, tests, branch/PR, migration/deployment notes.

Replace stale status; do not append an endless diary.

### ARCHITECTURE.md

Create when architecture has meaningful structure or constraints.

### PROJECT_GRAPH.md

Human-readable high-level dependency/runtime map. Do not duplicate every source import.

### ROADMAP.md

Create when multiple milestones/versions matter.

### AGENTS.md

Create when multiple agents/roles are used or repository-wide agent boundaries matter.

## Traceability

For significant requirements:

`Requirement → Issue/Task → Acceptance Criteria → Implementation/PR → Tests → Release`

Do not invent GitHub objects when GitHub is not used.

## Identifiers

Stable IDs are useful when the project is large enough, for example `REQ-014`.

Do not add identifiers to tiny projects when they add more bookkeeping than value.

## GitHub

When GitHub is available, use Issues for work, PRs for implementation/review, Actions for CI, and Releases for stable delivery.

GitHub is an adapter, not a hard requirement.

## Drift checks

Compare:
- `ARCHITECTURE.md ↔ Code`
- `PROJECT_GRAPH.md ↔ Actual major dependencies`
- `README.md ↔ Runtime/setup`
- `ROADMAP.md ↔ active milestones/issues`
- `STATUS.md ↔ repository reality`

## Handoff

Before handoff verify tests/checks, current branch/PR, objective, blockers/risks, pending decisions, graph freshness when relevant, deployment/migration state, and the next executable step.

## Repository purity

Before commit or push, run `python scripts/repository_purity.py --root . --json`. Tool-generated artifacts must not become tracked project files. See `references/local-workspace-and-repository-purity.md`.
