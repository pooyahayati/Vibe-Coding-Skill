# Improvement Roadmap

Status: `R1`-`R4` are complete, merged and delivered in `1.3.1`, with the published package and local installation verified. This hardening cycle is closed. The original nine-package cycle and feedback follow-up shipped in `1.3.0`; their evidence is retained below.
Audit baseline: main commit [`156676d502fae98c5c0b3a9bafdf5497698a062e`](https://github.com/pooyahayati/Vibe-Coding-Skill/commit/156676d502fae98c5c0b3a9bafdf5497698a062e); released runtime `1.3.0`, commit `83fd4f47e60930718a2c9fb5e27fdedb74de2e81`.
Last reviewed: 2026-10-04, Asia/Tehran. This is the canonical progress tracker; [implementation scope and dependencies](docs/improvement-implementation-plan.md#targeted-hardening-cycle-r1-r4) are maintained in the existing implementation plan.

## Current position

- **Current phase:** `R1`-`R4` remain closed and delivered in `1.3.1`. A separate user-authorized security follow-up is implemented and verified, pending review and merge in [PR #83](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/83): native development controls and mandatory local Trivy before publication.
- **Implementation progress:** 4 of 4 hardening packages complete in source. The closed original cycle remains 9 of 9, with feedback F1 tracked separately. Counts describe work packages, not quality or coverage.
- **Next action:** Review and merge the security follow-up in [PR #83](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/83). Release and local replacement remain separate delivery actions. No fifth hardening package or model campaign is implied.
- **Completed order:** `R1` -> `R2` -> `R3` -> `R4`, prioritizing silent weakening of required controls. `R2`-`R4` did not technically depend on `R1`.
- **Blockers:** none for implementation acceptance or the closed hardening cycle. The local host lacks native Trivy and correctly blocks local publication. Actual native scanner and exact-package acceptance passed in the existing tool-contract CI; this does not establish Trivy availability on the local host.
- **Release delivery:** `1.3.1` is published and the maintainer's local installation was replaced and verified against its exact ZIP on 2026-10-04. [Published release](https://github.com/pooyahayati/Vibe-Coding-Skill/releases/tag/v1.3.1).

## Active hardening packages

User-authorized security follow-up (separate from the closed audit cycle): **Verified; pending review and merge** in [PR #83](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/83). Keep native project security controls and make installed native Trivy plus actual local final-artifact scans mandatory before publication. Implementation extends the existing adapter, receipt guidance and release builder; no new scanner/specialist or model evaluation. Acceptance covers missing native tooling, exit-zero findings, failed/invalid/stale reports, scope/version protections, extracted-package execution and the exact ZIP publication gate. All six required workflows passed on implementation head `fc3f258`; [native Trivy acceptance](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/37199221376/job/111427258707) used version `0.75.0` and returned `PASS` for both the fixture and the exact extracted 78-file candidate ZIP. This is candidate evidence, not a new release or local installation. Merge/release/local delivery will be recorded separately.

| ID | Priority | Audit findings | Work | Status | Complexity | Implementation / acceptance evidence |
|---|---|---|---|---|---|---|
| R1 | P1 | Audit F1, F2 | Default new structured completion to receipts and preserve required specialist commitments. | Complete | Medium | Both failures reproduced before correction. Affected contract/receipt/handoff regressions, all 3 extracted-package routes (including offline install), skill validation and mirror consistency passed. Required PR/push checks passed. Merged in [PR #77](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/77), commit [`3f847f4`](https://github.com/pooyahayati/Vibe-Coding-Skill/commit/3f847f4555bf92c75002439ab89beb312dd0f86d). Delivered in `1.3.1`; published-package and local-installation evidence below. |
| R2 | P1 | Audit F3 | Preserve platform discovery for large files and expose incomplete inspection. | Complete | Medium | Large-file platform loss reproduced before correction. Local acceptance verified: 56 routing/planning checks, relevant custom-area regressions, actual read-budget/diagnostic bounds, extracted-package routing (including offline install and plain-CLI warnings), skill validation and mirror consistency. All 6 active PR/push workflow runs passed on final head `99eae82`. Merged in [PR #78](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/78), commit [`a7ebfaf`](https://github.com/pooyahayati/Vibe-Coding-Skill/commit/a7ebfaf1c05b36abaeaa422d715b272c4b46d4c6). Delivered in `1.3.1`; published-package and local-installation evidence below. |
| R3 | P2 | Audit F4 | Use consistent project-root scope semantics in ownership and drift checks. | Complete | Small | Both failures reproduced before correction. 26 affected planning/retained-contract checks, literal and relative-path controls, extracted-package ownership/drift CLI route (including offline install), skill validation and mirror consistency passed. All 6 active PR/push workflow runs passed on final head `127af50`. Merged in [PR #79](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/79), commit [`8c16570`](https://github.com/pooyahayati/Vibe-Coding-Skill/commit/8c1657018a57d3a6ffc512d8e64118d648fffd2b). Delivered in `1.3.1`; published-package and local-installation evidence below. |
| R4 | P2 | Audit F5 | Remove obsolete mandatory benchmark claims and unavailable portable commands. | Complete | Small | Obsolete claims confirmed against actual workflows/gate and portable manifest. Affected links/command targets/help and six-workflow release-policy alignment verified. Skill validation, mirror consistency and portable offline install passed with no failures; only optional missing Trivy warned. No new tests or model execution. All 5 active PR/push workflow runs passed on final head `0f45c18`. Merged in [PR #80](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/80), commit [`4ddc350`](https://github.com/pooyahayati/Vibe-Coding-Skill/commit/4ddc350739871b7690c2c39be05caf03adc5c4a1). Delivered in `1.3.1`; published-package and local-installation evidence below. |

Audit IDs belong to the final audit, not the completed original-cycle package IDs. Audit F1 is distinct from the delivered F1 feedback feature.

## Package specifications

### R1: retained contract and required completion controls

**Why:** Audit F1 showed that a fresh structured task without `--receipt-completion` selects schema 2 and can accept declared results (`PASS` / `reported-met`) without receipts. It correctly leaves `execution_verified` false, but does not enforce the new-task route. Audit F2 showed that removing `specialist_assignment_ids` passes contract comparison and removes the missing-assignment failure before an operation has been created.

**Evidence:** [Workflow default](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/156676d502fae98c5c0b3a9bafdf5497698a062e/scripts/project_state.py#L118-L133), [contract comparison](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/156676d502fae98c5c0b3a9bafdf5497698a062e/scripts/behavior_contract.py#L99-L112) and [required-assignment completion check](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/156676d502fae98c5c0b3a9bafdf5497698a062e/scripts/specialist_handoff.py#L362-L385). Controlled in-memory reproductions exercised the actual functions; these are tooling findings, not an observed application incident.

**Correction / components:** Default new structured tasks to schema 3 in `project_state.py`; keep the supported in-flight legacy route explicit. Preserve required specialist IDs through `behavior_contract.py`, planning, state, handoff/resume and completion. Removal needs the existing Head-reconciled change route with a reason; records do not grant authorization. Retain digest protection for operations already created.

**Acceptance:**

- A fresh structured contract, including `--new-task`, cannot qualify with schema-2 declared evidence merely because an activation flag is omitted.
- Valid retained legacy work remains supported and accurately labeled; an activated receipt workflow cannot downgrade across capture/handoff/resume. Tiny inline/manual work stays proportionate.
- Removing a retained required specialist ID is rejected before replacement unless explicitly reconciled. A required assignment that has not started remains visible as missing at completion.

**Verification:** Extend affected behavior/state, receipt and specialist-handoff regressions with the two confirmed reproductions and positive legacy/reconciliation cases. Reuse existing tests; check retained state across handoff/resume and apply affected package checks when runtime resources change.

### R2: bounded discovery without silent platform loss

**Why:** Audit F3 used identical WordPress headers in a simulated 2 KB and 70 KB `plugin.php`. The larger file lost the WordPress pack while reporting no uncertainty because `safe_text` discards an oversized file entirely.

**Evidence:** [Whole-file rejection and scan bounds](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/156676d502fae98c5c0b3a9bafdf5497698a062e/scripts/context_router.py#L256-L293).

**Correction / components:** Update `context_router.py` to read a bounded header/prefix where appropriate and surface oversized, unreadable or budget-limited inspection. Keep locality and total scan limits; insufficient discovery of an affected entrypoint needs an explicit Head assessment, not an unconditional platform assumption.

**Acceptance:**

- The same plugin header selects WordPress rules in both small and oversized affected files.
- Unrelated PHP remains PHP; this fix must not classify every PHP project as WordPress.
- Incomplete relevant inspection produces a visible limitation/uncertainty, and scan metrics distinguish content inspected from files skipped or truncated.

**Verification:** Add the confirmed large-file routing regression, a non-WordPress control and a relevant unreadable/budget-limited case to existing router tests. Preserve literal-path and bounded/locality regressions; no unbounded repository scan.

### R3: consistent project-root ownership

**Why:** Audit F4 validated a bound two-owner plan with scopes `.` and `scripts` and recommended parallelism 2; it returned `PASS`. The same helper also reported that `.` does not cover `scripts/feature.py`.

**Evidence:** [Scope helpers](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/156676d502fae98c5c0b3a9bafdf5497698a062e/scripts/execution_plan.py#L91-L110) and [ownership gate](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/156676d502fae98c5c0b3a9bafdf5497698a062e/scripts/execution_plan.py#L365-L393).

**Correction / components:** Make `execution_plan.py` ownership and drift checks consistently interpret `.` as the project root. Share normalized containment with the existing `behavior_contract.py` helper so retained root aliases do not contradict planner scope checks. Normalize equivalent project-relative forms without changing retained fingerprints or broad unrelated path refactoring.

**Acceptance:** Different writers owning `.` and a nested scope are blocked; genuinely disjoint scopes pass; a nested file within an approved root scope is not reported as outside scope. Equivalent `./` forms give the same result and literal filenames remain literal.

**Verification:** Extend existing plan overlap/drift tests with the confirmed root case, a disjoint positive case and root coverage. Preserve current cross-platform/literal-path checks.

### R4: one accurate operational validation path

**Why:** Audit F5 found current benchmark guidance referring to a removed workflow and requiring credentialed agent runs for stable releases, contrary to the active six-workflow release gate. Packaged agent-output guidance also names runners absent from the portable package.

**Evidence:** [Obsolete workflow claim](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/156676d502fae98c5c0b3a9bafdf5497698a062e/benchmarks/README.md#L53-L62), [obsolete stable gate](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/156676d502fae98c5c0b3a9bafdf5497698a062e/benchmarks/README.md#L121-L123) and [portable guide commands](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/156676d502fae98c5c0b3a9bafdf5497698a062e/evals/AGENT_OUTPUT_SCHEMA.md#L37-L84).

**Correction / components:** Reconcile `benchmarks/README.md`, `evals/AGENT_OUTPUT_SCHEMA.md` and their active references with actual workflows and package contents. Remove or explicitly archive obsolete requirements. Retain optional maintainer evaluation only with a clear external/maintainer boundary; do not reintroduce runners, provider-key requirements or model campaigns.

**Acceptance:** Active release guidance agrees with the implemented gate. Every command in portable guidance resolves to an included entrypoint or a clearly identified optional maintainer route. Ordinary skill use and release readiness require no provider API key.

**Verification:** Check affected links, workflow/command targets and portable-guide resources; synchronize edited runtime mirrors. No model execution or new wording-only tests.

## Delivery evidence

| Delivery action | Verified result |
|---|---|
| Release source | [Merged PR #81](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/81); release tag `v1.3.1` points to commit `d8adf4eed74cd5893ae8ed30cf5f9483c314d023`. Published on 2026-10-04 at 10:45:41 UTC (2026-10-04, Asia/Tehran). |
| Release checks | All six required workflows passed on that release commit: Validate Skill, Cross Platform Smoke, Real World Repository Validation, Agent Skills Spec Compatibility, Tool Contract Tests and WordPress Artifact Contract. [Release-commit checks](https://github.com/pooyahayati/Vibe-Coding-Skill/commit/d8adf4eed74cd5893ae8ed30cf5f9483c314d023/checks). |
| Published package | `Vibe-Coding-Skill-1.3.1.zip`, 78 files. Published archive SHA-256: `b6539198bed950ea0d67967251f38faff330f698d43a9a86376c86c40f1685bb`; its digest matched the locally built package and published checksum. Archive and checksum are attached to the release. |
| Local installation snapshot | Verified on 2026-10-04: `C:\Users\Pooya\.codex\skills\vibe-coding-skill` is `1.3.1`; all 78 installed files matched the published archive byte-for-byte, with no extra files. The official installer staged the exact release tag before replacement. Required package/resource checks passed, with no offline-check failures; optional Trivy was unavailable. The previous `1.3.0` installation was replaced and its temporary backup removed after verification. |

Previous delivery snapshot: `1.3.0`, [PR #74](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/74), release commit `83fd4f47e60930718a2c9fb5e27fdedb74de2e81`. Its six release checks and 78-file package/local match were verified on 2026-10-03; archive SHA-256 was `7cdd0b522619b78332d8fe66f11b0e0e4268be7d4e8e5b7a8e0acb555ad7fc67`.

The installation row records one verified host snapshot, not automatic updates for every user or already-loaded agent instructions. Later roadmap-only changes do not change the immutable release artifact or require reinstalling unchanged runtime files.

<details>
<summary>Completed original cycle: baseline, packages and feedback</summary>

## Completed baseline

Original baseline: `1.1.0`, main `9e0ca5108567f38a66376883613fdcaff6616de0`. The nine original packages and feedback follow-up are delivered in `1.3.0`; none is counted as a new hardening package.

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
| D1 | 4 | Concise user/maintainer documentation reflecting implementation. | Complete | [Implementation PR #73](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/73). User/maintainer guidance aligned with runtime. Skill validation, mirror consistency, 63 local links/anchors and preservation of README tables/full author passed; offline install had no failures (optional Trivy warning). Merged in PR #73, merge `3c886874e00e331f2d17ec461d10eda0953a423f`; all three affected PR workflows passed. |

## Follow-up F1: skill feedback

This user-requested addition is outside the original nine-package cycle and is included in [PR #73](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/73) alongside D1. **Status: Complete; merged in PR #73 and shipped in `1.3.0`.** The conditional Head-owned route covers confirmed/suspected Vibe defects, minimal English local reports, deduplication and optional user-reviewed email. Skill validation, mirror consistency, two existing install-manifest checks and the extracted 78-file package check passed (optional Trivy warning only). Instruction review covered confirmed/suspected attribution, environment-only failures, duplicates, sharing, blocked work and unavailable storage; this is policy review, not real-agent conformance. Release and local installation evidence are recorded separately above.

</details>

## How progress stays current

This file is maintained in Git; it is not an automatic live monitor. Update it when a roadmap package starts, a blocker changes, implementation is verified/merged, or a release is delivered. Use `R1`-`R4` in this cycle's implementation PRs and link the relevant PR/commit and concise acceptance evidence in the active tracker. Keep closed-cycle evidence separate. Update the implementation plan only when scope, dependencies or acceptance decisions change.

Statuses: **Not started**, **In progress**, **Blocked**, **Complete**. Opening a PR or writing code does not make a package Complete. Completion requires its acceptance conditions, relevant verification and merged implementation; a completion update proposed in that implementation PR takes effect when merged. Track release/deployment/local-installation separately when they are part of the objective.

Current phase, next action and the completed count must agree with the active tracker and change as packages progress; do not replace the tracker with a growing diary or an unsupported percentage. A blocked item must state the cause and next resolving action. Planning this cycle does not close a finding. [Contributor update rule](CONTRIBUTING.md#roadmap-progress).

Verification stays proportional: extend affected regressions, reuse passing relevant evidence and run existing required CI at its normal gate. Do not repeat unrelated full suites after wording-only edits. Runtime/reference changes require mirror/package consistency; release and local installation remain separate authorized delivery actions.

## Outcome

Improve the delivered software, not the volume of code, instructions or tests. A non-programmer should receive the intended behavior, supported by relevant execution evidence, with specialist work integrated under one accountable engineering Head.

<details>
<summary>Original cycle: priorities and delivery sequence</summary>

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
| 0 | Complete | Set shared contracts and compatibility rules. | Head / maintainer. | [P0 design](references/shared-improvement-contracts.md): small behavior, receipt and specialist-return formats; policy for legacy reports and acceptance snapshots. | Minimal formats, trust limits and migration specified; relevant checks passed in PR #62. Runtime implementation followed in phases 1-3. | Existing source inspection. |
| 1 | Complete | Carry the user scenario through Define, Plan, Build and Verify. | Head; relevant specialist contributes domain detail. | B1 guidance and B2 linked acceptance IDs with state/handoff/resume propagation. | Scope and observable expectations survive planning and handoff; no blanket extra approval. Merged in PR #64. | Phase 0. |
| 2 | Complete | Record real execution and validate required receipts at completion. | Head and local tooling. | E1 local collection and E2 schema-3 local receipt resolution/manual observation records. | Failed/missing/stale receipts and mismatched artifacts do not qualify; sufficient evidence is reused. Merged in PR #66. | Phase 1. |
| 3 | Complete | Accept specialist updates and task output against the shared contracts. | Head accepts; selected specialist supplies domain work. | S1 instruction compatibility and S2 retained stage returns/separate Head acceptance. Merged in PR #68. | Required conflicts are resolved or the affected workflow remains blocked; no standalone specialist lifecycle. | Phases 1 and 2. |
| 4 | Complete | Integrate, document and prepare delivery. | Head / maintainer. | Focused regression evidence, synchronized portable package, installation evidence and user-facing examples. | Changed behavior passes relevant checks; documentation matches runtime and risk routes stay proportionate. | Phases 1-3. |

Release, merge and local installation are separate delivery actions. A version number is chosen after compatibility review; no release date or publication is implied by this plan.

</details>

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

The active packages address five confirmed tooling/instruction findings from the audited source and controlled in-memory reproductions. They are not claims that a produced application was observed to fail. Release/package/installation consistency was checked separately and showed no material drift; it is not an additional improvement package.

A command receipt can show the recorded command/result and detect later mismatches. It cannot prove that the selected check tests the right requirement, prevent a privileged actor from forging local records, or prove every vulnerability absent. Head review and host permissions remain necessary. Semantic compatibility review is an engineering assessment, not an automatic proof from keyword checks.

Measure improvement with affected real workflows: can an intentionally failing/stale result be rejected, can the intended behavior be demonstrated, and can a conflicting specialist return be kept out of integration? Record only observed results; do not promise an error-reduction percentage or a future score.
