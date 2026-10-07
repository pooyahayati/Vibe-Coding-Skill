# Improvement Implementation and Acceptance Index

Current progress is maintained only in [ROADMAP.md](../ROADMAP.md). This page specifies the five remediation packages, implementation boundaries and acceptance criteria. Historical packages remain delivered and retain their original evidence.

Closed specifications, dependencies and original design decisions: [implementation-plan archive](archive/improvement-plan-through-1.4.0.md) · [roadmap archive](archive/improvement-roadmap-through-1.4.0.md).

## Confirmed audit findings

Baseline: `a6e43fe73500367e52a257e0f9f725166d9c79dc`, audited 2026-10-07; runtime `1.4.0`. All seven findings have high confidence from repository tracing and isolated reproductions. **F1-F7 below are audit finding IDs, not the historical F1 feedback package.** Links identify the implementation to revisit, not immutable future line numbers.

| Finding | Severity | Reproduced failure and evidence | Package |
|---|---|---|---|
| F1 | High | [Workspace identity](../scripts/local_workspace.py) changes when `origin` is added/changed, hiding retained state. [Recovery](../scripts/state_recovery.py) regenerates corrupt project state without the accepted contract; [resume](../scripts/resume_context.py) returned `PASS`, no warnings and no retained acceptance in a documented clean fixture. This proves lost continuity, not a demonstrated false `Done`. | A1 |
| F2 | High | After specialist acceptance, [state capture](../scripts/project_state.py) accepts an authorized scope extension, but [specialist completion](../scripts/specialist_handoff.py) raises `operation belongs to another root/contract`. It checks every retained operation against the replacement contract; there is no supported revision transition for those operations. | A1 |
| F3 | High | [Router normalization](../scripts/context_router.py) uses `lstrip("./")`: `.github/workflows/validate-skill.yml` becomes `github/workflows/validate-skill.yml`. The affected scan inspected zero files without a limitation; matching nested `AGENTS.md` selections were lost. | A2 |
| F4 | Medium | [Graph refresh](../scripts/graph_provider.py) copies source before execution but fingerprints the live tree afterward. An injected source edit during generation left an old graph reported as `fresh: true`. | A2 |
| F5 | Medium | [Dependency guard](../scripts/dependency_guard.py) accepted `MIT AND GPL-3.0-only` with an MIT-only allow-list. Its npm adapter also used package-level repository/license metadata when the selected version had different or missing metadata. | A3 |
| F6 | Medium | [WordPress runner](../scripts/wordpress_artifact.py) truncates merged stdout/stderr before JSON parsing. A valid 60-plugin response of 6,240 characters became invalid after truncation to 4,000. | A4 |
| F7 | Medium | [Integration guard](../scripts/integration_guard.py) returned `FAIL`/exit 2 for Tier 3 development solely because Trivy was missing, with no publication request. [Head policy](../SKILL.md) and [security policy](../references/security-and-dependencies.md) permit safe development while blocking publication; the guard has no stage/equivalence input. | A5 |

These are the complete implementation scope for this cycle. Existing-tag/partial-release retry behavior remains unconfirmed and is not an additional package. The audit's passing checks and package/installation comparison are recorded in the roadmap; they do not qualify a future fix.

## A1: Retained-state and contract continuity

**Purpose:** Fix F1/F2 without weakening independent acceptance, receipt freshness or required specialist findings. **Complexity:** Medium. Start here; no earlier package is required.

**Affected components:** `local_workspace.py`, `project_state.py`, `state_recovery.py`, `resume_context.py`, `specialist_handoff.py`; receipt/behavior binding only where migration requires it; recovery, state, specialist-composition and shared-format references.

**Implementation sequence:**

