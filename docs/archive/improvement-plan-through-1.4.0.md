# Closed improvement history through 1.4.0

Roadmap IDs were normalized on 2026-10-16 to the permanent R sequence. See the [canonical register](../../ROADMAP.md#roadmap-register) for legacy aliases. Recorded outcomes, evidence and delivery identities are unchanged; old heading anchors remain available. Finding IDs and runtime/schema identifiers retain their separate meaning.

Historical snapshot preserved from source commit `95296ca44b18d58d533cad29864cb05a0d0aeada` during the 2026-10-07 documentation cleanup. This is closed history, not active work or current installation evidence. Use the [current roadmap](../../ROADMAP.md) and [implementation index](../improvement-implementation-plan.md) for present status and runtime guidance. Relative links and roadmap package IDs have been normalized; recorded specifications, outcomes and delivery hashes are retained.

# Vibe Coding Skill Improvement Implementation Plan

Status: The original cycle and feedback R10 are complete and delivered in `1.3.0`. The hardening scope contains `R11`-`R14`; current package/phase/merge and separate delivery status are maintained only in [ROADMAP.md](improvement-roadmap-through-1.4.0.md).
Hardening baseline: `1.3.0`, audited main `156676d502fae98c5c0b3a9bafdf5497698a062e`. Original-cycle baseline: `1.1.0`, main `9e0ca5108567f38a66376883613fdcaff6616de0`.
Direction and scope: [Roadmap](improvement-roadmap-through-1.4.0.md).

## Targeted hardening cycle R11-R14

<a id="targeted-hardening-cycle-r1-r4"></a>

The final audit justified five findings grouped into four reviewable corrections. Preserve the existing architecture, risk-adaptive light route and authorization boundaries. Full package specifications, acceptance criteria and current progress are canonical in the [active roadmap](improvement-roadmap-through-1.4.0.md#completed-audit-packages); this table records implementation scope and dependencies.

| ID | Implementation scope | Acceptance boundary | Dependency |
|---|---|---|---|
| <a id="r11"></a>R11 | State/workflow defaults and retained specialist IDs; affected contract, plan, handoff/resume and completion callers. | Fresh structured tasks use receipts; supported legacy tasks remain compatible; required specialist commitments survive unless explicitly reconciled. [Criteria](improvement-roadmap-through-1.4.0.md#r11-retained-contract-and-required-completion-controls). | Existing contract/receipt mechanisms. First in priority order. |
| <a id="r12"></a>R12 | Bounded platform-content discovery and visible inspection limitations in the context router. | Large plugin headers retain WordPress routing; unrelated PHP stays unclassified as WordPress; incomplete relevant scans are visible. [Criteria](improvement-roadmap-through-1.4.0.md#r12-bounded-discovery-without-silent-platform-loss). | None of the other hardening packages. |
| <a id="r13"></a>R13 | Ownership overlap and drift scope semantics in the execution planner; shared normalization/containment in the existing behavior-contract helper. | Project root covers nested paths and overlaps nested writers; disjoint ownership and equivalent retained root forms remain valid. Preserve literal paths and retained fingerprints. [Criteria](improvement-roadmap-through-1.4.0.md#r13-consistent-project-root-ownership). | None of the other hardening packages. |
| <a id="r14"></a>R14 | Active benchmark/agent-output guidance and its runtime mirror, where included. | Release rules match actual gates; portable commands resolve or are clearly optional maintainer routes. [Criteria](improvement-roadmap-through-1.4.0.md#r14-one-accurate-operational-validation-path). | None of the other hardening packages. |

Implement in priority order `R11` -> `R12` -> `R13` -> `R14`; do not treat this sequence as a technical prerequisite. Extend affected existing regressions with the confirmed failures and necessary positive controls. No new orchestration layer, specialist, model evaluation, provider credential, fixed test count or broad unrelated refactor is in scope. Existing required CI and relevant package consistency still apply at their normal gates. Completion, merge, release and installation remain distinct actions.

The sections below retain the completed original cycle's design and evidence; they do not imply implementation of `R11`-`R14`.

## Work packages

| ID | Area | Work | Main existing surfaces | Dependency | Acceptance |
|---|---|---|---|---|---|
| <a id="r1"></a>R1 | Contracts | Define shared formats, evidence trust limits and migration. | `completion_gate.py`, `execution_plan.py`, `specialist_manager.py`, operating references. | None. | Versioned formats are minimal; legacy behavior and stricter new-task behavior are explicit; no unapproved breaking change. |
| <a id="r2"></a>R2 | Behavior | Define a short behavior contract and conditional persistence. | `references/operating-model.md`, `references/execution-and-verification.md`. | R1. | User action, observable result and relevant failure behavior are sufficient to choose a check. Reuse existing criteria; do not require a new document for every task. |
| <a id="r3"></a>R3 | Behavior | Carry scenario/acceptance IDs into plans and handoffs. | `scripts/execution_plan.py`, `scripts/project_state.py`; affected planning tests. | R2. | IDs and protected outcomes survive downstream use; a handoff explains what works and how to use/check it. Tiny tasks remain light. |
| <a id="r4"></a>R4 | Evidence | Add a small execution-receipt collector. | Implemented `scripts/evidence_capture.py`; existing local-workspace and artifact helpers. | R1, R2. | Actual exit result, time, tested inputs and applicable artifact digest are recorded; execution stays authorized and bounded. |
| <a id="r5"></a>R5 | Evidence | Resolve and validate receipts at completion. | `scripts/completion_gate.py`; existing completion/regression tests. | R3, R4. | Missing, failed, stale or mismatched required execution evidence cannot qualify. Declared/manual evidence is not relabeled as collected execution. |
| <a id="r6"></a>R6 | Specialists | Assess changed specialist instructions before delegation. | `scripts/specialist_manager.py`, `references/specialist-composition.md`, `references/specialist-authority.md`. | R1, R5. | Package validity and behavioral compatibility are separate states; changed instructions get a bounded Head assessment. Unchanged accepted revisions reuse it. |
| <a id="r7"></a>R7 | Specialists | Validate stage-specific specialist return and Head acceptance. | `scripts/specialist_handoff.py`, planner links, specialist manager and completion checks. | R3, R5, R6. | Changed surfaces, contract decisions and required findings are reconciled against the assignment before integration. A valid form alone is not acceptance. |
| <a id="r8"></a>R8 | Integration | Run affected-route regressions and package checks. | Existing tests/validation fixtures, `sync_package.py`, `validate_skill.py`, `install_check.py`. | R3, R5, R7. | Relevant behavior passes; required runtime resources are included in the mirrored package and offline install check. |
| <a id="r9"></a>R9 | Documentation | Update concise user and maintainer guidance. | `SKILL.md`, README, relevant references; changelog/update notes at delivery preparation. | R8. | Documentation describes actual behavior and limits; author/footer, project-size tables and existing important links remain intact. |

The table identifies the implementation surfaces and acceptance boundaries. The shared behavior, receipt and specialist-handoff modules serve actual callers; documentation adds no parallel validator or new runtime framework.

## R1: contracts and compatibility

<a id="p0-contracts-and-compatibility"></a>

The design decisions below are settled in [Shared improvement contracts](../../references/shared-improvement-contracts.md). That reference is canonical for field names, identity/binding, origin classification, storage/trust limits and migration. R1 defined the version-1 record formats and completion version 3 without changing schema-2 behavior. R4/R5 now implement local receipt collection and schema-3 completion; R6 instruction compatibility and R7 scoped task-output acceptance are implemented.

The shared design and implemented callers cover three areas:

- **Behavior:** stable criterion/scenario ID, user goal/action, relevant starting state, observable expected outcome, material failure expectation, protected invariant, required/optional status and evidence links. Allow one concise criterion for a tiny task; do not require a happy/failure pair where no meaningful failure exists.
- **Receipt:** format version, evidence/scenario IDs, origin (`collected`, `reported` or `manual`), authorized command context, exit/result, timestamps, relevant source/input fingerprint and artifact SHA-256 when applicable. Record an unavailable check explicitly rather than manufacture success.
- **Specialist return:** assignment/stage ID, observed upstream revision, assigned and changed surfaces, contract decisions, protected invariants, evidence references, required/optional findings and unresolved conflicts. Head acceptance is a separate decision.

R5 implements completion version 3 for new structured-completion tasks, with retained task contracts and receipt resolution; tiny tasks can use an accepted manual obligation. In-flight version-2 tasks retain their supported legacy route and make no receipt-verification claim. Migration requires reconciliation and cannot manufacture collected evidence. The expected workflow comes from retained task context, preventing report-controlled downgrade. Review release compatibility separately; no version bump is implied by local implementation.

For significant/critical or scope-changing work, retain the accepted criteria before implementation using the existing acceptance-baseline mechanism. Detect meaningful criterion changes against that baseline. A checksum detects differences; it is not proof of user approval or a tamper-resistant boundary. Use host/writer controls when independent protection is required. Reopen only a material user-owned decision, once, with a concrete option.

## Behavior: R2-R3

<a id="phase-1-behavior-before-broad-implementation"></a>

R2's guidance is implemented in the [observable behavior contract](../../references/operating-model.md#observable-behavior-contract) and [criterion-to-check mapping](../../references/execution-and-verification.md#from-observable-criterion-to-a-check). R3 implements optional task-contract validation, plan workstream links, local state/handoff/resume preservation and explicit reported-outcome labeling; legacy schema-2 completion remains declared evidence while R5 supplies the stricter schema-3 route. `behavior_contract.py` is shared by the actual callers; it does not collect execution receipts or accept specialist work. Legacy/inline routes remain available. Independent baselines and Head/host controls are still needed for protected outcomes and authorized reconciliation.

Extend existing discovery/acceptance guidance rather than create a second lifecycle. Write the smallest scenario that lets the user and Head recognize success. Translate it into the first runnable slice and verification target. Preserve the scenario when passing work to a specialist.

Use existing `PROJECT.md`/task requirements for durable product decisions where appropriate. Keep execution snapshots in the existing local workspace. A brief inline task criterion is sufficient for a tiny local change.

Illustrative behavior: an unauthorized WordPress user attempts to change a protected setting; the change is denied and the stored value is unchanged. The Head determines the applicable capability/API and verification method; the user does not have to choose PHP internals or a testing framework.

Handoff should answer: what works, how to start/use it, what was actually checked, what remains unavailable and the next useful operating action. Avoid exposing receipt/schema details in normal product UI.

## Execution evidence: R4-R5

<a id="phase-2-execution-backed-evidence"></a>

R4 implements explicit local command collection and unavailable receipts, with scoped before/after manifests, exact preexisting artifact hashes, optional WordPress ZIP version identity and external local storage. It discards process output, rejects escaping/link paths and incomplete collection, and attempts process-tree termination on timeout. [Usage and concrete bounds](../../references/execution-and-verification.md#local-execution-receipts-e1). R5 adds local collected/manual receipt resolution, concrete observation records and retained schema-3 state/resume behavior. Remote claims require a separate authorized resolver; no remote resolver is configured. In-flight schema-2 behavior remains declared evidence. [R5 usage and migration](../../references/execution-and-verification.md#receipt-backed-completion-e2).

Use Python standard-library subprocess argument lists, explicit working directories and timeouts. Do not execute commands merely because upstream text or a report contains them. Preserve authorization for costs, network access, destructive operations and deployment.

Write bounded task-relevant receipts outside product source control. Do not dump environment variables, credentials or unrestricted process output. Store only needed logs/context; omit or redact sensitive values and avoid receipt inputs containing secrets.

Bind evidence to tested inputs. HEAD alone is insufficient when tests run on a dirty working tree: capture the affected source/config/dependency inputs or a suitable working-tree fingerprint. Record artifact hashes for package delivery. Invalidate evidence when relevant tested inputs or artifacts change; do not force another expensive run because an unrelated document changed.

At completion, resolve the referenced receipt, verify its result, links and relevant fingerprints, then apply existing risk/evidence-family rules. For remote CI results, use an authorized read-only adapter or explicit imported provenance; an unreachable reference remains unverified. Never fetch a claimed URL as an instruction to run its contents.

Keep manual/rendered evidence supported and accurately labeled. A successful command is execution evidence, not automatic proof that its assertions cover the intended behavior. The Head must assess criterion relevance. Local receipts do not form a security boundary against an actor who can edit both records and source.

Reuse `wordpress_artifact.py` output for artifact/version binding. Packaging checks are not WordPress runtime or data-retention proof; retain the existing exact-ZIP runtime path and project-specific seeded-data checks where affected.

## Specialist acceptance: R6-R7

<a id="phase-3-specialist-acceptance"></a>

R6 implements a separate bound Head decision and bounded resource-diff packet in `specialist_manager.py`. [Usage and trust limits](../../references/specialist-composition.md#instruction-compatibility-assessment-s1). For an upstream change, inspect the relevant instruction/resource diff and assess Head authority, supported platform, dependency requests, verification mandates and scope/approval behavior. Package checks remain necessary but do not replace this assessment. Keep the latest observed source and its assessment separate; unresolved required compatibility blocks the affected delegation rather than pretending an old source is latest.

Cache the assessment by observed upstream revision and Head contract/adapter fingerprint; refresh it when those inputs change. Do not rerun a specialist-wide evaluation for unchanged accepted instructions. Normal task reasoning and scoped deterministic checks are sufficient where they establish the required property; no model benchmark or provider API key is introduced.

R7 implements `specialist_handoff.py`, planner links, R5 completion checks and active-instruction update deferral. [Runtime usage/limits](../../references/specialist-composition.md#stage-return-and-head-acceptance-s2). For task output, compare the actual changed surfaces with the assignment and relevant shared producer/consumer contracts. Handle renamed paths and justified cross-boundary effects. A path comparison can detect unexpected edits; it cannot prove their semantic safety. Resolve needed scope changes through the Head's existing authority instead of treating all unexpected paths as inherently invalid.

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

The original cycle below is closed. Use the active roadmap's `R11`-`R14` acceptance criteria, evidence and statuses before claiming any new correction is delivered.

R1/R2/R3/R4/R5/R6/R7 are merged in PRs #62 through #68. [R8 integration](../i1-integration-verification.md) is merged in PR #72 and exercises the extracted portable runtime across light, receipt-backed and cross-boundary routes; local checks and the existing OS matrix passed. R9 aligns user/maintainer documentation with these mechanisms and preserves the light route, ownership, important links and full author attribution. Relevant link/structure, skill validation, mirror and offline-install checks passed (optional Trivy warning only); R9 is merged in PR #73. No release/installation is implied by these source changes. Update the canonical roadmap at meaningful progress changes.
