# Improvement Roadmap

Canonical current status. Reviewed: 2026-10-15, Asia/Tehran. This cycle addresses unnecessary verification and coordination overhead while preserving evidence for real risks.

## Current position

| State | Position |
|---|---|
| Published runtime | Stable [1.5.0](https://github.com/pooyahayati/Vibe-Coding-Skill/releases/tag/v1.5.0); release commit `0509f53d274e63ae47077dfd4656310281f9bd05`. |
| Local installation | `1.5.0`; local VERSION rechecked on 2026-10-15. This planning update changes no installed runtime. |
| Audit baseline | Main `e75a8cae9f27c3e5f6305fb5e14523ed9fe06401`; targeted code tracing, in-memory reproductions and prior CI-run evidence. No full-suite or live-agent benchmark claim. |
| Current phase | **T1-T5 planned; implementation not started.** Scope and acceptance criteria are ready. |
| Scope | Five approved corrections: actual-change risk, lightweight specialist participation, stage-aware verification/completion, execution diagnostics, and selective CI. |
| Next action | Start **T1**, reproduce the false risk escalation, then implement its bounded correction and focused acceptance checks. |
| Progress | **0/5 implemented and merged; 5 remaining.** Planning does not close a finding. |
| Blockers | None identified for starting T1. Project-specific latency and the percentage of improvement remain unmeasured. |
| Preparation | Roadmap and acceptance plan ready for sequential implementation; no runtime implementation or release selected. |

## Active cycle: proportionate verification T1-T5

Priority combines impact, expected frequency and confidence. Execute **T1 -> T2 -> T3 -> T4 -> T5**, with one package in progress. Detailed evidence, components and acceptance criteria live in the [implementation plan](docs/improvement-implementation-plan.md#confirmed-audit-findings).

| Order | Package | Intended result | Priority | Dependency | Status |
|---|---|---|---|---|---|
| 1 | [T1: Risk grounded in actual change](docs/improvement-implementation-plan.md#t1-risk-grounded-in-actual-change) | Documentation/comments do not acquire sensitive-operation controls solely from words or paths; real sensitive changes retain their risk floor. | Very high | None | **Not started** |
| 2 | [T2: Lightweight specialist participation](docs/improvement-implementation-plan.md#t2-lightweight-specialist-participation) | Mechanical edits reuse accepted guidance; meaningful specialist work retains scoped acceptance; same-assignment preflight is reused when valid. | High | T1 risk semantics | **Not started** |
| 3 | [T3: Outcome- and stage-based verification](docs/improvement-implementation-plan.md#t3-outcome--and-stage-based-verification) | Required checks follow outcomes, risks and delivery stage; a fixed evidence-family quota does not manufacture extra work. | High | T1/T2 scope and participation rules | **Not started** |
| 4 | [T4: Bounded execution diagnostics](docs/improvement-implementation-plan.md#t4-bounded-execution-diagnostics) | One failed execution provides usable local diagnostics without another run merely to recover its output. | Medium | T3 evidence contract; reuse existing receipt format where possible | **Not started** |
| 5 | [T5: Change-aware CI and release checks](docs/improvement-implementation-plan.md#t5-change-aware-ci-and-release-checks) | Documentation, affected runtime changes and publication get appropriate checks; overlapping branch/PR runs are removed. | Medium | Follow T4; no runtime dependency on it | **Not started** |

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