1. Define stable checkout identity and compatibility with existing workspace/receipt identities. Treat the remote URL as mutable metadata. Preserve project isolation and stop for ambiguous legacy matches; never silently adopt another project's evidence.
2. Separate recoverable caches from retained obligations. Write authoritative state atomically, keep a recoverable accepted baseline, and surface missing required context when no valid baseline can be recovered. Preserve existing task IDs, workflow selection, risk and evidence obligations.
3. Add an explicit Head-reconciled contract revision transition for retained specialist operations. Preserve history and required findings; identify which assignments must be reassessed, superseded or reopened. Unchanged work may be reused only with verified bindings; old acceptance cannot automatically approve changed scope.
4. Align capture, handoff, resume and completion with those decisions and document migration. Do not make disposable-cache loss block an otherwise recoverable lightweight task.

**Acceptance criteria:**

- Creating `origin` after local work, or changing an equivalent remote URL, retains the task/receipt ledger or offers a verified migration. Distinct projects and ambiguous matches remain isolated.
- An interrupted state write retains a valid accepted baseline. A corrupt-state repair either restores required context or explicitly requires reconstruction/reconciliation; it cannot return unqualified readiness after losing obligations.
- Authorized scope/criterion revisions after active or accepted specialist work have a supported path to completion. Removed/superseded assignments retain required-finding history; unreconciled changes still block.
- No risk downgrade, schema-3-to-schema-2 fallback, stale-receipt reuse or automatic Head acceptance is introduced. Normal resume and light/manual/legacy behavior remain supported.

**Verification:** Extend the existing state/recovery, receipt and handoff fixtures with remote-change and corrupt-state cases, plus an accepted-specialist -> authorized-revision -> renewed-evidence/acceptance -> completion route. Include a conflicting-project negative case and exercise the affected route from the extracted portable package. Reuse unaffected receipt tests; do not rerun checks merely because unrelated files changed.

## A2: Reliable routing and graph inputs

**Purpose:** Fix F3/F4 so context and freshness refer to the actual source. **Complexity:** Medium. Follow A1; reuse its accepted workspace identity if changed.

**Affected components:** `context_router.py`, `graph_provider.py`; context-routing and graph-provider references. Inspect repeated path normalization at all affected router call sites, not only the first helper.

**Correction:** Normalize path components without stripping real leading dots. Preserve existing containment/root/literal-path protections. Bind graph metadata to the source snapshot actually processed; compare relevant source identity around snapshot/generation and reject or mark stale when it changes. Keep any retry bounded and explicit.

**Acceptance criteria:**

- Real `.github`/`.devcontainer` paths remain literal, are inspected when selected, and retain governing root/nested `AGENTS.md`; unrelated siblings remain excluded.
- `./`, backslash, project-root and bracket-containing routes preserve existing supported meaning. Absolute/escaping inputs cannot become apparently safe relative paths. Relevant uninspected inputs produce an explicit limitation.
- An injected edit during snapshot/generation never yields a fresh graph for the changed tree. Stable-source refresh still succeeds; a failed refresh does not replace known evidence with a false-current result.

**Verification:** Add path fixtures to existing context-routing tests and a provider stub that mutates source during graph generation to the existing graph contract tests. Check the affected routing entrypoint in the portable integration suite; no live Graphify installation or model run is needed for these regressions.

## A3: Version-bound dependency decisions

**Purpose:** Fix F5's false acceptance paths. **Complexity:** Medium. No runtime dependency on A2.

**Affected components:** `dependency_guard.py`, its existing registry/policy tests and security/dependency guidance.

**Correction:** Bind npm license and provenance evidence to the requested version. Keep missing version-specific evidence unknown instead of filling it from another version. Evaluate supported license expressions against explicit project policy; unsupported or ambiguous expressions require review rather than an inferred acceptance. A bounded conservative evaluator is sufficient; no new dependency is assumed.

**Acceptance criteria:**

- MIT-only policy does not accept `MIT AND GPL-3.0-only`; supported `AND`, `OR` and exception handling follow documented policy, with unresolved expressions returning `REVIEW REQUIRED`.
- A selected npm version's repository/license overrides unrelated package-level metadata. Missing selected-version evidence stays missing unless independently established for that same version.
- Existing simple permitted/denied licenses, version checks and risk-required evidence behavior remain correct. No default license policy is imposed on projects that have not specified one.

