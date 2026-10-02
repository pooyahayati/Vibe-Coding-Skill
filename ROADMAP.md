# Improvement Roadmap

Status: P0/B1/B2/E1/E2/S1/S2 merged; preflight resource-validation fixes shipped in 1.2.0. Literal-path fixes are merged in [PR #71](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/71) and remain unreleased. I1 integration is merged in [PR #72](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/72). D1 documentation is implemented and locally verified; its completion update takes effect with its implementation PR's merge. This is the canonical improvement-progress record.
Baseline: version `1.1.0`; repository main commit `9e0ca5108567f38a66376883613fdcaff6616de0`.
Last reviewed: 2026-10-03, Asia/Tehran. Detailed work: [Implementation plan](docs/improvement-implementation-plan.md).

## Current position

- **Current phase:** Phase 4; I1 is merged and D1 documentation is verified. Phase 4 completion below takes effect with D1's merge.
- **Completed in this improvement cycle:** P0 shared contracts, B1/B2 observable behavior propagation, E1/E2 execution receipts/completion, S1 instruction compatibility, S2 scoped specialist-return/Head acceptance and I1 portable workflow integration; D1 documentation completes the cycle when merged.
- **Implementation progress:** 9 of 9 packages complete after D1's merge; 8 are merged beforehand. This counts work packages, not software quality or test coverage.
- **Next action:** Review/merge D1. This closes the improvement cycle; release/version selection and local installation remain separate authorized delivery actions.
- **Blockers:** none identified by local checks. Required CI/merge status is recorded in D1's implementation PR; an unobserved/pending result is not a pass.
- **Release delivery:** version `1.2.0` is published. Later main-branch corrections and I1 are separate from that release and local installation. [Published release](https://github.com/pooyahayati/Vibe-Coding-Skill/releases/tag/v1.2.0).

## Completed baseline

- Version `1.1.0` published with the eight-stage Head lifecycle and four scoped specialists. [Release](https://github.com/pooyahayati/Vibe-Coding-Skill/releases/tag/v1.1.0), [implementation PR #59](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/59).
- README project-size/risk tables restored, Start section removed and full author attribution moved to the end. [Merged PR #60](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/60).
- The original three improvement priorities and their dependency order are recorded here; the tracker below distinguishes implemented/merged work from release delivery.

## Work-package tracker

| ID | Phase | Work | Status | Implementation evidence |
|---|---|---|---|---|
| P0 | 0 | Shared formats, trust limits and compatibility/migration policy. | Complete | [Contract design](references/shared-improvement-contracts.md); [merged PR #62](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/62), merge `a3e58725133b282ef60cc76066493deb7d9cf0c8`. Relevant contract/package checks passed. |
| B1 | 1 | Short observable behavior contract. | Complete | [Behavior guidance](references/operating-model.md#observable-behavior-contract); [merged PR #63](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/63), merge `ed8bb85f2b2db899ba1578d1333f6af1198b73d7`. Relevant checks passed. |
| B2 | 1 | Behavior/acceptance propagation into plans and handoffs. | Complete | [Plan binding](references/context-routing-and-execution.md#retained-behavior-in-a-plan-b2), [handoff/state](references/project-state-automation.md#preserve-task-behavior-and-useful-delivery-details-b2), [implementation PR #64](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/64). Merged in PR #64; relevant propagation/regression/package checks passed. |
| E1 | 2 | Bounded execution-receipt collector. | Complete | [Local collector](references/execution-and-verification.md#local-execution-receipts-e1); [merged PR #65](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/65), merge `8b849f22f68163821f94a5f9fc3fc6e69dc97446`. Actual success/failure/timeout, scoped-input/artifact binding, unavailable and external-storage checks passed. |
| E2 | 2 | Completion validation against actual receipts. | Complete | [Receipt-backed completion](references/execution-and-verification.md#receipt-backed-completion-e2); [merged PR #66](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/66), merge `4f227116a5ba21f8b413c0532c71667f3c64e453`. Relevant receipt/migration/legacy regressions and package checks passed. |
| S1 | 3 | Compatibility assessment for changed specialist instructions. | Complete | [Instruction compatibility](references/specialist-composition.md#instruction-compatibility-assessment-s1); [merged PR #67](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/67), merge `7e75cdf6c5cee4c532a66e4c565cbff784d71581`. Bound explicit Head assessment/conflict handling and unchanged reuse passed relevant checks. |
| S2 | 3 | Stage-specific specialist return and Head acceptance. | Complete | [S2 handoffs](references/specialist-composition.md#stage-return-and-head-acceptance-s2), [implementation PR #68](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/68). Real changes, receipts, required-finding history, shared-contract decisions, active instructions and completion linkage are implemented. Merged in PR #68; relevant checks passed. |
| I1 | 4 | Affected-route regressions and portable-package integration. | Complete | [Integration evidence](docs/i1-integration-verification.md), [merged PR #72](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/72), merge `512272202f9fc178dd6ec191e4a9f0d0f411b881`; three extracted-ZIP routes passed locally and in the existing Linux/macOS/Windows matrix. |
| D1 | 4 | Concise user/maintainer documentation reflecting implementation. | Complete | [Implementation PR #73](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/73). User/maintainer guidance aligned with runtime. Skill validation, mirror consistency, 63 local links/anchors and preservation of README tables/full author passed; offline install had no failures (optional Trivy warning). Completion takes effect with PR #73's merge. |

## How progress stays current

This file is maintained in Git; it is not an automatic live monitor. Update it when a roadmap package starts, a blocker changes, implementation is verified/merged, or a release is delivered. Use the same stable package IDs in implementation PRs and link the relevant PR/commit and concise verification evidence here. Update the implementation plan only when scope, dependencies or acceptance decisions change.

Statuses: **Not started**, **In progress**, **Blocked**, **Complete**. Opening a PR or writing code does not make a package Complete. Completion requires its acceptance conditions, relevant verification and merged implementation; a completion update proposed in that implementation PR takes effect when merged. Track release/deployment/local-installation separately when they are part of the objective.

Phase status and the completed count must agree with the work-package tracker. Keep the current position and next action accurate; do not replace the tracker with a growing diary or an unsupported percentage. A blocked item must state the cause and next resolving action. [Contributor update rule](CONTRIBUTING.md#roadmap-progress).

## Outcome

Improve the delivered software, not the volume of code, instructions or tests. A non-programmer should receive the intended behavior, supported by relevant execution evidence, with specialist work integrated under one accountable engineering Head.

## Three priorities

| Impact priority | Improvement | Current gap | Observable success |
|---|---|---|---|
| 1 | Execution-backed completion | E1/E2 now validate local command/manual receipts and scoped inputs/artifacts; remote evidence still requires a separately authorized resolver, and the Head must choose meaningful checks. | An unsuccessful, missing or stale required execution receipt cannot justify completion. An authorized real workflow supplies evidence for the intended behavior. |
| 2 | Specialist compatibility and acceptance | S1/S2 now bind explicit Head decisions to current instructions, assigned stage, actual changes and receipts. Semantic sufficiency still needs Head reasoning and later real-project evidence. | Changed instructions and task output are reconciled with the Head contract, platform invariants and affected shared contracts before use/integration. |
| 3 | Observable user behavior | B1/B2 now preserve observable criteria through planning and handoff; the Head must still choose sufficient scenarios and checks. | One short scenario connects user intent, observable result, applicable failure behavior and acceptance evidence without making the user design the implementation. |

The impact ranking is not the implementation order. Define behavior first so execution receipts and specialist acceptance use the same target.

## Delivery sequence

| Phase | Status | Work | Owner | Deliverable | Exit condition | Dependency |
|---|---|---|---|---|---|---|
| 0 | Complete | Set shared contracts and compatibility rules. | Head / maintainer. | [P0 design](references/shared-improvement-contracts.md): small behavior, receipt and specialist-return formats; policy for legacy reports and acceptance snapshots. | Minimal formats, trust limits and migration specified; relevant checks passed in PR #62. Runtime delivery remains later work. | Existing source inspection. |
| 1 | Complete | Carry the user scenario through Define, Plan, Build and Verify. | Head; relevant specialist contributes domain detail. | B1 guidance and B2 linked acceptance IDs with state/handoff/resume propagation. | Scope and observable expectations survive planning and handoff; no blanket extra approval. Merged in PR #64. | Phase 0. |
| 2 | Complete | Record real execution and validate required receipts at completion. | Head and local tooling. | E1 local collection and E2 schema-3 local receipt resolution/manual observation records. | Failed/missing/stale receipts and mismatched artifacts do not qualify; sufficient evidence is reused. Merged in PR #66. | Phase 1. |
| 3 | Complete | Accept specialist updates and task output against the shared contracts. | Head accepts; selected specialist supplies domain work. | S1 instruction compatibility and S2 retained stage returns/separate Head acceptance. Merged in PR #68. | Required conflicts are resolved or the affected workflow remains blocked; no standalone specialist lifecycle. | Phases 1 and 2. |
| 4 | Complete at D1 merge | Integrate, document and prepare delivery. | Head / maintainer. | Focused regression evidence, synchronized portable package, installation evidence and user-facing examples. | Changed behavior passes relevant checks; documentation matches runtime and risk routes stay proportionate. | Phases 1-3. |

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
