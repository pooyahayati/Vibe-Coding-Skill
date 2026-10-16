# Improvement Roadmap

Canonical current status. Reviewed: 2026-10-16, Asia/Tehran. This cycle addresses three confirmed reliability gaps in 1.6.0, preserving proportionate verification.

## Current position

| State | Position |
|---|---|
| Published runtime | Stable [1.6.0](https://github.com/pooyahayati/Vibe-Coding-Skill/releases/tag/v1.6.0), release commit `c23f9ae97fd14a0433ddf1a4d12e5ec2499ba339`. |
| Local installation | `1.6.0`; the 2026-10-16 audit matched all 80 active files to the published ZIP, with no extra or missing runtime files. |
| Audit baseline | Main `80defe5d8061ea85df7a6c523f7120dc85699807`; code tracing, isolated reproductions and hosted release evidence. |
| Current phase | **H1-H2 accepted locally; H3 in progress.** H1-H3 implementation, acceptance, merge, release and local update are authorized. |
| Approved scope | Same-contract specialist reassessment, dynamic test-dependency selection, and verified release recovery. |
| Next action | Implement **H3** verified release recovery after H1/H2 acceptance. |
| Progress | **2/3 implemented and locally accepted; 0/3 merged.** Branch `codex/1.6.0-audit-roadmap`; H1: 20 handoff tests and the extracted specialist route passed. H2: all six selector tests passed, including the six-module normal/platform mapping. |
| Blockers / limits | No planning blocker identified. Reconfirm each reproduction against current source at implementation start. Project latency and general agent quality remain unmeasured. |
| Delivery baseline | All six required workflows and the native Trivy publication gate passed for 1.6.0. The current release is complete; H3 addresses a recovery defect, not a broken published artifact. [Delivery evidence](docs/archive/improvement-roadmap-through-1.6.0.md#current-position). |

## Current cycle: targeted reliability H1-H3

Execution order: **H1 -> H2 -> H3**. The packages have no technical dependency on each other; this is the priority order. Scope, evidence and acceptance belong in the [implementation plan](docs/improvement-implementation-plan.md#confirmed-audit-findings).

| Order | Package / finding | Required result | Priority | Status |
|---|---|---|---|---|
| 1 | [H1: Same-contract specialist reassessment](docs/improvement-implementation-plan.md#h1-same-contract-specialist-reassessment) / F1 | Fresh evidence can be accepted after an in-scope correction without inventing a contract revision or losing retained findings. | High | **In progress — locally accepted; merge pending** |
| 2 | [H2: Dynamic regression-test dependencies](docs/improvement-implementation-plan.md#h2-dynamic-regression-test-dependencies) / F2 | Runtime changes select their existing dynamically loaded regressions; overview edits retain lightweight checks. | Medium | **In progress — locally accepted; merge pending** |
| 3 | [H3: Verified release recovery](docs/improvement-implementation-plan.md#h3-verified-release-recovery) / F3 | Existing releases qualify only after identity, publication state and assets are verified; incomplete publication has an explicit recovery path. | Medium | **In progress** |

## Execution and completion rules

- Start one package at a time. Mark its row **In progress** and record its implementation branch/PR, evidence, blocker if any, and next action here.
- Reuse existing tests and sufficient current evidence. Add regressions only for the confirmed failure or a necessary preservation check; no test-count target, coverage quota, new framework, scanner or model evaluation.
- During Build, run affected checks. H2/H3 change CI or delivery controls, so their integration/publication must retain the existing full-baseline requirements; do not repeat the full suite after each edit.
- Preserve Head authority, the sole UI/UX specialist, scoped evidence freshness, required findings, current-source policy and native Trivy before publication. A failing receipt or incomplete release must never become a fabricated pass.
- **Complete** requires accepted behavior and merged implementation, linked to the PR/commit and relevant evidence. Audit reproductions, a local fix or a successful command alone do not establish completion.
- Synchronize changed runtime resources with the portable mirror and check the affected extracted route. Preserve existing record compatibility and retained obligations.
- Commit, merge, release and local installation follow existing user authorization. This planning change does not perform implementation or delivery.

## Delivered history

| Completed cycle | Retained record |
|---|---|
| T1-T5: proportionate verification, shipped in 1.6.0 | [Specifications](docs/archive/improvement-plan-through-1.6.0.md) and [merge/release/installation evidence](docs/archive/improvement-roadmap-through-1.6.0.md). |
| A1-A5: seven audit findings, shipped in 1.5.0 | [Specifications](docs/archive/improvement-plan-through-1.5.0.md) and [delivery evidence](docs/archive/improvement-roadmap-through-1.5.0.md). |
| Earlier B/E/S/I, R1-R4 and delivery follow-ups | [Roadmap](docs/archive/improvement-roadmap-through-1.4.0.md) and [implementation history](docs/archive/improvement-plan-through-1.4.0.md). |

Historical dates and next actions are snapshots. The partial-release concern previously marked unconfirmed is now represented by the reproduced F3/H3 finding; 1.6.0 itself remains verified.

## How progress stays current

Maintain current status, blockers, branch/PR, merge evidence and next action only here. Keep scope and acceptance in the implementation plan; archive closed detail. Update on meaningful transitions using **Not started**, **In progress**, **Blocked**, **Complete**. This is maintained documentation, not an automatic monitor. See [contributor rules](CONTRIBUTING.md#roadmap-progress).