**Verification:** Use deterministic registry-response fixtures with conflicting/missing version metadata and table-driven expression cases in existing dependency tests. Run live registry checks only at their existing CI gate or if adapter behavior actually requires live confirmation.

## A4: WordPress command output integrity

**Purpose:** Fix F6 without changing the plugin lifecycle contract. **Complexity:** Small. No dependency on A3.

**Affected components:** `wordpress_artifact.py`, its runtime fixtures and WordPress delivery guidance if the output contract changes.

**Correction:** Parse complete structured stdout separately from stderr. Bound only diagnostic presentation, or fail explicitly at a documented input limit; never parse silently truncated JSON. Preserve command failure/timeout reporting and exact-artifact verification.

**Acceptance criteria:**

- A valid plugin list above 4,000 characters parses successfully within the supported limit; a zero-exit command with stderr diagnostics does not corrupt that JSON.
- Invalid JSON, nonzero exits, timeouts and unsupported oversized output remain explicit failures rather than success or silent data loss.
- Install/upgrade checks still use the exact supplied artifacts, verify versions and preserve existing uninstall/data safeguards.

**Verification:** Extend the existing WP-CLI stub fixtures with a long plugin list, separate warning output and malformed output. Run affected artifact/runtime tests; use the existing WordPress Artifact Contract CI for real-environment validation at integration, without touching a user's live site.

## A5: Stage-aware integration controls

**Purpose:** Fix F7's instruction/runtime contradiction. **Complexity:** Medium. No dependency on A4; reuse A2 freshness semantics where relevant.

**Affected components:** `integration_guard.py`, its callers/tests, `references/risk-classifier-and-integrations.md` and canonical security guidance; update Head instructions only if the public control contract needs clarification.

**Correction:** Distinguish tool availability, required capability evidence and publication readiness. Supply enough operation/stage context to apply the actual requirement. Use the native release scanner as the authoritative publication check; an availability check or equivalent development control cannot waive it. Remove obsolete contradictory guidance rather than duplicating another policy.

**Acceptance criteria:**

- Safe non-publication work does not fail solely because Trivy is absent. Missing task-required security evidence still blocks the affected action.
- Publication still requires a working native Trivy runtime and qualifying scans bound to the final target; presence alone, Docker fallback or a development equivalent cannot satisfy that gate.
- A stale graph blocks authoritative reliance on that graph, not an explicitly supported source-analysis fallback. Unsupported/missing operation context cannot silently grant publication readiness.
- Existing callers, exit codes and compatibility/migration behavior are explicit and tested; all routed guidance agrees on the boundary.

**Verification:** Extend integration-guard scenarios for development versus publication, missing/available-but-unscanned Trivy, stale graph reliance versus source fallback, and legacy callers. Reuse native release-gate tests to establish that publication remains protected; do not add another scanner or a duplicate security workflow.

## Package execution and closeout

Implement one package at a time in the roadmap order. Begin each with its minimal failing reproduction; implement the smallest correction, run the affected checks, review the diff and preserve remaining limitations. Use existing test modules; do not create a new test framework or fixed coverage quota.

When runtime resources change, synchronize the portable mirror and verify the affected installed entrypoints. Shared state/format changes need explicit compatibility decisions and migration regressions. Existing required CI remains the integration gate; model evaluations and provider keys are outside this cycle.

Record progress, branch/PR, merge evidence and the next action only in the roadmap. A locally tested fix is not yet a completed package. Release and installation evidence must be recorded separately after those actions are authorized and verified; this plan does not select a release number or modify an installed skill.

## Targeted hardening cycle R1-R4

