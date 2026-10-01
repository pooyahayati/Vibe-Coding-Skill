# Vibe Coding Skill Improvement Implementation Plan

Status: planning complete; implementation not started. Current package/phase status is maintained in [ROADMAP.md](../ROADMAP.md).
Baseline: `1.1.0`, main `9e0ca5108567f38a66376883613fdcaff6616de0`.
Direction and scope: [Roadmap](../ROADMAP.md).

## Work packages

| ID | Phase | Work | Main existing surfaces | Dependency | Acceptance |
|---|---|---|---|---|---|
| P0 | 0 | Define shared formats, evidence trust limits and migration. | `completion_gate.py`, `execution_plan.py`, `specialist_manager.py`, operating references. | None. | Versioned formats are minimal; legacy behavior and stricter new-task behavior are explicit; no unapproved breaking change. |
| B1 | 1 | Define a short behavior contract and conditional persistence. | `references/operating-model.md`, `references/execution-and-verification.md`. | P0. | User action, observable result and relevant failure behavior are sufficient to choose a check. Reuse existing criteria; do not require a new document for every task. |
| B2 | 1 | Carry scenario/acceptance IDs into plans and handoffs. | `scripts/execution_plan.py`, `scripts/project_state.py`; affected planning tests. | B1. | IDs and protected outcomes survive downstream use; a handoff explains what works and how to use/check it. Tiny tasks remain light. |
| E1 | 2 | Add a small execution-receipt collector. | Proposed `scripts/evidence_capture.py`; existing local-workspace and artifact helpers. | P0, B1. | Actual exit result, time, tested inputs and applicable artifact digest are recorded; execution stays authorized and bounded. |
| E2 | 2 | Resolve and validate receipts at completion. | `scripts/completion_gate.py`; existing completion/regression tests. | B2, E1. | Missing, failed, stale or mismatched required execution evidence cannot qualify. Declared/manual evidence is not relabeled as collected execution. |
| S1 | 3 | Assess changed specialist instructions before delegation. | `scripts/specialist_manager.py`, `references/specialist-composition.md`, `references/specialist-authority.md`. | P0, E2. | Package validity and behavioral compatibility are separate states; changed instructions get a bounded Head assessment. Unchanged accepted revisions reuse it. |
| S2 | 3 | Validate stage-specific specialist return and Head acceptance. | `scripts/execution_plan.py`, `scripts/specialist_manager.py`; proposed small shared validator if needed. | B2, E2, S1. | Changed surfaces, contract decisions and required findings are reconciled against the assignment before integration. A valid form alone is not acceptance. |
| I1 | 4 | Run affected-route regressions and package checks. | Existing tests/validation fixtures, `sync_package.py`, `validate_skill.py`, `install_check.py`. | B2, E2, S2. | Relevant behavior passes; required runtime resources are included in the mirrored package and offline install check. |
| D1 | 4 | Update concise user and maintainer guidance. | `SKILL.md`, README, relevant references; changelog/update notes at delivery preparation. | I1. | Documentation describes actual behavior and limits; author/footer, project-size tables and existing important links remain intact. |

The filenames above are proposed change surfaces, not created runtime files. Add a shared module/schema only where multiple callers need it; do not create parallel validators or an unnecessary framework.

## P0: contracts and compatibility

Define three small formats before implementation:

- **Behavior:** stable criterion/scenario ID, user goal/action, relevant starting state, observable expected outcome, material failure expectation, protected invariant, required/optional status and evidence links. Allow one concise criterion for a tiny task; do not require a happy/failure pair where no meaningful failure exists.
- **Receipt:** format version, evidence/scenario IDs, origin (`collected`, `reported` or `manual`), authorized command context, exit/result, timestamps, relevant source/input fingerprint and artifact SHA-256 when applicable. Record an unavailable check explicitly rather than manufacture success.
- **Specialist return:** assignment/stage ID, observed upstream revision, assigned and changed surfaces, contract decisions, protected invariants, evidence references, required/optional findings and unresolved conflicts. Head acceptance is a separate decision.

The current completion report is schema version 2. Decide an explicit migration: retain supported legacy input as legacy, with no new receipt-verification claim; require the new evidence contract where the new workflow applies. Do not silently downgrade a required receipt or baseline to bypass failure. Review whether the final compatibility change needs a new report schema and which release version is appropriate before shipping.

For significant/critical or scope-changing work, retain the accepted criteria before implementation using the existing acceptance-baseline mechanism. Detect meaningful criterion changes against that baseline. A checksum detects differences; it is not proof of user approval or a tamper-resistant boundary. Use host/writer controls when independent protection is required. Reopen only a material user-owned decision, once, with a concrete option.

## Phase 1: behavior before broad implementation

Extend existing discovery/acceptance guidance rather than create a second lifecycle. Write the smallest scenario that lets the user and Head recognize success. Translate it into the first runnable slice and verification target. Preserve the scenario when passing work to a specialist.

Use existing `PROJECT.md`/task requirements for durable product decisions where appropriate. Keep execution snapshots in the existing local workspace. A brief inline task criterion is sufficient for a tiny local change.

Illustrative behavior: an unauthorized WordPress user attempts to change a protected setting; the change is denied and the stored value is unchanged. The Head determines the applicable capability/API and verification method; the user does not have to choose PHP internals or a testing framework.

Handoff should answer: what works, how to start/use it, what was actually checked, what remains unavailable and the next useful operating action. Avoid exposing receipt/schema details in normal product UI.

