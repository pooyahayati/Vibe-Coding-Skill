# Recovery and Resume

## Goal

A new agent must be able to continue the project without relying on chat history.

Repository state is primary evidence. Local Vibe state is supplemental and disposable.

## Resume context

Build a bounded recovery packet:

    python scripts/resume_context.py --root . --write-local --json

The packet reads durable project documents in this order:

STATUS -> PROJECT -> ROADMAP -> ARCHITECTURE -> PROJECT_GRAPH -> AGENTS -> README -> Git/GitHub -> source/tests

It also records Git HEAD/branch/dirty state, recent commits, manifests, local graph freshness, and valid local project state.

Document content is size-bounded so one oversized file cannot dominate agent context.

The command is offline by default. It does not fetch GitHub, registries, or external services.

## Missing local state

Missing local state is not a blocker.

The agent should recover from repository documents, Git history, source, tests, manifests, and explicit user decisions.

Do not fabricate local state from remembered chat content.

## Corrupt local state

Inspect:

    python scripts/state_recovery.py inspect --root . --json

Plan repair:

    python scripts/state_recovery.py repair --root . --json

Apply repair explicitly:

    python scripts/state_recovery.py repair --root . --apply --json

Corrupt state is quarantined under the local workspace. project-state.json can be regenerated from current repository evidence.

The tool does not fabricate project.json or traceability.json; those require verified project/GitHub facts.

Removing corrupt graph state intentionally forces a graph refresh before authoritative graph use.

## Recovery test

A recovery flow is successful when a fresh agent can determine:

- current objective or where to find it;
- repository HEAD/branch and uncommitted work;
- relevant architecture/project documents;
- current graph freshness;
- project manifests/runtime shape;
- next evidence sources to inspect.

Chat history must not be required.