| Package | Preserved acceptance boundary | Specification / evidence |
|---|---|---|
| R1 | Fresh structured tasks require receipts; legacy compatibility is explicit; required specialist IDs cannot disappear without reconciliation. | [Archived criteria](archive/improvement-roadmap-through-1.4.0.md#r1-retained-contract-and-required-completion-controls) · [current completion guidance](../references/execution-and-verification.md#receipt-backed-completion-e2). |
| R2 | Large plugin headers retain platform routing; unrelated PHP stays unrelated; incomplete relevant inspection is visible. | [Archived criteria](archive/improvement-roadmap-through-1.4.0.md#r2-bounded-discovery-without-silent-platform-loss) · [context routing](../references/context-routing-and-execution.md). |
| R3 | Root scope covers nested paths and overlaps nested writers; disjoint/literal paths remain valid. | [Archived criteria](archive/improvement-roadmap-through-1.4.0.md#r3-consistent-project-root-ownership) · [planning guidance](../references/context-routing-and-execution.md). |
| R4 | Release rules match the implemented gate; portable commands resolve or are explicitly optional full-source routes. | [Archived criteria](archive/improvement-roadmap-through-1.4.0.md#r4-one-accurate-operational-validation-path) · [validation policy](../references/validation-and-benchmarking.md). |

## Current contract ownership

| Mechanism | Canonical instructions | Key boundary |
|---|---|---|
| P0 formats / migration | [Shared improvement contracts](../references/shared-improvement-contracts.md) | Identity, origins, storage/trust limits and supported migration; records grant no authorization. |
| B1 observable behavior | [Behavior contract](../references/operating-model.md#observable-behavior-contract) | Actor action/result and only meaningful failure/protected-state expectations. Tiny tasks stay inline. |
| B2 retained behavior | [Plan propagation](../references/context-routing-and-execution.md#retained-behavior-in-a-plan-b2), [state/handoff](../references/project-state-automation.md#preserve-task-behavior-and-useful-delivery-details-b2) | Preserve criteria, protected outcomes and commitments; detect removal or material change. |
| E1 local collection | [Execution receipts](../references/execution-and-verification.md#local-execution-receipts-e1) | Explicit authorized commands, bounded execution, scoped inputs and exact artifacts outside product source. |
| E2 completion | [Receipt-backed completion](../references/execution-and-verification.md#receipt-backed-completion-e2) | Required failed/missing/stale evidence blocks; manual/legacy evidence is accurately labeled. |
| S1 instruction compatibility | [Compatibility assessment](../references/specialist-composition.md#instruction-compatibility-assessment-s1) | Source currency/package validity is separate from Head acceptance of current instructions. |
| S2 task acceptance | [Stage returns](../references/specialist-composition.md#stage-return-and-head-acceptance-s2) | Assess actual scope/contracts/findings/receipts; specialist Done is not whole-task completion. |
| I1 portable integration | [Verification snapshot](i1-integration-verification.md) | Exercise installed entrypoints from the extracted ZIP; fixtures do not prove arbitrary agent outcomes. |
| F1 feedback | [Skill feedback](../references/skill-feedback.md) | Attribute confirmed/suspected skill defects, protect sensitive content and send nothing automatically. |

## Necessary verification

| Changed area | Relevant evidence to reuse |
|---|---|
| Behavior/state/plans | Preserved criteria and task identity; material changes detected; light route remains light. |
| Receipt collection/completion | Actual success/failure/timeout, freshness/artifact binding, manual/legacy labeling and required-failure rejection. |
| Specialist compatibility/return | Bound current instructions, allowed scope/shared contracts, resolved required findings and separate Head acceptance. |
| Package/runtime resources | Mirror, required resources and actual extracted offline/CLI integration. |
| Documentation only | Accurate claims, working links/anchors, preserved constraints and relevant mirror consistency; no wording-only tests. |

Extend affected regressions only for meaningful uncovered failures. Run existing required CI at its normal gate; do not repeat unrelated suites. Receipts cannot prove adequate assertions or resist an actor who controls both source and records; Head judgment and host controls remain necessary.

## Implementation and delivery handling

Use one writer for shared contracts and the existing stack/specialists. Keep approved work on an isolated branch, runtime mirrors synchronized and generated reports/state outside product source. Record changed behavior, relevant results, limits and actual Git state. Merge, publication and installation need their applicable authorization; a local draft or version string proves none of them. [Contributor guidance](../CONTRIBUTING.md).
