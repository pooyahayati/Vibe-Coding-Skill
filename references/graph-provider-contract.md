# Graph Provider Contract

## Purpose

The Vibe Coding Skill depends on a project-intelligence graph capability, not on Graphify internals.

Runtime contract:

```text
status
refresh
query
path
explain
freshness
```

Default provider: Graphify.

## Local-only architecture

Graph generation runs against a shadow copy under the project's local Vibe workspace. The user project working tree is not used as Graphify's output directory.

```text
Project working tree
        |
        +-- tracked + relevant untracked source snapshot
        v
~/.vibe-coding/projects/<id>/worktrees/graph-shadow/
        |
        v
Graphify
        |
        v
~/.vibe-coding/projects/<id>/graph/graphify-out/
```

This preserves uncommitted source changes in graph analysis while keeping Graphify output outside the project repository.

## Commands

Status:

```bash
python scripts/graph_provider.py status --root . --json
```

Refresh:

```bash
python scripts/graph_provider.py refresh --root . --mode auto --json
```

`auto` uses incremental update when prior provider output is available and otherwise performs a full code-only extraction.

Query:

```bash
python scripts/graph_provider.py query "What is affected by changing authentication?" --root .
```

Path:

```bash
python scripts/graph_provider.py path AuthService UserRepository --root .
```

Explain:

```bash
python scripts/graph_provider.py explain AuthService --root .
```

Query/path/explain refuse stale graphs by default. `--allow-stale` is explicit degraded mode and should not be used as authoritative evidence for high-risk work.

## Freshness

Freshness binds graph evidence to current Git HEAD plus a working-tree fingerprint containing tracked modifications and untracked non-ignored source files.

Graph state is local:

`~/.vibe-coding/projects/<id>/state/graph-state.json`

## Fallback

If Graphify is unavailable or incompatible:

`Repository search -> manifests/config -> source -> tests -> schemas/migrations -> runtime evidence`

Do not block Tier 0/1 work merely because a graph provider is unavailable. For Tier 2/3, record degraded graph mode and perform explicit fallback impact analysis.
