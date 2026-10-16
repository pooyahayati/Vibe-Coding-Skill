# Improvement Roadmap

Canonical progress tracker. Reviewed: 2026-10-16, Asia/Tehran. All documented improvement packages now use one permanent sequence, starting at **R1**.

## Current position

| State | Position |
|---|---|
| Published runtime | Stable [1.7.0](https://github.com/pooyahayati/Vibe-Coding-Skill/releases/tag/v1.7.0), release commit `e556f0a1b41b43c6001d03739905001249be574d`. |
| Local installation | Active **1.7.0**, verified on 2026-10-16. All 81 installed files match the published ZIP byte-for-byte; offline installation check passed without failures or warnings. Previous installation retained as a backup outside skill discovery. |
| Review baseline | Main `1204b41fced7cb144721bebc90a5ec03d84dad50`, runtime 1.7.0; inspected source and bounded reproductions of selection disagreement and repeated unrelated inventory checks. |
| Overall progress | **R1-R32 complete; R33 accepted locally; R34 next.** The counts track packages, not quality or coverage. |
| Current phase | R33 scoped source and extracted-package acceptance passed on `codex/r33-r34`; merge pending. |
| Next action | Implement R34's separated required preparation and bounded periodic inventory. |
| Next unallocated ID | **R35**. Continue the same sequence for later improvements. |
| Delivery state | R33-R34 implementation, merge, release and local update are authorized. Runtime acceptance and new delivery remain pending; latest verified delivery is 1.7.0 below. |
| Blockers / limits | No known planning blocker. Runtime acceptance is pending. Legacy or unverifiable assignment bindings retain their update guard; project speed gains remain unmeasured. |

## Current cycle: R33-R34

**R33, first / high priority:** Make task entry and specialist preparation use the same current inspection, risk and domain-effect assessment. Preserve guidance-only handling for verified mechanical edits; incomplete inspection must not become complete by default. [Scope and acceptance](docs/improvement-implementation-plan.md#r33).

**R34, second / high priority:** Separate required task preparation from periodic checks of unrelated installed specialists. Bound retries of unrelated failures without weakening current-source checks before use, compatibility or active-assignment safeguards. [Scope and acceptance](docs/improvement-implementation-plan.md#r34).

Implement sequentially: R33 first establishes consistent required-specialist selection; R34 then changes preparation scheduling around that selection. R34 has no separate feature dependency, but shares preparation code and follows R33 acceptance. Neither package authorizes a new workflow framework, broad instruction rewrite or testing-policy expansion.

## Roadmap register

The register counts documented implementation packages and approved follow-ups in their original execution order. Priority themes, audit findings, verification subtasks and release actions are not additional stages. The delivery column identifies the release record covering completion; it does not claim every package first appeared in that release.

Legacy aliases explain old conversations, PRs and technical references. In particular, the old 1.3.1-cycle R1-R4 are now **R11-R14**. Earlier baseline releases are context, not invented roadmap stages.

| ID | Legacy alias | Work / retained details | Status | Delivery / evidence |
|---|---|---|---|---|
| R1 | P0 | [Shared formats, trust limits and migration policy](docs/archive/improvement-roadmap-through-1.4.0.md#r1) | **Complete** | `1.3.0` / [PR #62](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/62) |
| R2 | B1 | [Observable behavior contract](docs/archive/improvement-roadmap-through-1.4.0.md#r2) | **Complete** | `1.3.0` / [PR #63](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/63) |
| R3 | B2 | [Behavior and acceptance propagation](docs/archive/improvement-roadmap-through-1.4.0.md#r3) | **Complete** | `1.3.0` / [PR #64](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/64) |
| R4 | E1 | [Bounded execution-receipt collector](docs/archive/improvement-roadmap-through-1.4.0.md#r4) | **Complete** | `1.3.0` / [PR #65](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/65) |
| R5 | E2 | [Receipt-backed completion validation](docs/archive/improvement-roadmap-through-1.4.0.md#r5) | **Complete** | `1.3.0` / [PR #66](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/66) |
| R6 | S1 | [Specialist instruction compatibility](docs/archive/improvement-roadmap-through-1.4.0.md#r6) | **Complete** | `1.3.0` / [PR #67](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/67) |
| R7 | S2 | [Specialist returns and Head acceptance](docs/archive/improvement-roadmap-through-1.4.0.md#r7) | **Complete** | `1.3.0` / [PR #68](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/68) |
| R8 | I1 | [Portable workflow integration](docs/archive/improvement-roadmap-through-1.4.0.md#r8) | **Complete** | `1.3.0` / [PR #72](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/72) |
| R9 | D1 | [User and maintainer guidance](docs/archive/improvement-roadmap-through-1.4.0.md#r9) | **Complete** | `1.3.0` / [PR #73](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/73) |
| R10 | F1 (feedback) | [Skill feedback reporting](docs/archive/improvement-roadmap-through-1.4.0.md#r10) | **Complete** | `1.3.0` / [PR #73](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/73) |
| R11 | R1 (1.3.1 cycle) | [Retained contract and completion controls](docs/archive/improvement-roadmap-through-1.4.0.md#r11) | **Complete** | `1.3.1` / [PR #77](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/77) |
| R12 | R2 (1.3.1 cycle) | [Bounded platform discovery](docs/archive/improvement-roadmap-through-1.4.0.md#r12) | **Complete** | `1.3.1` / [PR #78](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/78) |
| R13 | R3 (1.3.1 cycle) | [Consistent project-root ownership](docs/archive/improvement-roadmap-through-1.4.0.md#r13) | **Complete** | `1.3.1` / [PR #79](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/79) |
| R14 | R4 (1.3.1 cycle) | [Accurate operational validation guidance](docs/archive/improvement-roadmap-through-1.4.0.md#r14) | **Complete** | `1.3.1` / [PR #80](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/80) |
| R15 | Unnumbered 1.4.0 follow-up | [Native security and Trivy publication gate](docs/archive/improvement-roadmap-through-1.4.0.md#r15) | **Complete** | `1.4.0` / [PR #85](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/85) |
| R16 | Unnumbered 1.4.0 follow-up | [Document/runtime and excluded-domain routing](docs/archive/improvement-roadmap-through-1.4.0.md#r16) | **Complete** | `1.4.0` / [PR #85](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/85) |
| R17 | Unnumbered 1.4.0 follow-up | [Product installation and local runtime](docs/archive/improvement-roadmap-through-1.4.0.md#r17) | **Complete** | `1.4.0` / [PR #85](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/85) |
| R18 | A1 | [Retained-state and contract continuity](docs/archive/improvement-roadmap-through-1.5.0.md#r18) | **Complete** | `1.5.0` / [PR #90](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/90) |
| R19 | A2 | [Reliable routing and graph inputs](docs/archive/improvement-roadmap-through-1.5.0.md#r19) | **Complete** | `1.5.0` / [PR #91](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/91) |
| R20 | A3 | [Version-bound dependency decisions](docs/archive/improvement-roadmap-through-1.5.0.md#r20) | **Complete** | `1.5.0` / [PR #92](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/92) |
| R21 | A4 | [WordPress command output integrity](docs/archive/improvement-roadmap-through-1.5.0.md#r21) | **Complete** | `1.5.0` / [PR #93](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/93) |
| R22 | A5 | [Stage-aware integration controls](docs/archive/improvement-roadmap-through-1.5.0.md#r22) | **Complete** | `1.5.0` / [PR #94](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/94) |
| R23 | T1 | [Risk grounded in actual change](docs/archive/improvement-roadmap-through-1.6.0.md#r23) | **Complete** | `1.6.0` / [PR #100](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/100) |
| R24 | T2 | [Lightweight specialist participation](docs/archive/improvement-roadmap-through-1.6.0.md#r24) | **Complete** | `1.6.0` / [PR #100](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/100) |
| R25 | T3 | [Outcome- and stage-based verification](docs/archive/improvement-roadmap-through-1.6.0.md#r25) | **Complete** | `1.6.0` / [PR #100](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/100) |
| R26 | T4 | [Bounded execution diagnostics](docs/archive/improvement-roadmap-through-1.6.0.md#r26) | **Complete** | `1.6.0` / [PR #100](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/100) |
| R27 | T5 | [Change-aware CI and release checks](docs/archive/improvement-roadmap-through-1.6.0.md#r27) | **Complete** | `1.6.0` / [PR #100](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/100) |
| R28 | H1 | [Same-contract specialist reassessment](docs/archive/improvement-roadmap-through-1.6.1.md#r28) | **Complete** | `1.6.1` / [PR #102](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/102) |
| R29 | H2 | [Dynamic regression-test dependencies](docs/archive/improvement-roadmap-through-1.6.1.md#r29) | **Complete** | `1.6.1` / [PR #102](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/102) |
| R30 | H3 | [Verified release recovery](docs/archive/improvement-roadmap-through-1.6.1.md#r30) | **Complete** | `1.6.1` / [PR #102](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/102) |
| R31 | W1 (planning draft) | [Effect-based specialist participation](docs/improvement-implementation-plan.md#r31) | **Complete** | `1.7.0` / [PR #104](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/104); scoped selection, extracted route and full hosted checks passed. |
| R32 | W2 (planning draft) | [Assignment-isolated skill updates](docs/improvement-implementation-plan.md#r32) | **Complete** | `1.7.0` / [PR #104](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/104); two-project continuation/migration, retained history, interruption protection, cleanup and extracted-package checks passed. |
| R33 | None | [Consistent inspected specialist selection](docs/improvement-implementation-plan.md#r33) | **Accepted locally** | Existing specialist/routing suites and affected extracted-package route passed; merge pending. |
| R34 | None | [Bounded periodic specialist inventory](docs/improvement-implementation-plan.md#r34) | **Planned - second** | Scope approved; queued after R33 acceptance. No runtime acceptance or delivery claimed. |

## Numbering policy

- Append the next integer after the highest allocated ID. Never restart at R1, change the prefix for a new cycle or reuse an allocated number.
- Retain completed, withdrawn or superseded entries with their actual state and evidence. A changed title, release or priority does not change the ID.
- Use the same ID in scope, dependencies, acceptance, progress updates and future PR descriptions. Historical Git commits, release/PR titles, finding IDs and runtime/schema/test identifiers stay unchanged; the legacy-alias column supplies the mapping.
- Keep current status only here. The implementation plan defines scope and acceptance; archives retain the original outcomes with normalized roadmap labels and compatible heading anchors.

## Scope and execution rules

- Current authorization covers sequential R33-R34 implementation, commit, push, merge, new-version publication and local Head installation. Preserve real assignments and unrelated specialist installations; their closure/update is not part of this request.
- Work on one package at a time. Record its branch/PR, relevant checks, acceptance, blocker and next action at meaningful transitions.
- Preserve Head authority, the sole UI/UX specialist, risk floors, required findings, scoped evidence freshness and current-source checks for new tasks.
- Reuse existing preparation caching, test selection and valid evidence. Add only meaningful missing regressions; no test-count target, coverage quota, model evaluation or new framework.
- During Build, run affected checks. Keep existing integration/publication gates, including native Trivy; do not repeat full suites after each edit.
- During implementation, synchronize changed canonical runtime resources with the portable mirror and check the affected extracted route.
- **Complete** requires accepted behavior and merged implementation. Publication and local installation remain separate outcomes. Historical permissions do not authorize a new cycle.

## Deferred proposals

Broad instruction slimming is not a separate stage: R33 may clarify only the task-entry and conditional-reference instructions needed for its correction. General testing-policy changes still need evidence of unnecessary execution from existing receipts; broader observability needs a concrete operational requirement. Neither is allocated in R33-R34. Do not add a routing cache, background service, model evaluation or test-count target.

## Current acceptance evidence

| Package | Verified locally |
|---|---|
| R33 | 98 existing specialist/routing tests passed, including the extended manager/router/planner agreement case for readable/missing source, changed effects and explicit selection. The affected extracted-package route passed, including the same manager-entry scenario and existing preparation reuse. Structure and portable mirror checks passed. |

These are bounded mechanism checks, not a project-speed measurement. R34, integration, release and local activation evidence remain pending.

## Retained local acceptance evidence: R31-R32

| Area | Verified result |
|---|---|
| R31 selection | 34 specialist tests and 64 context-routing tests passed, including preserved versus changed/unknown RTL/responsive effects, risk floors, explicit assignments and router/planner agreement. |
| R32 state and execution | 23 handoff tests passed. The added temporary-installation scenarios exercise old/new resources across two projects, actual retained-interpreter review/resume, explicit migration, findings/history, stale evidence, interrupted binding/migration, damaged resources and conservative cleanup. Relevant cases were rerun after final edits. |
| Recovery and package | Two existing recovery tests, three manifest/dependency-selection checks and two affected extracted-ZIP routes passed. Package construction included offline installation verification. Canonical runtime mirror: 79 files. |
| Policy and consistency | All 16 deterministic risk/policy scenarios passed; skill structure, local links, mirror and diff checks passed. Purity has no forbidden files; only the pre-existing optional local-exclude setup warning remains. |

These are local mechanism checks, not model evaluations or measurements of project speed. Implementation used temporary installations. Analysis used inspected source and existing tests; no new Graphify freshness claim is made. Hosted delivery and the authorized local update are verified separately below.

## Verified delivery: 1.7.0

All release evidence below belongs to `e556f0a1b41b43c6001d03739905001249be574d`; subsequent tracker-only commits do not change the immutable release target.

| Outcome | Evidence |
|---|---|
| Full hosted baseline | [Validate Skill](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/38901047295), [four platform jobs](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/38901047180), [repository validation](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/38901047358), [Skill specification](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/38901047429), [tool contracts](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/38901047396) and [WordPress artifact](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/38901047177) passed. Collected schema-2 readiness reports PASS with full scope. |
| Publication | [Release workflow, attempt 2](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/38901339748/attempts/2) passed readiness, native Trivy, extracted-package verification and publication. The first attempt stopped while rereading the new draft; the existing bounded recovery completed the same draft without changing its tag or replacing assets. |
| Consumer package | Published stable tag resolves to the release commit. Downloaded ZIP/checksum verified; all 81 files match canonical release resources. ZIP SHA-256: `7d362e60b897cdab14332e5b58459fbdc6d98fec3eaccd8fa1be8192e072e91b`. |
| Local activation | Managed Head update to `v1.7.0` completed with backup/provenance. Installed contents match the downloaded ZIP; installed offline check PASS, no failures or warnings. No unrelated specialist was updated and no real assignment was closed. |

## Retained planning evidence

Before implementation, the numbering-only change passed consecutive unique R1-R32 numbering and 195 local links/anchors. All 75 archival GitHub evidence references, 48 delivery-digest occurrences and 28 changed historical heading anchors were preserved. Its structure, purity and unchanged runtime mirror checks passed. Runtime implementation evidence is recorded separately above.

This is a maintained tracker, not an automatic monitor. See [contributor rules](CONTRIBUTING.md#roadmap-progress).