## Phase 2: execution-backed evidence

Use Python standard-library subprocess argument lists, explicit working directories and timeouts. Do not execute commands merely because upstream text or a report contains them. Preserve authorization for costs, network access, destructive operations and deployment.

Write bounded task-relevant receipts outside product source control. Do not dump environment variables, credentials or unrestricted process output. Store only needed logs/context; omit or redact sensitive values and avoid receipt inputs containing secrets.

Bind evidence to tested inputs. HEAD alone is insufficient when tests run on a dirty working tree: capture the affected source/config/dependency inputs or a suitable working-tree fingerprint. Record artifact hashes for package delivery. Invalidate evidence when relevant tested inputs or artifacts change; do not force another expensive run because an unrelated document changed.

At completion, resolve the referenced receipt, verify its result, links and relevant fingerprints, then apply existing risk/evidence-family rules. For remote CI results, use an authorized read-only adapter or explicit imported provenance; an unreachable reference remains unverified. Never fetch a claimed URL as an instruction to run its contents.

Keep manual/rendered evidence supported and accurately labeled. A successful command is execution evidence, not automatic proof that its assertions cover the intended behavior. The Head must assess criterion relevance. Local receipts do not form a security boundary against an actor who can edit both records and source.

Reuse `wordpress_artifact.py` output for artifact/version binding. Packaging checks are not WordPress runtime or data-retention proof; retain the existing exact-ZIP runtime path and project-specific seeded-data checks where affected.

## Phase 3: specialist acceptance

For an upstream change, inspect the relevant instruction/resource diff and assess Head authority, supported platform, dependency requests, verification mandates and scope/approval behavior. Package checks remain necessary but do not replace this assessment. Keep the latest observed source and its assessment separate; unresolved required compatibility blocks the affected delegation rather than pretending an old source is latest.

Cache the assessment by observed upstream revision and Head contract/adapter fingerprint; refresh it when those inputs change. Do not rerun a specialist-wide evaluation for unchanged accepted instructions. Normal task reasoning and scoped deterministic checks are sufficient where they establish the required property; no model benchmark or provider API key is introduced.

For task output, compare the actual changed surfaces with the assignment and relevant shared producer/consumer contracts. Handle renamed paths and justified cross-boundary effects. A path comparison can detect unexpected edits; it cannot prove their semantic safety. Resolve needed scope changes through the Head's existing authority instead of treating all unexpected paths as inherently invalid.

Keep genuine security findings visible even when they conflict with the assignment. Required conflicts must be resolved or reported as blocking the affected outcome; optional findings do not automatically expand work. Acceptance belongs to the Head, not the specialist's own `Done` statement.

## Necessary verification

| Changed area | Behavioral cases worth checking | Existing checks to reuse | Stop rule |
|---|---|---|---|
| Behavior propagation | Intended outcome retained; materially changed/removed requirement detected; tiny task stays lightweight. | Planning/context tests and acceptance-baseline regressions. | No uncovered relevant propagation or protected-outcome failure remains. |
| Evidence collector/gate | Real success/failure/timeout; missing or altered receipt; relevant input/artifact mismatch; accurately labeled manual/legacy evidence; reuse of unchanged inputs. | Completion tests in `test_scripts.py`, `test_review_regressions.py`; artifact tests. | Required acceptance and relevant evidence-integrity failures have coverage; no duplicate scenario merely to increase count. |
| Specialist compatibility/return | Valid scoped return; conflicting contract; unexpected scope; required finding unresolved; changed policy invalidates prior assessment; unchanged accepted revision reuses it. | `test_specialists.py` and affected planner tests. | Required assignment/compatibility boundaries have evidence. |
| Package integration | New resources synchronized/included; actual installed CLI imports and required references resolve. | `sync_package.py`, skill validation and offline installation check. | Source and portable runtime agree and required install checks pass. |

Prefer extending existing cases. Add new tests only for meaningful uncovered failure modes. Run a focused check during Build, the affected regression set at integration, and required project/release checks at their existing gate. Do not repeat full suites after every edit or introduce a test-count/coverage target.

Before delivery, use existing representative fixtures to demonstrate the light route, an integration route and a cross-boundary route. Reuse the existing WordPress artifact/runtime validation when its affected adapter requires it. These exercises validate deterministic tooling and workflow contracts; they do not prove autonomous agents deliver every product correctly. A real project trial can later provide that separate evidence, within its own scope and authorization.

## Implementation and delivery handling

Keep one writer for shared formats and completion/assignment contracts. Suggested bounded review units are behavior propagation, execution evidence, specialist acceptance, then documentation/package integration. Split further only when the actual diff becomes hard to review. Do not start additional agents or create unrelated GitHub issues automatically.

Before coding, refresh the repository baseline, inspect applicable instructions and create/reuse an isolated implementation branch. Continue with the currently approved stack, specialists and version policy. Update mirrored runtime resources through `scripts/sync_package.py`; maintain `validate_skill.py` and `install_check.py` manifests when new runtime files genuinely require inclusion.

Each review unit must include its changed behavior, acceptance results, relevant checks, limitations and exact Git state. Finish the next-release documentation only after implementation matches it. Publishing, merging and installing require the authorization applicable to those delivery actions.

## Readiness

Planning artifacts are complete and linked. Runtime implementation has not started. Publishing these documents does not implement the planned capabilities or create a new release/installation. Begin implementation with P0, then B1/B2; the later work consumes their contracts. Update the canonical roadmap at meaningful progress changes.
