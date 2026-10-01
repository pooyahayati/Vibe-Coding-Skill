# Improvement Roadmap

Status: P0/B1/B2 complete; further implementation is on hold at the user's request. This is the canonical improvement-progress record.
Baseline: version `1.1.0`; repository main commit `9e0ca5108567f38a66376883613fdcaff6616de0`.
Last reviewed: 2026-10-02, Asia/Tehran. Detailed work: [Implementation plan](docs/improvement-implementation-plan.md).

## Current position

- **Current phase:** Phase 1 complete; no later package has started.
- **Completed in this improvement cycle:** roadmap/planning, P0 shared contracts, B1 behavior guidance and B2 behavior/acceptance propagation.
- **Implementation progress:** 3 of 9 work packages complete. B2's completion update takes effect with the merge of PR #64. This counts work packages, not software quality or test coverage.
- **Next action:** wait for the user's instruction before starting another package. E1 remains the next planned package, Not started.
- **Blockers:** none identified; receipt collection and specialist acceptance remain unimplemented.
- **Next release:** version/date not assigned; publication and installation remain separate delivery states.

## Completed baseline

- Version `1.1.0` published with the eight-stage Head lifecycle and four scoped specialists. [Release](https://github.com/pooyahayati/Vibe-Coding-Skill/releases/tag/v1.1.0), [implementation PR #59](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/59).
- README project-size/risk tables restored, Start section removed and full author attribution moved to the end. [Merged PR #60](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/60).
- The three next improvements and their dependency order are documented here and in the implementation plan. These are planned improvements, not delivered runtime capabilities.

## Work-package tracker

| ID | Phase | Work | Status | Implementation evidence |
|---|---|---|---|---|
| P0 | 0 | Shared formats, trust limits and compatibility/migration policy. | Complete | [Contract design](references/shared-improvement-contracts.md); [merged PR #62](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/62), merge `a3e58725133b282ef60cc76066493deb7d9cf0c8`. Relevant contract/package checks passed. |
| B1 | 1 | Short observable behavior contract. | Complete | [Behavior guidance](references/operating-model.md#observable-behavior-contract); [merged PR #63](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/63), merge `ed8bb85f2b2db899ba1578d1333f6af1198b73d7`. Relevant checks passed. |
| B2 | 1 | Behavior/acceptance propagation into plans and handoffs. | Complete | [Plan binding](references/context-routing-and-execution.md#retained-behavior-in-a-plan-b2), [handoff/state](references/project-state-automation.md#preserve-task-behavior-and-useful-delivery-details-b2), [implementation PR #64](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/64). Relevant propagation/regression/package checks passed; this completion update takes effect when merged. |
| E1 | 2 | Bounded execution-receipt collector. | Not started | None yet; depends on P0 and B1. |
| E2 | 2 | Completion validation against actual receipts. | Not started | None yet; depends on B2 and E1. |
| S1 | 3 | Compatibility assessment for changed specialist instructions. | Not started | None yet; depends on P0 and E2. |
| S2 | 3 | Stage-specific specialist return and Head acceptance. | Not started | None yet; depends on B2, E2 and S1. |
| I1 | 4 | Affected-route regressions and portable-package integration. | Not started | None yet; depends on B2, E2 and S2. |
| D1 | 4 | Concise user/maintainer documentation reflecting implementation. | Not started | None yet; depends on I1. |

## How progress stays current

This file is maintained in Git; it is not an automatic live monitor. Update it when a roadmap package starts, a blocker changes, implementation is verified/merged, or a release is delivered. Use the same stable package IDs in implementation PRs and link the relevant PR/commit and concise verification evidence here. Update the implementation plan only when scope, dependencies or acceptance decisions change.

Statuses: **Not started**, **In progress**, **Blocked**, **Complete**. Opening a PR or writing code does not make a package Complete. Completion requires its acceptance conditions, relevant verification and merged implementation; a completion update proposed in that implementation PR takes effect when merged. Track release/deployment/local-installation separately when they are part of the objective.

Phase status and the completed count must agree with the work-package tracker. Keep the current position and next action accurate; do not replace the tracker with a growing diary or an unsupported percentage. A blocked item must state the cause and next resolving action. [Contributor update rule](CONTRIBUTING.md#roadmap-progress).

## Outcome

Improve the delivered software, not the volume of code, instructions or tests. A non-programmer should receive the intended behavior, supported by relevant execution evidence, with specialist work integrated under one accountable engineering Head.

## Three priorities

| Impact priority | Improvement | Current gap | Observable success |
|---|---|---|---|
| 1 | Execution-backed completion | Completion validates declared results and provenance, but does not independently establish that a referenced command ran or an artifact matches the tested revision. | An unsuccessful, missing or stale required execution receipt cannot justify completion. An authorized real workflow supplies evidence for the intended behavior. |
| 2 | Specialist compatibility and acceptance | Package identity/resources and written authority rules exist; update behavior and actual task returns still need a bounded acceptance decision. | Changed instructions and task output are reconciled with the Head contract, platform invariants and affected shared contracts before use/integration. |
| 3 | Observable user behavior | Acceptance criteria exist, but their practical quality depends on interpretation and they are not consistently carried through all stages. | One short scenario connects user intent, observable result, applicable failure behavior and acceptance evidence without making the user design the implementation. |

The impact ranking is not the implementation order. Define behavior first so execution receipts and specialist acceptance use the same target.

## Delivery sequence

| Phase | Status | Work | Owner | Deliverable | Exit condition | Dependency |
|---|---|---|---|---|---|---|
| 0 | Complete | Set shared contracts and compatibility rules. | Head / maintainer. | [P0 design](references/shared-improvement-contracts.md): small behavior, receipt and specialist-return formats; policy for legacy reports and acceptance snapshots. | Minimal formats, trust limits and migration specified; relevant checks passed in PR #62. Runtime delivery remains later work. | Existing source inspection. |
| 1 | Complete | Carry the user scenario through Define, Plan, Build and Verify. | Head; relevant specialist contributes domain detail. | B1 guidance and B2 linked acceptance IDs with state/handoff/resume propagation. | Scope and observable expectations survive planning and handoff; no blanket extra approval. Completion takes effect with PR #64's merge. | Phase 0. |
| 2 | Not started | Record real execution and validate required receipts at completion. | Head and local tooling. | Bounded evidence collector and completion integration. | Failed/missing/stale receipts and mismatched artifacts do not qualify; sufficient evidence is reused. | Phase 1. |
| 3 | Not started | Accept specialist updates and task output against the shared contracts. | Head accepts; selected specialist supplies domain work. | Update-change assessment and stage-specific acceptance record. | Required conflicts are resolved or the affected workflow remains blocked; no standalone specialist lifecycle. | Phases 1 and 2. |
| 4 | Not started | Integrate, document and prepare delivery. | Head / maintainer. | Focused regression evidence, synchronized portable package, installation evidence and user-facing examples. | Changed behavior passes relevant checks; documentation matches runtime and risk routes stay proportionate. | Phases 1-3. |

Release, merge and local installation are separate delivery actions. A version number is chosen after compatibility review; no release date or publication is implied by this plan.

## Application by project route

| Route | Behavior contract | Execution evidence | Specialist controls |
|---|---|---|---|
| Tiny/local change | Reuse a concise acceptance statement; no new project document. | Relevant visual/document/static check may be sufficient; no forced new automated tests. | No specialist unless the affected domain actually requires one. |
| Small product or bounded feature | One useful user workflow and material failure behavior. | Cheapest sufficient check of changed behavior. | One scoped assignment/return only where needed. |
| Medium product | Contracts per affected vertical slice and meaningful integration boundary. | Relevant unit/component/contract/integration evidence; reuse existing coverage. | Head reconciles affected producer/consumer obligations. |
| Large or cross-boundary change | Retain ownership, protected invariants and confirmed shared contracts. | Revision-bound integration and relevant security/data/recovery evidence. | Explicit writer boundaries and resolved cross-domain findings. |
| WordPress delivery | Same routes plus permission, lifecycle/data-retention and compatibility expectations. | Test the exact installable ZIP; data preservation needs a seeded-data assertion when affected. | Specialists retain WordPress/WooCommerce invariants and do not introduce an unrelated stack. |

Project size never substitutes for task risk. Failure scenarios are added only when they matter to the changed behavior.

## Constraints

- Keep the existing eight-stage lifecycle and the Head's final authority.
- Retain the sole UI/UX specialist and the three already registered specialists; do not add an external repository or another orchestration layer.
- Keep latest-stable resolution, the no-release default-branch exception, and revision provenance. No fixed specialist pins or hot replacement during an assignment.
- Do not silently introduce an offline/old-version fallback: freshness policy remains unchanged in this improvement scope.
- Keep runtime receipts outside product source control; meaningful requirements and product tests remain legitimate project files.
- Use existing authorization. Plans, receipts and assignments never grant deployment, destructive-operation or host permissions.
- No model evaluations, provider API keys, fixed test counts, coverage quotas or repeated unrelated full-suite runs.
- Store detailed contracts in relevant references; keep `SKILL.md` and README summaries short and non-duplicative.

## Evidence and limits

The baseline gaps are based on source inspection, including `completion_gate.py`, `specialist_manager.py`, `execution_plan.py` and the operating references. They are not a claim that a produced application was observed to fail.

A command receipt can show the recorded command/result and detect later mismatches. It cannot prove that the selected check tests the right requirement, prevent a privileged actor from forging local records, or prove every vulnerability absent. Head review and host permissions remain necessary. Semantic compatibility review is an engineering assessment, not an automatic proof from keyword checks.

Measure improvement with affected real workflows: can an intentionally failing/stale result be rejected, can the intended behavior be demonstrated, and can a conflicting specialist return be kept out of integration? Record only observed results; do not promise an error-reduction percentage or a future score.
