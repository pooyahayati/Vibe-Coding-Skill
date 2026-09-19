# Project Intelligence and Graphs

## Goal

Reduce blind repository exploration and improve impact analysis without treating a static graph as complete runtime truth.

## Provider model

Capability: `Project Intelligence Graph`

Default provider: `Graphify`

The skill depends on the capability, not on Graphify internals.

If Graphify is unavailable, fall back to repository search, manifests, tests, config, database/schema inspection, and runtime evidence.

## When graph analysis is expected

Use it for Tier 2/3 changes, unfamiliar repositories, cross-module changes, refactors, public contract changes, or difficult regression analysis.

For Tier 0 work, do not generate a graph merely for ceremony.

## Pre-change analysis

When Graphify is available, use commands such as:

- `graphify query "<question>"`
- `graphify path "<A>" "<B>"`
- `graphify explain "<concept>"`

Then verify important conclusions in source.

Reason through:

`Change → Affected Component → Dependencies → Data/API → Test Impact → Deployment Impact`

## Post-change update

After significant integration, update the graph, check freshness, reassess tests, and update `PROJECT_GRAPH.md` only when high-level architecture changed.

Typical command:

`graphify update .`

## Graph state

A project may record `.vibe/graph-state.json`:

```json
{
  "provider": "graphify",
  "provider_version": "0.9.64",
  "source_commit": "abc123",
  "generated_at": "2026-09-19T00:00:00Z",
  "schema_version": 1
}
```

If `source_commit` differs from current `HEAD`, treat the graph as potentially stale.

## Graphify update policy

Do not blindly install the newest release in production workflows.

Use:

`Latest Stable Available → Compatibility Contract Tests → Approved Latest → Project`

The repository's `config/toolchain.json` tracks the approved version.

The scheduled compatibility workflow tests newly released Graphify versions and proposes a pull request. Merging the PR makes the new version approved.

## Contract expectations

A candidate Graphify release should preserve the workflow required by this skill: version output, code-only extraction, graph JSON generation, and graph query/explain behavior used by the skill.

If a new version breaks the contract, keep the last known good version and surface the incompatibility.

## Truth model

Graph evidence must be combined with source code, manifests, configuration, feature flags, database schema/migrations, tests, runtime logs, and external integrations.

Dynamic imports, reflection, generated code, queues, triggers, environment configuration, and remote systems may not be fully represented in the graph.
