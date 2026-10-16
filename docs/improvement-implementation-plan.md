# Improvement Implementation and Acceptance Index

Progress and the next action are maintained only in [ROADMAP.md](../ROADMAP.md). This document defines H1-H3 scope and acceptance in priority order. Current implementation and delivery evidence belong in the roadmap.

## Confirmed audit findings

Baseline: main `80defe5d8061ea85df7a6c523f7120dc85699807`, runtime `1.6.0`, audited 2026-10-16. F1-F3 below refer to this audit only; findings in earlier archives retain their historical meaning. Confidence is high in all three findings. No new model evaluation or performance benchmark was run.

| Finding / package | Severity | Confirmed behavior and evidence |
|---|---|---|
| F1 / H1 | High | An accepted `current-delivery` specialist operation blocks completion after an input changes. A fresh passing execution cannot be accepted because the closed return changes; reopening requires a different task contract. Reproduced with the existing temporary handoff fixture. [Closed-return check](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/80defe5d8061ea85df7a6c523f7120dc85699807/scripts/specialist_handoff.py#L418-L446); [reconciliation restriction](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/80defe5d8061ea85df7a6c523f7120dc85699807/scripts/specialist_handoff.py#L457-L472). |
| F2 / H2 | Medium | The selector misses literal `load("module")` dependencies in `test_review_regressions.py` (14 tests in three classes). Separate changes to its six runtime modules select none of those classes in either normal or platform selection. [Dependency extraction](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/80defe5d8061ea85df7a6c523f7120dc85699807/scripts/ci_scope.py#L26-L67); [dynamic loader](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/80defe5d8061ea85df7a6c523f7120dc85699807/tests/test_review_regressions.py#L14-L40). Full release validation still includes them. |
| F3 / H3 | Medium | The release workflow exits successfully as soon as `gh release view` succeeds, without checking draft state, target identity or required assets. The exact shell branch returned success for simulated existing-draft, missing-ZIP and wrong-target states. [Existing-release branch](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/80defe5d8061ea85df7a6c523f7120dc85699807/.github/workflows/release.yml#L82-L108). The real 1.6.0 release was independently verified complete. |

## H1: Same-contract specialist reassessment

**Priority:** High. **Complexity:** Medium. **Dependency:** None; first implementation package.

**Why it matters:** An ordinary in-scope correction after specialist acceptance can strand structured completion. Changing the accepted task contract just to reopen the specialist can invalidate unrelated receipts and create unnecessary work.

**Correction:** Add an explicit, reasoned reassessment transition for the same task contract. Preserve the previous acceptance and finding history, reopen the assignment under valid Head/specialist controls, and require a fresh return and separate Head acceptance. Do not invent a contract field, remove a retained assignment or relabel an old receipt to bypass the closed state.

**Likely components:** `scripts/specialist_handoff.py`; receipt/completion/state callers only if required by the transition; `references/specialist-composition.md`; existing `tests/test_handoffs.py` and the affected portable integration route.

**Acceptance:**

- With task identity, contract digest, scope and outcomes unchanged, an accepted assignment can be explicitly reopened after a relevant input/context/control change. New scope or changed requirements still use the existing contract-reconciliation route.
- Old acceptance and stale receipts cannot qualify completion. New passing receipts plus a fresh Head decision can qualify the reassessed assignment without recreating unrelated task evidence.
- Required findings, protected invariants, authorized scope and acceptance history survive reopening. A new assignment ID or abandoning the old operation cannot erase unresolved obligations.
- Reopened operations restore active-instruction protection until accepted or explicitly abandoned. Retained records remain readable; an interrupted transition must not manufacture acceptance or lose the outstanding operation.

**Verification:** Extend the existing handoff fixture from accepted -> relevant change -> stale evidence blocked -> explicit same-contract reopening -> fresh receipt/return/Head decision -> completion. Reuse finding-retention, stale-context, marker and changed-contract checks. Exercise the affected route from the extracted package once runtime behavior is ready; no live specialist installation is needed for the fixture.

## H2: Dynamic regression-test dependencies

**Priority:** Medium. **Complexity:** Small. **Dependency:** None technically; follows H1 by priority.

**Why it matters:** Existing regressions can be skipped during development even though their runtime module changed. Preserving selective CI requires an accurate dependency map, not a return to full testing for every edit.

**Correction:** Recognize the repository's supported dynamic-loading pattern or supply a small explicit dependency mapping where static inference is inadequate. Keep selection explainable and conservatively handle unresolved impact using the existing fallback.

**Likely components:** `scripts/ci_scope.py`, existing selector tests in `tests/test_scripts.py`; test dependency declarations only if chosen. Preserve the current runtime regression scenarios.

**Acceptance:**

- Changes to `completion_gate.py`, `context_router.py`, `dependency_guard.py`, `execution_plan.py`, `risk_classifier.py` and `wordpress_artifact.py` select their relevant classes from `tests/test_review_regressions.py`, including the applicable platform route.
- Supported static and dynamic dependency edges compose with existing callers/helper propagation; an unmapped or ambiguous dependency cannot silently establish reliable focused coverage.
- Overview-only documentation still uses the overview profile. Ordinary mapped changes remain selective; this fix adds no global test-count or coverage quota.
- Release/full-validation selection and its evidence markers remain intact.

**Verification:** Assert actual selector outputs for the existing dynamic loader, representative ordinary imports/helper dependencies, unresolved impact and overview-only edits. Use focused selector checks during implementation. Because `ci_scope.py` controls CI, retain the existing full integration baseline at the authorized PR/merge boundary, rather than rerunning it after every edit.

## H3: Verified release recovery

**Priority:** Medium. **Complexity:** Medium. **Dependency:** None technically; follows H2 by priority.

**Why it matters:** A cancelled/interrupted publication can leave an existing draft or incomplete release. A later successful workflow must not imply that a complete consumer package was published.

**Correction:** Inspect the existing release and actual tag target before treating publication as complete. Verify expected assets and checksum/content identity. Reuse an already complete matching release without duplicate publication; report an incomplete or inconsistent state explicitly and support bounded recovery of a matching draft under existing publication authorization.

**Likely components:** `.github/workflows/release.yml`, a focused release-state helper if needed, existing release/readiness tests, and contributor/release guidance. Change build/readiness interfaces only where necessary for the verified result.

**Acceptance:**

- Existence alone is insufficient: a draft, missing asset/checksum, mismatched tag target or mismatched asset digest cannot yield publication success.
- Resolve the actual tag commit, including an annotated tag where applicable; do not rely only on release `target_commitish` or assume `--target` moves an existing tag.
- A complete matching published release is safely reusable. A matching incomplete draft can be explicitly recovered; incompatible existing content blocks with a concrete next action. Never silently delete a published release, replace its assets or move its tag.
- Recovery preserves exact-revision full-validation evidence, native Trivy checks for the final artifact and existing authorization. It cannot turn prior partial CI or stale artifacts into new publication evidence.

**Verification:** Use deterministic GitHub/CLI fixtures for complete, draft, interrupted upload, missing asset, wrong-target and checksum-mismatch states. Verify repeated execution and recovery decisions without creating or deleting a real release. Retain the existing full CI baseline for delivery-control changes; verify real publication only when a release is authorized.

## Implementation and validation boundaries

1. When implementation is requested, begin H1 only. Recheck the current repository and minimal reproduction, then use the existing branch/PR workflow. Keep one owner for shared state and delivery controls.
2. Run checks justified by the affected behavior. Extend existing regression fixtures rather than introducing a framework or repeating broad suites after each edit. Record audit reproduction separately from fix verification.
3. Update canonical runtime sources and generated portable resources together when applicable. Documentation-only planning receives structure, links, purity and mirror checks.
4. Record acceptance, actual check results, branch/PR and merge evidence in the roadmap before marking a package Complete. Follow the existing user-authorized sequence; release and local installation are separate delivery steps.

No redesign, new specialist/scanner, model evaluation, provider key, test quota or unrelated cleanup belongs to this cycle. Keep Head authority, one UI/UX specialist, risk-proportionate verification, local retained state, scoped receipt freshness and native Trivy before publication.

Measured speed gains and universal real-agent conformance are not established by these reproductions and are not additional implementation packages.

## Delivered specifications

- [T1-T5 specifications through 1.6.0](archive/improvement-plan-through-1.6.0.md) and [delivery evidence](archive/improvement-roadmap-through-1.6.0.md).
- [A1-A5 specifications through 1.5.0](archive/improvement-plan-through-1.5.0.md) and [delivery evidence](archive/improvement-roadmap-through-1.5.0.md).
- [Earlier implementation history](archive/improvement-plan-through-1.4.0.md) and [roadmap history](archive/improvement-roadmap-through-1.4.0.md).

Archived next actions and unconfirmed concerns are historical. The formerly unconfirmed partial-release concern is now scoped to the reproduced F3/H3 defect. The [current roadmap](../ROADMAP.md) is the only progress tracker.
