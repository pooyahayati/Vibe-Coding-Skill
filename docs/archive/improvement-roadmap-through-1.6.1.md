# Roadmap Archive through 1.6.1

Roadmap IDs were normalized on 2026-10-16 to the permanent R sequence. See the [canonical register](../../ROADMAP.md#roadmap-register) for legacy aliases. Recorded outcomes, evidence and delivery identities are unchanged; old heading anchors remain available. Finding IDs and runtime/schema identifiers retain their separate meaning.

Archived on 2026-10-16 after R28-R30 shipped in 1.6.1. Status, authorization, next-action and local-rollout statements below are historical snapshots. The local activation deferral was subsequently resolved by the owner and 1.6.1 is now active. Use the [current roadmap](../../ROADMAP.md) and [implementation plan](../improvement-implementation-plan.md) for R31-R32 and current delivery state.

Canonical current status. Reviewed: 2026-10-16, Asia/Tehran. The three confirmed reliability gaps from the 1.6.0 audit are fixed and released in 1.6.1, preserving proportionate verification.

## Current position

| State | Position |
|---|---|
| Published runtime | Stable [1.6.1](https://github.com/pooyahayati/Vibe-Coding-Skill/releases/tag/v1.6.1), release commit `f18e1a30a7fbeb488b9853b4de7672cafc8f2cf5`. |
| Local installation | Active **1.6.0**, unchanged at the owner's explicit request. The staged 1.6.1 candidate passed installation checks and matched all 80 published runtime files; it is not the active installation. |
| Audit baseline | Main `80defe5d8061ea85df7a6c523f7120dc85699807`, runtime 1.6.0; code tracing, isolated reproductions and hosted evidence. |
| Current phase | **R28-R30 complete and released. Local rollout deferred by the owner.** |
| Delivered scope | Same-contract specialist reassessment, dynamic test-dependency selection, and verified release recovery. |
| Next action | No remaining R28-R30 implementation. Replace the active local installation only when the owner resumes that rollout and active-assignment protection is resolved. |
| Progress | **3/3 accepted and merged** in [PR #102](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/102). |
| Blockers / limits | No implementation or publication blocker. Local activation is deferred; project latency and general agent quality remain unmeasured. |
| Delivery evidence | All six full baselines passed on the exact release commit; [publication attempt 2](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/38877760579/attempts/2) passed readiness, native Trivy, artifact build and verified draft recovery. |

## Current cycle: targeted reliability R28-R30

<a id="current-cycle-targeted-reliability-h1-h3"></a>

Execution order: **R28 -> R29 -> R30**. The packages have no technical dependency on each other; this is the priority order. Scope, evidence and acceptance belong in the [implementation plan](improvement-plan-through-1.6.1.md#confirmed-audit-findings).

| Order | Package / finding | Required result | Priority | Status |
|---|---|---|---|---|
| 1 | <a id="r28"></a>[R28: Same-contract specialist reassessment](improvement-plan-through-1.6.1.md#r28-same-contract-specialist-reassessment) / F1 | Fresh evidence can be accepted after an in-scope correction without inventing a contract revision or losing retained findings. | High | **Complete** |
| 2 | <a id="r29"></a>[R29: Dynamic regression-test dependencies](improvement-plan-through-1.6.1.md#r29-dynamic-regression-test-dependencies) / F2 | Runtime changes select their existing dynamically loaded regressions; overview edits retain lightweight checks. | Medium | **Complete** |
| 3 | <a id="r30"></a>[R30: Verified release recovery](improvement-plan-through-1.6.1.md#r30-verified-release-recovery) / F3 | Existing releases qualify only after identity, publication state and assets are verified; incomplete publication has an explicit recovery path. | Medium | **Complete** |

## Acceptance and delivery evidence

- **R28:** 20 focused handoff tests plus the extracted-package specialist route passed. The same-contract cycle preserves findings/baseline/authority, rejects prior receipts and decisions, and requires new Head acceptance. Interrupted transition retains instruction protection.
- **R29:** All six selector tests passed, including each of the six dynamically loaded runtime modules on normal/platform routes, transitive helpers, unrelated-class exclusion, unresolved-loader fallback and overview/full profiles.
- **R30:** 20 publication/readiness tests passed. Actual tag resolution and asset download were checked against GitHub. The first publication stopped when its new draft was not yet visible in the release listing; one explicit retry recovered the same draft without moving the tag or replacing assets. No false publication success was claimed.
- **Exact-commit CI:** [Validate Skill](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/38877522789), [Cross Platform Smoke](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/38877522724) (Linux, macOS, Windows), [Real World Repository Validation](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/38877522793), [Agent Skills Spec Compatibility](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/38877522782), [Tool Contract Tests](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/38877522711), and [WordPress Artifact Contract](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/38877522709) passed on `f18e1a30a7fbeb488b9853b4de7672cafc8f2cf5`.
- **Consumer artifact:** The stable release contains its ZIP and matching checksum, 80 files / 261,112 bytes. ZIP SHA-256: `28e9adfbbe4869eae7f3aaf6ecd74d8f79363d03308df9755788dd08581dbf8e`. Independent download verification matched the actual tag and every staged installation file. Native Trivy found no blocking or other secret findings.
- **Local rollout:** Candidate 1.6.1 returned installation `PASS` with no warnings. Activation was then explicitly deferred; the existing installation and retained assignments were left unchanged. No model evaluation/provider key was used.

## Execution and completion rules

- Start one package at a time. Mark its row **In progress** and record its implementation branch/PR, evidence, blocker if any, and next action here.
- Reuse existing tests and sufficient current evidence. Add regressions only for the confirmed failure or a necessary preservation check; no test-count target, coverage quota, new framework, scanner or model evaluation.
- During Build, run affected checks. R29/R30 change CI or delivery controls, so their integration/publication must retain the existing full-baseline requirements; do not repeat the full suite after each edit.
- Preserve Head authority, the sole UI/UX specialist, scoped evidence freshness, required findings, current-source policy and native Trivy before publication. A failing receipt or incomplete release must never become a fabricated pass.
- **Complete** requires accepted behavior and merged implementation, linked to the PR/commit and relevant evidence. Audit reproductions, a local fix or a successful command alone do not establish completion.
- Synchronize changed runtime resources with the portable mirror and check the affected extracted route. Preserve existing record compatibility and retained obligations.
- Commit, merge, release and local installation follow existing user authorization. The user authorized implementation, acceptance, merge, publication and local installation in order.

## Delivered history

| Completed cycle | Retained record |
|---|---|
| R23-R27: proportionate verification, shipped in 1.6.0 | [Specifications](improvement-plan-through-1.6.0.md) and [merge/release/installation evidence](improvement-roadmap-through-1.6.0.md). |
| R18-R22: seven audit findings, shipped in 1.5.0 | [Specifications](improvement-plan-through-1.5.0.md) and [delivery evidence](improvement-roadmap-through-1.5.0.md). |
| R1-R17: initial scope, hardening and delivery follow-ups | [Roadmap](improvement-roadmap-through-1.4.0.md) and [implementation history](improvement-plan-through-1.4.0.md). |

Historical dates and next actions are snapshots. The partial-release concern previously marked unconfirmed is now represented by the reproduced F3/R30 finding; 1.6.0 itself remains verified.

## How progress stays current

Maintain current status, blockers, branch/PR, merge evidence and next action only here. Keep scope and acceptance in the implementation plan; archive closed detail. Update on meaningful transitions using **Not started**, **In progress**, **Blocked**, **Complete**. This is maintained documentation, not an automatic monitor. See [contributor rules](../../CONTRIBUTING.md#roadmap-progress).
