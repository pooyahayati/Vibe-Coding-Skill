# Recovery and Resume

## Goal

A new agent must be able to continue the project without relying on chat history.

Repository state is primary product evidence. Local caches are disposable; accepted task contracts, specialist commitments and evidence ledgers are retained obligations and must be restored or explicitly reconstructed before continuing.

## Resume context

Build a bounded recovery packet:

    python scripts/resume_context.py --root . --write-local --json

The packet reads durable project documents in this order:

STATUS -> PROJECT -> ROADMAP -> ARCHITECTURE -> PROJECT_GRAPH -> AGENTS -> README -> Git/GitHub -> source/tests

It also records Git HEAD/branch/dirty state, recent commits, manifests, local graph freshness, and valid local project state.

Document content is size-bounded so one oversized file cannot dominate agent context.

The command is offline by default. It does not fetch GitHub, registries, or external services.

## Missing local state

Never-initialized local state and missing optional caches do not block a lightweight task. A missing primary task snapshot with a retained copy, an interrupted write or a pending recovery marker requires repair. Losing the entire workspace cannot be detected from that workspace alone: reconstruct approved obligations from independent project evidence before resuming known structured work.

The agent should recover from repository documents, Git history, source, tests, manifests, and explicit user decisions.

Do not fabricate local state from remembered chat content.

## Corrupt local state

Inspect:

    python scripts/state_recovery.py inspect --root . --json

Plan repair:

    python scripts/state_recovery.py repair --root . --json

Apply repair explicitly:

    python scripts/state_recovery.py repair --root . --apply --json

Corrupt state is quarantined under the local workspace. Repair restores a validated `project-state-retained.json` to `project-state.json`, preserving the task contract, risk floor, workflow and revision history. Writes use atomic replacement; an interrupted capture is detected before resume/capture can replace obligations. Repair success establishes restored state, not current completion: resume independently rechecks receipts.

When neither snapshot is valid, repair returns `BLOCK` (exit 2) and leaves a recovery marker. Verify the approved contract against durable requirements and existing specialist/evidence history, then explicitly reconstruct it:

```bash
python scripts/project_state.py capture --root <project> \
  --task-contract <verified-contract.json> --reconcile-recovery "<evidence-based reconstruction reason>" --json
```

This records a Head decision, not new authorization. Preserve the known task ID, required findings, scope, risk and evidence obligations; do not invent an empty contract. Reconstruction uses schema 3 and does not restore a success claim. Existing specialist records remain subject to independent acceptance. Without independently verifiable obligations, report the missing context and stop the dependent work.

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
