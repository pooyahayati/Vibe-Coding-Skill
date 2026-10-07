# Improvement Implementation and Acceptance Index

Current progress is maintained only in [ROADMAP.md](../ROADMAP.md). The original nine-package cycle + F1, R1-R4 and the three `1.4.0` follow-ups are delivered. This page locates current mechanisms and acceptance boundaries; it does not reopen closed work or approve a new package.

Closed specifications, dependencies and original design decisions: [implementation-plan archive](archive/improvement-plan-through-1.4.0.md) · [roadmap archive](archive/improvement-roadmap-through-1.4.0.md).

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
