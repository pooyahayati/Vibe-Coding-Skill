# Improvement Roadmap

Canonical current status. Reviewed: 2026-10-16, Asia/Tehran. This cycle addresses unnecessary verification and coordination overhead while preserving evidence for real risks.

## Current position

| State | Position |
|---|---|
| Published runtime | Stable [1.5.0](https://github.com/pooyahayati/Vibe-Coding-Skill/releases/tag/v1.5.0); release commit `0509f53d274e63ae47077dfd4656310281f9bd05`. |
| Local installation | `1.5.0`; local VERSION rechecked on 2026-10-15. T1-T5 are source changes; installed runtime is unchanged. |
| Audit baseline | Main `e75a8cae9f27c3e5f6305fb5e14523ed9fe06401`; targeted code tracing, in-memory reproductions and prior CI-run evidence. No full-suite or live-agent benchmark claim. |
| Current phase | **T1-T5 integration and 1.6.0 release preparation** on `codex/t5-change-aware-ci`. The user authorized commit, merge, publication and local installation on 2026-10-16. |
| Scope | Five approved corrections: actual-change risk, lightweight specialist participation, stage-aware verification/completion, execution diagnostics, and selective CI. |
| Next action | Submit the combined implementation and version metadata, inspect actual CI, merge, publish the exact validated revision and update the local installation from the verified release. |
| Progress | **0/5 merged; T1-T5 implemented locally.** Local implementation does not close a package. |
| Blockers / delivery limits | No approval blocker. Integration, publication and installation evidence are still pending; existing local checks do not establish those outcomes. Product latency and improvement percentages are unmeasured. |
| Preparation | T1/T2 mechanisms reproduced against main `950a40a3570a475a58a911c29812d8d43f89707a`; T3's quota failure reproduced in declared and actual receipt completion before correction. Local continuation before prior delivery was explicitly requested; the complete delivery chain is now authorized. |
| T1 evidence | Focused classifier, router/planner, contract and receipt-binding regressions; extracted-ZIP capture/handoff/resume/planning route including build/offline install-check; structural and portable-mirror checks. The Head still verifies scope semantics; no live-agent performance claim. |
| T2 evidence | Existing selection/compatibility, handoff and router/planner regressions; paired mechanical/material routing; stubbed preparation proves one Head/specialist resolution each and no duplicate resolution at assignment. Changed scope/resources/provenance/controls/assessment or due inventory invalidate reuse. Extracted-ZIP router/planner and prepare/assign entrypoints passed with offline installation checks. Structural/mirror checks passed; no live download, host installation or model evaluation. |
| T3 evidence | Focused completion, receipt, behavior-contract and risk regressions passed, including one sufficient high-risk check, same-family evidence, missing explicit review, failed/stale/altered receipts, legacy/manual routes and retained commitments. The extracted-ZIP route reuses valid evidence across Build/Verify/Review, rejects expanded publication claims and schema downgrade, and rechecks stale inputs on resume. Structural/mirror checks passed. This proves fixture behavior, not measured project speed or release readiness. |
| T4 evidence | Missing diagnostics reproduced before correction. Focused collector checks passed for original-attempt failure, separate/verbose/binary streams, sensitive-output suppression, read/storage errors, timeout/tree cleanup and bounded inherited-pipe draining. Receipt checks reject altered/missing referenced logs while retaining no-log compatibility. The extracted-ZIP route exposes its original assertion failure, supports CLI suppression and retains completion/state safeguards. Structural/mirror checks passed. Executed locally on Windows; no new cross-platform CI, release, installation or model-evaluation claim. |
| T5 evidence | Eighteen focused selector/readiness/workflow tests and the extracted-package readiness route passed. The actual platform-result step rejects failed/cancelled/missing selected work. Changed Markdown links, structure, portable mirror and diff checks passed; real-source samples select overview, affected-code, instruction and full-version routes. Workflow wiring preserves full-validation markers, exact-revision/latest-attempt collection and the native final-target Trivy gate. Read-only GitHub inspection with admin access found no main protection, branch rules or rulesets. Hosted workflow execution and release remain unverified. |

## Active cycle: proportionate verification T1-T5

Priority combines impact, expected frequency and confidence. Implement **T1 -> T2 -> T3 -> T4 -> T5**, one package at a time. Keep delivery status explicit when the user authorizes local continuation before a prior merge. Detailed evidence, components and acceptance criteria live in the [implementation plan](docs/improvement-implementation-plan.md#confirmed-audit-findings).

| Order | Package | Intended result | Priority | Dependency | Status |
|---|---|---|---|---|---|
| 1 | [T1: Risk grounded in actual change](docs/improvement-implementation-plan.md#t1-risk-grounded-in-actual-change) | Documentation/comments do not acquire sensitive-operation controls solely from words or paths; real sensitive changes retain their risk floor. | Very high | None | **In progress — locally implemented; pending commit/merge** |
| 2 | [T2: Lightweight specialist participation](docs/improvement-implementation-plan.md#t2-lightweight-specialist-participation) | Mechanical edits reuse accepted guidance; meaningful specialist work retains scoped acceptance; same-assignment preflight is reused when valid. | High | T1 risk semantics | **In progress — locally implemented; pending commit/merge** |
| 3 | [T3: Outcome- and stage-based verification](docs/improvement-implementation-plan.md#t3-outcome--and-stage-based-verification) | Required checks follow outcomes, risks and delivery stage; a fixed evidence-family quota does not manufacture extra work. | High | T1/T2 scope and participation rules | **In progress — locally implemented; pending commit/merge** |
| 4 | [T4: Bounded execution diagnostics](docs/improvement-implementation-plan.md#t4-bounded-execution-diagnostics) | One failed execution provides usable local diagnostics without another run merely to recover its output. | Medium | T3 evidence contract; reuse existing receipt format where possible | **In progress — locally implemented; pending commit/merge** |
| 5 | [T5: Change-aware CI and release checks](docs/improvement-implementation-plan.md#t5-change-aware-ci-and-release-checks) | Documentation, affected runtime changes and publication get appropriate checks; overlapping branch/PR runs are removed. | Medium | Follow T4; no runtime dependency on it | **In progress — locally implemented; pending commit/merge** |

## Execution and completion rules

- At package start, mark only that row **In progress** and record its branch/PR and next action. Reconfirm the affected reproduction against current source.
- Choose the smallest relevant checks. Reuse sufficient current evidence; broaden only for changed impact, a failure or an uncovered material risk. Existing required project/CI checks still apply until T5 is implemented.
- Add or adjust regressions for actual uncovered behavior, including unnecessary escalation and missed real risk. No test-count target, fixed coverage quota, new test framework, model evaluation or new scanner.
- Keep Head ownership, the sole UI/UX specialist, current-source policy, required findings, truthful manual/collected evidence and scoped freshness. Retain native Trivy before publication and exact-artifact installation checks where applicable.
- **Complete** requires accepted behavior and merged implementation, with PR/commit and relevant evidence. A tested local fix or successful command alone is not completion. For partial/blocked work, name the remaining criterion or blocker and resolving action.
- Synchronize changed runtime resources with the portable mirror. Shared format/policy changes need explicit compatibility and retained-task reconciliation; do not silently discard obligations or reuse stale evidence.
- Release and local installation remain separate authorized delivery steps after implementation. No new version number is assigned by this plan.

## Delivered history

A1-A5 and its seven findings remain closed and shipped in `1.5.0`; T1-T5 is a separate approved improvement cycle.

| History | Retained record |
|---|---|
| A1-A5 specifications, reproductions and acceptance | [Implementation archive through 1.5.0](docs/archive/improvement-plan-through-1.5.0.md) |
| Merges, checks, release hashes and installation snapshots | [Roadmap archive through 1.5.0](docs/archive/improvement-roadmap-through-1.5.0.md) |
| Earlier B/E/S/I, R1-R4 and delivery follow-ups | [Earlier roadmap](docs/archive/improvement-roadmap-through-1.4.0.md) and [implementation archive](docs/archive/improvement-plan-through-1.4.0.md) |

Historical dates, counts and installation statements are snapshots, not current pending work. The earlier partial-release retry concern remains unconfirmed and outside this cycle.

## How progress stays current

Maintain status, blockers, branch/PR, merge evidence and the next action only here. Keep implementation scope and acceptance in the linked plan; archive closed detail instead of adding an execution diary. Update on meaningful transitions, not every command. Use **Not started**, **In progress**, **Blocked**, **Complete**. This file is maintained documentation, not an automatic monitor. See [contributor rules](CONTRIBUTING.md#roadmap-progress).
