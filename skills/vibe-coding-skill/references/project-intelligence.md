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

Use the provider contract rather than calling Graphify directly:

- `python scripts/graph_provider.py query "<question>" --root .`
- `python scripts/graph_provider.py path "<A>" "<B>" --root .`
- `python scripts/graph_provider.py explain "<concept>" --root .`

Then verify important conclusions in source.

Reason through:

`Change → Affected Component → Dependencies → Data/API → Test Impact → Deployment Impact`

## Post-change update

After significant integration, update the graph, check freshness, reassess tests, and update `PROJECT_GRAPH.md` only when high-level architecture changed.

Typical command:

`python scripts/graph_provider.py refresh --root . --mode auto --json`

The adapter refreshes Graphify in a shadow copy under the local Vibe workspace and keeps provider output outside the project repository.

## Graph state

Graph provider state is local-only and must not be committed to the project repository.

Default state location:

`~/.vibe-coding/projects/<project-id>/state/graph-state.json`

Example:

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

Graphify-generated `graphify-out/` is also local-only. Prefer an external output location when supported; otherwise keep the working-tree output untracked through `.git/info/exclude`.

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

## Repository purity

Machine graph outputs are engineering artifacts, not source. Do not commit them. See `references/local-workspace-and-repository-purity.md`.

## Provider boundary

The stable runtime contract is documented in `references/graph-provider-contract.md`. Other skill components should depend on that contract rather than Graphify-specific paths or command details.
