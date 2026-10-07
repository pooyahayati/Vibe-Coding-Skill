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

Freshness binds graph evidence to the Git HEAD and working-tree fingerprint captured before generation, the exact source-file snapshot processed, and the stored graph bytes. Check the live inputs and copied inputs before and after provider execution; reject a changed or incompletely copied snapshot without publishing it or replacing the previous graph. Provider failure also keeps prior evidence. Retry only after the source stabilizes; no automatic retry loop or synthetic freshness follows.

Local graph-state schema 3 retains `source_snapshot_sha256` and `graph_sha256`. Older cache metadata lacks proof of the processed snapshot and is reported stale until refreshed; it is not silently promoted. This is a disposable graph-cache migration, not a task-contract/receipt migration. A successful refresh still reports current freshness independently; later source/output changes invalidate authoritative graph use. Links escaping the snapshot, directory/dangling links and links the host cannot copy fail explicitly instead of being silently omitted.

Graph state is local:

`~/.vibe-coding/projects/<id>/state/graph-state.json`

## Fallback

If Graphify is unavailable or incompatible:

`Repository search -> manifests/config -> source -> tests -> schemas/migrations -> runtime evidence`

Do not block Tier 0/1 work merely because a graph provider is unavailable. For Tier 2/3, record degraded graph mode and perform explicit fallback impact analysis.
