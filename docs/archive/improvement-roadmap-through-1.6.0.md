# Roadmap Archive through 1.6.0

Roadmap IDs were normalized on 2026-10-16 to the permanent R sequence. See the [canonical register](../../ROADMAP.md#roadmap-register) for legacy aliases. Recorded outcomes, evidence and delivery identities are unchanged; old heading anchors remain available. Finding IDs and runtime/schema identifiers retain their separate meaning.

Archived on 2026-10-16 after R23-R27 shipped in 1.6.0. The status, approval, next-action and concern statements below are historical snapshots. The partial-release concern is superseded by current F3/R30. Use the [current roadmap](../../ROADMAP.md) and [implementation plan](../improvement-implementation-plan.md) for active work.

Canonical current status. Reviewed: 2026-10-16, Asia/Tehran. This cycle addresses unnecessary verification and coordination overhead while preserving evidence for real risks.

## Current position

| State | Position |
|---|---|
| Published runtime | Stable [1.6.0](https://github.com/pooyahayati/Vibe-Coding-Skill/releases/tag/v1.6.0); release commit `c23f9ae97fd14a0433ddf1a4d12e5ec2499ba339`. |
| Local installation | `1.6.0`, verified on 2026-10-16 at `~/.codex/skills/vibe-coding-skill`. All 80 files match the published ZIP and recorded source; offline install check PASS with no warnings/failures. Previous `1.5.0` preserved outside active skills for rollback. |
| Audit baseline | Main `e75a8cae9f27c3e5f6305fb5e14523ed9fe06401`; targeted code tracing, in-memory reproductions and prior CI-run evidence. No full-suite or live-agent benchmark claim. |
| Current phase | **R23-R27 delivered in 1.6.0.** [PR #100](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/100) merged all five packages and the release metadata. |
| Scope | Five approved corrections: actual-change risk, lightweight specialist participation, stage-aware verification/completion, execution diagnostics, and selective CI. |
| Next action | No remaining approved implementation or delivery work in this cycle. Reopen only for a confirmed issue or a newly approved objective. |
| Progress | **5/5 merged, released and installed locally.** |
| Blockers / delivery limits | No delivery blocker. Product latency and improvement percentages remain unmeasured; passing fixtures do not guarantee every agent's delivery quality. |
| Publication evidence | All six baseline workflows passed on the exact release commit, including the four OS/Python combinations. [Release run](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/38809463454) enforced readiness, native Trivy and the exact portable artifact before publication. |
| Artifact evidence | `Vibe-Coding-Skill-1.6.0.zip`: 80 files, 260354 bytes; SHA-256 `0e3f0c15c16791c3014b565c636148dc47fd40f7bed032980d855beb72d02b30`. Downloaded checksum, tagged source, staged installer and active installation agree. |
| Preparation | R23/R24 mechanisms reproduced against main `950a40a3570a475a58a911c29812d8d43f89707a`; R25's quota failure reproduced in declared and actual receipt completion before correction. Local continuation before prior delivery was explicitly requested; the complete delivery chain is now authorized. |
| R23 evidence | Focused classifier, router/planner, contract and receipt-binding regressions; extracted-ZIP capture/handoff/resume/planning route including build/offline install-check; structural and portable-mirror checks. The Head still verifies scope semantics; no live-agent performance claim. |
| R24 evidence | Existing selection/compatibility, handoff and router/planner regressions; paired mechanical/material routing; stubbed preparation proves one Head/specialist resolution each and no duplicate resolution at assignment. Changed scope/resources/provenance/controls/assessment or due inventory invalidate reuse. Extracted-ZIP router/planner and prepare/assign entrypoints passed with offline installation checks. Structural/mirror checks passed; no live download, host installation or model evaluation. |
| R25 evidence | Focused completion, receipt, behavior-contract and risk regressions passed, including one sufficient high-risk check, same-family evidence, missing explicit review, failed/stale/altered receipts, legacy/manual routes and retained commitments. The extracted-ZIP route reuses valid evidence across Build/Verify/Review, rejects expanded publication claims and schema downgrade, and rechecks stale inputs on resume. Structural/mirror checks passed. This proves fixture behavior, not measured project speed or release readiness. |
| R26 evidence | Missing diagnostics reproduced before correction. Focused collector checks passed for original-attempt failure, separate/verbose/binary streams, sensitive-output suppression, read/storage errors, timeout/tree cleanup and bounded inherited-pipe draining. Receipt checks reject altered/missing referenced logs while retaining no-log compatibility. The extracted-ZIP route exposes its original assertion failure, supports CLI suppression and retains completion/state safeguards. Final cross-platform release checks also passed. |
| R27 evidence | Focused selector/readiness/workflow and extracted-package checks passed, followed by complete PR and exact-merge-commit CI. The platform-result step rejects failed/cancelled/missing selected work; release collection verified full-run scope. Full integration caught and corrected a missing required-reference entry for the already-packaged execution-receipts guide. Read-only GitHub inspection found no main protection, branch rules or rulesets. |

## Completed cycle: proportionate verification R23-R27

<a id="completed-cycle-proportionate-verification-t1-t5"></a>

The approved sequence was **R23 -> R24 -> R25 -> R26 -> R27**, implemented locally and delivered together in PR #100. Detailed evidence, components and acceptance criteria remain in the [implementation plan](improvement-plan-through-1.6.0.md#confirmed-audit-findings).

| Order | Package | Intended result | Priority | Dependency | Status |
|---|---|---|---|---|---|
| 1 | <a id="r23"></a>[R23: Risk grounded in actual change](improvement-plan-through-1.6.0.md#r23-risk-grounded-in-actual-change) | Documentation/comments do not acquire sensitive-operation controls solely from words or paths; real sensitive changes retain their risk floor. | Very high | None | **Complete — 1.6.0 / PR #100** |
| 2 | <a id="r24"></a>[R24: Lightweight specialist participation](improvement-plan-through-1.6.0.md#r24-lightweight-specialist-participation) | Mechanical edits reuse accepted guidance; meaningful specialist work retains scoped acceptance; same-assignment preflight is reused when valid. | High | R23 risk semantics | **Complete — 1.6.0 / PR #100** |
| 3 | <a id="r25"></a>[R25: Outcome- and stage-based verification](improvement-plan-through-1.6.0.md#r25-outcome--and-stage-based-verification) | Required checks follow outcomes, risks and delivery stage; a fixed evidence-family quota does not manufacture extra work. | High | R23/R24 scope and participation rules | **Complete — 1.6.0 / PR #100** |
| 4 | <a id="r26"></a>[R26: Bounded execution diagnostics](improvement-plan-through-1.6.0.md#r26-bounded-execution-diagnostics) | One failed execution provides usable local diagnostics without another run merely to recover its output. | Medium | R25 evidence contract; reuse existing receipt format where possible | **Complete — 1.6.0 / PR #100** |
| 5 | <a id="r27"></a>[R27: Change-aware CI and release checks](improvement-plan-through-1.6.0.md#r27-change-aware-ci-and-release-checks) | Documentation, affected runtime changes and publication get appropriate checks; overlapping branch/PR runs are removed. | Medium | Follow R26; no runtime dependency on it | **Complete — 1.6.0 / PR #100** |

## Execution and completion rules

- At package start, mark only that row **In progress** and record its branch/PR and next action. Reconfirm the affected reproduction against current source.
- Choose the smallest relevant checks. Reuse sufficient current evidence; broaden only for changed impact, a failure or an uncovered material risk. Follow the change-aware CI and full publication gates in CONTRIBUTING.md.
- Add or adjust regressions for actual uncovered behavior, including unnecessary escalation and missed real risk. No test-count target, fixed coverage quota, new test framework, model evaluation or new scanner.
- Keep Head ownership, the sole UI/UX specialist, current-source policy, required findings, truthful manual/collected evidence and scoped freshness. Retain native Trivy before publication and exact-artifact installation checks where applicable.
- **Complete** requires accepted behavior and merged implementation, with PR/commit and relevant evidence. A tested local fix or successful command alone is not completion. For partial/blocked work, name the remaining criterion or blocker and resolving action.
- Synchronize changed runtime resources with the portable mirror. Shared format/policy changes need explicit compatibility and retained-task reconciliation; do not silently discard obligations or reuse stale evidence.
- Release and local installation remain separately authorized and verified delivery steps after implementation.

## Delivered history

R18-R22 and its seven findings remain closed and shipped in `1.5.0`; R23-R27 is complete in `1.6.0` with the delivery evidence above.

| History | Retained record |
|---|---|
| R18-R22 specifications, reproductions and acceptance | [Implementation archive through 1.5.0](improvement-plan-through-1.5.0.md) |
| Merges, checks, release hashes and installation snapshots | [Roadmap archive through 1.5.0](improvement-roadmap-through-1.5.0.md) |
| R1-R17: initial scope, hardening and delivery follow-ups | [Earlier roadmap](improvement-roadmap-through-1.4.0.md) and [implementation archive](improvement-plan-through-1.4.0.md) |

Historical dates, counts and installation statements are snapshots, not current pending work. The earlier partial-release retry concern remains unconfirmed and outside this cycle.

## How progress stays current

Maintain status, blockers, branch/PR, merge evidence and the next action only here. Keep implementation scope and acceptance in the linked plan; archive closed detail instead of adding an execution diary. Update on meaningful transitions, not every command. Use **Not started**, **In progress**, **Blocked**, **Complete**. This file is maintained documentation, not an automatic monitor. See [contributor rules](../../CONTRIBUTING.md#roadmap-progress).
