# Project State and Traceability

## Repository as persistent memory

Conversation history is not the project database. Prefer durable state in the repository and Git/GitHub.

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
