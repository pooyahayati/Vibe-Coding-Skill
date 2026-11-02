# Improvement Implementation and Acceptance Index

Package numbers belong to the permanent [repository roadmap register](../ROADMAP.md#roadmap-register); they do not restart with a new release or cycle.

[ROADMAP.md](../ROADMAP.md) is the only current progress tracker. This document defines R35-R39 scope and acceptance in priority order and retains the delivered R31-R34 specifications below. Runtime behavior belongs to canonical scripts and operating references; implementation evidence belongs in the roadmap. The execution boundaries below reflect the subsequent implementation authorization; installation and publication remain separate.

## Review baseline and evidence boundaries

Baseline: main `38925f29a733528321004389f3a337779406ad9f`, runtime `1.7.1`, reviewed 2026-11-02, Asia/Tehran. Prioritization was reconsidered against existing coverage, realistic change scenarios and added workflow cost. Existing risk-adaptive testing, Head authority, specialist isolation and conditional Docker/Compose delivery remain the foundation.

| Package | Evidence / limitation | Expected benefit |
|---|---|---|
| R35 | A bounded temporary-fixture reproduction changed stored data, observed a meaningful check fail, replaced that check with `assert True`, then obtained a fresh passing receipt and `PASS` with the retained outcome unchanged. This exposes missing verification-weakening review, not forged receipts or a promise that hashes prove semantics. See [receipt limits](../references/execution-receipts.md#receipt-backed-completion-e2) and [change signals](../scripts/change_budget.py). | Prevent false completion while preserving legitimate test maintenance. |
| R36 | [Technology selection](../references/operating-model.md#solution-and-technology-selection) checks decision-critical versions, but the implementation route does not consistently bind a documentation lookup to the installed/supported product version. Context7 supplies retrieval, not compatibility proof. | Reduce invented APIs, obsolete examples and avoidable correction loops. |
| R37 | [Contract validation](../scripts/behavior_contract.py) validates declared criteria/evidence, and [specialist assignments](../scripts/specialist_handoff.py) inherit declared invariants; neither establishes that an initially omitted security outcome was captured. Existing security guidance remains valid. This is a coverage gap, not a demonstrated product exploit. | Preserve changed-boundary security outcomes through implementation and acceptance. |
| R38 | [Reuse and architecture rules](../references/operating-model.md#architecture) already exist. The change summary reports churn and sensitive paths, not whether a new subsystem/dependency/boundary has a current need or a sufficient existing alternative. No defect is inferred from size alone. | Reduce unnecessary code and maintenance surfaces through a targeted existing review. |
| R39 | The [performance pack](../packs/performance-web.md) covers before/after evidence, and [product installation](../references/product-installation-and-runtime.md) covers real startup/data persistence. A concise, conditional link from workload/recovery expectations to supported operational claims remains to be defined. | Make performance, capacity and recovery claims reviewable without premature infrastructure. |

The R35 observation is retained audit evidence, not a committed regression or a new CI result. R36-R39 are targeted improvements, not four additional reproduced defects. Speed gains, live provider integration and production-scale outcomes remain unmeasured. Revalidate the affected code before implementation if the baseline changes.

## Execution and validation boundaries

1. **Authorization:** The planning-only request was superseded by explicit authorization to commit/merge the plan and implement **R35 -> R36 -> R37 -> R38 -> R39**, including the README update. Continue after scoped acceptance without another approval for every step. The subsequent delivery request authorizes implementation commit/merge, a new release and local Head update; verify and record each outcome separately.
2. **Existing mechanisms first:** Reuse task contracts, evidence obligations, Head acceptance, routing, state and receipt freshness. R37 depends on R35's integrity handling; R36, R38 and R39 otherwise follow priority/integration order, not a requirement to install each other's providers. Define compatibility/migration before changing a persisted format; retain obligations and handle legacy/unknown state explicitly.
3. **No extra workflow:** Add no new orchestrator, mandatory specialist, global test quota, model evaluation, blanket scanner, recurring service or per-edit document. Keep the sole UI/UX specialist. A small non-runtime edit must not acquire formal security work, documentation lookups or load tests from this cycle.
4. **Proportionate verification:** Reuse sufficient existing cases and receipts. Extend existing fixtures only for an uncovered acceptance failure; run affected checks during implementation. When portable behavior changes, synchronize the canonical resources and check the affected extracted route. Existing full integration/publication and native final-artifact Trivy gates keep their current triggers; no full suite after every edit.
5. **Safe evidence:** Use owned temporary fixtures and stubbed providers for mechanism checks. No real-project mutation, production load, credentialed/paid request or host installation is implied. Provider availability, returned text and mechanism success are distinct from correct product behavior. Do not claim measured speed gains from fixture counts.
6. **Planning acceptance:** Check structure, relevant local links/anchors, consecutive unique IDs, preservation of historical evidence, repository purity and unchanged portable resources. Update current status only in the roadmap. Completing this document does not complete R35-R39.

<a id="r35"></a>

## R35: Verification integrity and evidence protection

**Priority:** 1 / High. **Complexity:** Medium. **Dependency:** None.

**Trigger / outcome:** When a change modifies a check used to support acceptance, review lost detection power before using a new passing result to declare completion. Ordinary test maintenance remains allowed.

**Implementation sequence:**

1. Reproduce the audit scenario in the existing isolated receipt fixture. Identify the relevant pre-change check definitions and accepted outcome using existing task/Git evidence; do not invent a new baseline from the weakened check.
2. Extend the existing diff/review route to surface removed assertions, skipped/deleted relevant tests, relaxed expectations/thresholds and new suppressions as review signals. Keep inspection scoped; missing comparison evidence is explicit uncertainty, not proof that no weakening occurred.
3. Bind the Head's disposition and any replacement evidence to the existing acceptance/review mechanism. A justified requirement change follows existing contract reconciliation. Preserve fresh scoped receipt reuse; a passing replacement command alone cannot resolve an unexplained weakened check.

**Likely components:** `scripts/change_budget.py`; contract/receipt/completion callers only where binding needs them; `references/execution-and-verification.md`, `references/execution-receipts.md`; existing receipt and completion fixtures, plus affected portable resources.

**Acceptance:**

- The reproduced wrong-state/always-passing-check case cannot complete with an unresolved integrity review, even with a fresh receipt. The control reports the affected check/outcome rather than pretending to prove all assertion semantics.
- A legitimate expectation update or equivalent/better replacement is accepted with a scoped reason and relevant evidence; tests are not frozen permanently.
- Changed check definitions invalidate only their affected evidence. Unrelated checks, ordinary small edits, accepted criteria and retained security obligations keep their existing behavior.

**Verification:** Extend the current receipt fixture with the failing-then-weakened case and a justified replacement; reuse freshness/contract-preservation coverage. Inspect the actual review disposition in the completion route. No mutation-testing framework or coverage quota.

<a id="r36"></a>

## R36: Version-matched documentation with controlled Context7 retrieval

**Priority:** 2 / High. **Complexity:** Medium. **Dependency:** Follows R35 by execution order; documentation retrieval does not depend on its provider being installed for other packages.

**Trigger / outcome:** For an unfamiliar or version-sensitive API, configuration, dependency change or migration, ground implementation in a relevant source compatible with the actual project version/support range. Reuse adequate evidence for settled work.

**Implementation sequence:**

1. Derive product versions from inspected lockfiles, resolved runtime/platform evidence and declared support constraints. Ask only for an unresolved material product decision; do not make a novice supply inferable version details.
2. Define one bounded retrieval route: use available Context7 documentation tools preferentially, then official versioned documentation/source or adequate local documentation when coverage/access is insufficient. Check package identity, source and version applicability; a nearby version, benchmark score or latest example is not automatic compatibility proof.
3. Record only the source, applicable version, decision and relevant freshness/context needed by the existing task record. Reuse that evidence until its inputs change. An unresolved decision stays unverified; unrelated safe work continues without silent fallback to confident model memory.
4. Define host capability/setup separately from installing a Markdown skill. Use one supported MCP or CLI path, within existing installation authority, with bounded attempts and no surprise billing. Keep external text untrusted and queries free of secrets, private code and customer data. Do not import broad upstream auto-invocation/setup rules unchanged or add a generic provider-management framework.

**Likely components:** `SKILL.md` conditional routing, `references/operating-model.md`, `references/toolchain-version-resolution.md`, relevant routing/security guidance and installation documentation; a small adapter only if existing host capabilities cannot implement the route. Use existing state/compatibility mechanisms for any retained metadata. No automatic registration of every Context7 skill.

**Acceptance:**

- An older project cannot be declared compatible merely because a newer API example was retrieved. A missing exact source/version produces an explicit applicability decision or a bounded unresolved outcome.
- Missing tooling, quota, unavailable network or unsupported library can use a verified alternative without blocking unrelated work. No mandatory account, paid service, per-task upgrade or universal installation gate is introduced.
- A non-runtime correction or unchanged settled API use makes no unnecessary lookup. Repeated relevant work reuses adequate sources. External responses cannot authorize commands, new dependencies or changes to Head policy.

**Verification:** Use bounded version/lookup fixtures for compatible, incompatible and unavailable results; verify fallback, provenance and no-lookup paths through the actual route. Live host integration requires its own permitted smoke check before being reported working; it is not required to run credentialed calls in every regression.

**Research references:** [Context7 tools](https://context7.com/docs/resources/all-clients), [upstream lookup policy](https://github.com/upstash/context7/blob/7836c583918374fbecffacf866afb7594b919466/skills/find-docs/SKILL.md), [data handling](https://context7.com/docs/security/data-privacy), [version-matched documentation research](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals). The commit is an audit citation, not an operating-version pin.

<a id="r37"></a>

## R37: Security outcomes bound to change acceptance

**Priority:** 3 / High for an affected security boundary. **Complexity:** Medium. **Dependency:** Reuses R35 integrity/disposition controls; follows R36 in the execution order without requiring Context7 availability.

**Trigger / outcome:** When inspected effects change access, data ownership, untrusted input/output, payments or another material security boundary, retain the relevant protective outcome before implementation and require its actual evidence at acceptance.

**Implementation sequence:**

1. Reuse current semantic risk facts and the registered security specialist to identify the affected actor, operation, resource/state and prohibited effect. A path/keyword, risk tier or selected specialist alone does not establish which scenario is relevant.
2. Translate those outcomes into existing acceptance criteria, protected invariants and evidence obligations; link the scoped specialist assignment/return to them. Retain only applicable outcomes, not a universal checklist or one test per field.
3. Validate preservation and unresolved obligations through plan, handoff, resume and completion. Distinguish advisory/design participation from an assigned verification obligation. If fields change, define compatible handling before migration; never fabricate missing legacy evidence.

**Likely components:** `scripts/behavior_contract.py`, `scripts/specialist_handoff.py`, affected plan/completion/state callers; `references/security-and-dependencies.md`, existing acceptance/composition guidance and applicable packs; current contract/handoff/receipt fixtures and portable resources.

**Acceptance:**

- For a changed protected mutation, the relevant denial includes unchanged protected state; for changed ownership/isolation, the relevant cross-owner access is denied. Use these only where the actual boundary requires them.
- Ordinary happy-path success or a clean Trivy result cannot satisfy an unresolved behavioral security outcome. Required findings survive handoff/resume and cannot be omitted from completion.
- Low-risk unrelated changes do not acquire security records or a mandatory allow/deny pair. Adequate existing checks count; no new scanner, second security workflow or automatic requirement based only on project size.

**Verification:** Extend the existing protected-setting or scoped security-assignment case with an initially missing obligation, retained propagation and a result that reports denial but still changes state. Reuse valid-obligation and guidance-only cases to show that unrelated work stays lightweight.

<a id="r38"></a>

## R38: Evidence-based reuse and structural growth review

**Priority:** 4 / Medium. **Complexity:** Small. **Dependency:** Follows R37 by priority; no new provider or specialist prerequisite.

**Trigger / outcome:** When adding a custom subsystem, runtime dependency, service or material architectural boundary, review the existing alternative and the actual need using the current decision/review route. Strengthen execution of the existing simplicity rule rather than add a general refactoring phase.

**Implementation sequence:**

1. Inspect the relevant local implementation, platform capability and established project convention before creating a replacement. Prefer compatible, maintained existing behavior; reuse still respects security, licensing and ownership constraints.
2. Extend the existing change summary/review to surface material new maintenance boundaries and connect them to a current requirement, consumer, failure-isolation need or demonstrated repetition. Counts and naming patterns are signals, not automatic judgments of architecture quality.
3. Keep a concise existing decision rationale: what was inspected, why it is insufficient and what the new structure buys/costs. Remove only unjustified additions within the authorized change; do not reorganize unrelated product code or require a document for every helper.

**Likely components:** `scripts/change_budget.py` if a bounded signal improves review; `references/operating-model.md`, `references/execution-and-verification.md`; existing diff/decision scenarios and affected portable resources. No new architecture framework or project-wide code-search service.

**Acceptance:**

- An existing adequate capability is reused or a concrete incompatibility/requirement explains the new implementation. Popularity or fewer lines alone cannot establish suitability or performance.
- A justified dependency/boundary remains allowed. An unjustified layer introduced by the current change is flagged without mandatory wholesale refactoring or blanket dependency bans.
- Ordinary function fixes and copy edits do not trigger an alternatives study, dependency installation or additional suite. Maintain observable behavior, readability and existing focused verification.

**Verification:** Reuse a scoped change scenario containing an adequate existing implementation and contrast it with a real boundary/compatibility need. If detection code changes, extend only its affected fixture; do not encode subjective line-count or interface-count targets as tests.

<a id="r39"></a>

## R39: Measured performance, capacity and recovery

**Priority:** 5 / High when a material operational requirement exists. **Complexity:** Medium. **Dependency:** Follows R38; reuses R35 evidence integrity and R37 for relevant protected-state outcomes. No mandatory Context7 connection or new performance specialist.

**Trigger / outcome:** For an explicit performance/capacity need, observed regression, significant workload growth or consequential stateful deployment change, establish the supported operating conditions and evidence behind the claim.

**Implementation sequence:**

1. Reuse project requirements to identify representative workload/data volume, target environment/resources, acceptable response/resource behavior and relevant data-loss/recovery expectations. Ask only unresolved material product questions in plain language; do not invent universal thresholds or promise scale from stack choice.
2. Measure the relevant core path under stated conditions. Identify the observed bottleneck, make the smallest justified correction and compare under equivalent conditions. If existing behavior meets the requirement, stop without adding caches, queues or services.
3. Where required, exercise recovery using disposable data and the actual supported installation/deployment path; capture the minimum diagnostic evidence needed to identify a failure. Link environment, dataset/workload and artifact identity through existing receipts/acceptance. Local startup, container health and data persistence alone are not proof of every production recovery or capacity claim.

**Likely components:** `packs/performance-web.md`, its routing triggers where necessary, `references/operating-model.md`, `references/execution-and-verification.md`, `references/product-installation-and-runtime.md`; existing architecture/acceptance templates only if they need conditional fields; current routing/receipt scenarios and portable resources.

**Acceptance:**

- Performance/capacity claims identify the workload, environment and observed limit/result; untested growth remains an assumption. A claimed improvement has a representative baseline and comparison, not merely an optimization label or famous library.
- Required recovery restores the promised state within the applicable expectation, or remains explicitly failed/unverified. Relevant environment/workload changes invalidate affected evidence; unrelated edits do not rerun load/recovery checks.
- No global load-test schedule, new monitoring stack, fixed benchmark number, compulsory microservices/Kubernetes or production load without authorization. Small local work with no such requirement uses the existing light route.

**Verification:** Use an owned representative fixture to demonstrate evidence linkage and an unmet requirement/recovery case, reusing existing context/freshness checks. Such a fixture proves the mechanism, not a real product's capacity; actual product claims require their own authorized measurements.

## Retained specifications: R33-R34

The following specifications describe delivered 1.7.1 work. Their priorities, baselines and dependencies are historical, not instructions to restart them. Current scope and execution boundaries are above; current status and delivery evidence are in the [roadmap](../ROADMAP.md).

<a id="review-baseline-and-confirmed-gaps"></a>

### Original review baseline and confirmed gaps

Baseline: main `1204b41fced7cb144721bebc90a5ec03d84dad50`, runtime `1.7.0`, reviewed 2026-10-16. Source inspection and bounded in-memory reproductions support the two gaps below. They establish inconsistent decisions and repeated work, not measured project latency or a demonstrated unsafe release. The reproductions did not change installed skills, project assignments or repository files.

| Package | Evidence and practical effect |
|---|---|
| R33 | For the same settled-label request, complete low-risk facts, preserved RTL context and an unreadable affected path, the router chooses formal participation while standalone manager selection chooses guidance-only. The selector defaults `inspection_complete` to true; the manager CLI does not supply the router's inspection/risk assessment. The planner already calls the router, so a new planning engine is unnecessary. [Selector](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/1204b41fced7cb144721bebc90a5ec03d84dad50/scripts/specialist_manager.py#L116-L120), [CLI caller](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/1204b41fced7cb144721bebc90a5ec03d84dad50/scripts/specialist_manager.py#L791-L794), [router](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/1204b41fced7cb144721bebc90a5ec03d84dad50/scripts/context_router.py#L1232-L1235), [existing planner reuse](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/1204b41fced7cb144721bebc90a5ec03d84dad50/scripts/execution_plan.py#L139-L150). |
| R34 | When inventory is due, preparation checks all installed specialists. An unrelated failure returns WARN, leaves inventory due and causes the next task to repeat the inventory. A stubbed three-call reproduction repeated the same installed-entry checks without writing a successful inventory record; this was not live network traffic. An unrelated WARN also prevents saving otherwise valid assignment preparation. [Inventory and task preparation](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/1204b41fced7cb144721bebc90a5ec03d84dad50/scripts/specialist_manager.py#L719-L760), [preparation persistence](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/1204b41fced7cb144721bebc90a5ec03d84dad50/scripts/specialist_handoff.py#L215-L227). |

<a id="r33"></a>

## R33: Consistent inspected specialist selection

**Priority:** First / High. **Complexity:** Medium. **Dependency:** None.

**Outcome:** Task entry, planning and specialist preparation agree on participation using the current inspected change. Verified mechanical edits remain lightweight; missing inspection cannot silently qualify them for guidance-only.

**Correction:**

- Reuse the existing router/risk evaluation at task entry and pass its inspection completeness, risk facts, domain effects and selected specialists into preparation in the same current operation. Avoid asking the agent to reconstruct the same decision through separate flags.
- Remove the standalone path's implicit complete-inspection assumption. Missing/unreadable paths, conflicting evidence and unknown scope retain conservative handling. Scope, source or relevant-control changes require reassessment; do not freeze a previous light decision.
- Keep the planner's existing router integration. Clarify only the corresponding entry and conditional-reference instructions in `SKILL.md` and specialist guidance; no general instruction rewrite, persistent routing cache or new workflow engine.

**Likely components:** `scripts/specialist_manager.py`, `scripts/context_router.py`; `scripts/execution_plan.py` callers only if needed; `SKILL.md`, `references/specialist-composition.md`; existing specialist/routing/planning fixtures and corresponding portable resources.

**Acceptance:**

- Equivalent task inputs and current source evidence produce the same selected specialists and participation through router, planner and manager entry points. Preparation consumes that assessment without manually rebuilding it or introducing a second selection policy.
- A reviewed mechanical label correction with preserved RTL/responsive behavior remains guidance-only without a formal assignment record. A missing/unreadable affected file or changed/unknown effects cannot take that path; changing the source/scope invalidates the earlier decision.
- Explicit assignments, risk floors, retained findings/obligations, accepted compatibility and current-source checks before use remain binding. Supplied evidence text alone does not prove inspection completeness.

**Verification:** Extend the existing router/planner participation scenario to cover the standalone manager entry with readable versus unreadable source and a changed scope. Reuse existing mechanical-edit, unknown-effect, explicit-assignment and risk-floor coverage. Run affected checks during implementation and the affected extracted-package route before acceptance; no full suite after every edit or new testing framework.

<a id="r34"></a>

## R34: Bounded periodic specialist inventory

**Priority:** Second / High. **Complexity:** Medium. **Dependency:** Follows R33 acceptance because both touch preparation; no separate feature dependency.

**Outcome:** An unavailable unrelated specialist does not make each new task wait for a repeated full installed-specialist inventory. Required Head/selected-specialist checks and observable periodic maintenance remain effective.

**Correction:**

- Separate required task preparation from general periodic inventory using the existing manager commands/state. Define an explicit safe maintenance boundary in the operating guidance so periodic inventory still runs; do not silently make it optional or perform background replacement of active instructions.
- Record failed-attempt scheduling separately from last successful freshness, with a bounded retry rule using the existing interval/state mechanism. An unrelated failure stays WARN/unverified and must not trigger all installed checks on every task or receive a false successful timestamp.
- If a previously unrelated specialist becomes required, perform the required current-source and compatibility checks before use regardless of inventory retry scheduling. Preserve scoped preparation reuse and its existing binding/invalidation rules; never resurrect older success after a failed fresh required check.
- Save/reuse valid required preparation independently of unrelated inventory warnings. Required failures, changed resources/controls and reload requirements still invalidate or block the affected preparation. Preserve R32's active/legacy assignment protections.

**Likely components:** `scripts/specialist_manager.py`, `scripts/specialist_handoff.py`; inventory policy in `config/specialists.json` only if needed; `SKILL.md`, `references/specialist-composition.md`; existing specialist/handoff fixtures and corresponding portable resources.

**Acceptance:**

- Across consecutive tasks during the retry interval, a failed unrelated specialist does not cause another whole-inventory pass or block successful required preparation. An unrelated WARN does not discard a valid preparation binding.
- Selecting that failed specialist immediately triggers its required checks; failure blocks its use. Head/required-specialist failures, incompatible instructions and RELOAD remain effective regardless of inventory scheduling.
- The last successful inventory time changes only after success. Attempts, unresolved failures and the next retry remain distinguishable; a due retry or explicit inventory action can reconcile them. Existing or missing inventory records remain readable without treating unknown freshness as current.
- No permanent source pin, stale cross-task success fallback, second preparation cache, background service, real-assignment closure or live-installation mutation is required to prove the behavior.

**Verification:** Extend the existing unused-specialist failure fixture across consecutive prepares, a due retry and selection of the failed specialist. Reuse assignment-preparation scenarios for unrelated WARN, required failure and changed bindings. Use temporary state, a controlled clock and stubbed upstream access rather than live updates; run affected checks and the affected extracted-package route before acceptance. Do not introduce a timing service, model evaluation or a test-count target.

<a id="deferred-and-excluded-work"></a>

R33-R34 retained the existing preparation/state mechanisms and proportionate checks; their implementation and publication permissions are historical. Broad instruction slimming, a new routing cache, a monitoring service and test quotas were outside that cycle. The R35-R39 boundaries above define the current planning scope without reopening delivered work.

## Retained specifications: R31-R32

The following specifications describe the delivered 1.7.0 work. Their priorities and dependencies are historical, not instructions to restart them. See the [roadmap](../ROADMAP.md) for current status and retained delivery evidence.

Original review baseline: main `8a7d51d978f651244842e6a743677718b6f1b14b`, runtime `1.6.1`, reviewed 2026-10-16. The following limitations motivated R31-R32 and are retained as historical evidence.

| Package | Evidence and practical effect |
|---|---|
| <a id="r31"></a>R31 | With otherwise identical complete low-risk facts and inspected mechanical-change evidence, `ui` can select guidance-only while `rtl` or `responsive` selects a formal assignment. The UI guidance allowlist contains only `ui`/`ux`; the participation condition rejects other concerns. A contextual domain label can therefore add a formal handoff to a settled mechanical edit. [Selection condition](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/8a7d51d978f651244842e6a743677718b6f1b14b/scripts/specialist_manager.py#L144-L176); [registry](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/8a7d51d978f651244842e6a743677718b6f1b14b/config/specialists.json#L25-L42). |
| <a id="r32"></a>R32 | Assignment markers cover the Head and assigned specialist. A changed installation is deferred when any corresponding marker exists, including an assignment in another project. This blocked the previously requested local update while Together assignments remained open. An unchanged current installation returns before this guard; ordinary checks are not always blocked. [Shared markers](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/8a7d51d978f651244842e6a743677718b6f1b14b/scripts/specialist_handoff.py#L125-L134); [replacement guard](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/8a7d51d978f651244842e6a743677718b6f1b14b/scripts/specialist_manager.py#L463-L473). |

Existing mechanisms to retain: assignment-bound preparation reuse, accepted instruction compatibility, same-contract reassessment, stage-aware scoped receipts and proportionate test selection. R31-R32 must extend these mechanisms rather than recreate them.

## R31: Effect-based specialist participation

<a id="w1-effect-based-specialist-participation"></a>

**Priority:** First / High. **Complexity:** Small. **Dependency:** None.

**Outcome:** A verified mechanical UI edit can use the selected specialist's accepted guidance without a formal handoff caused solely by the page's RTL/responsive context. The specialist and relevant visual verification remain part of the workflow.

**Correction:**

- Separate a domain's presence from a material change to that domain when choosing participation. Keep the existing complete-risk-facts, inspected-paths and concrete-diff-evidence requirements.
- Reuse the mechanical/guidance path and risk classifier. Contextual `rtl`/`responsive` facts alone must not force a formal assignment after the Head has established that the change preserves settled behavior.
- Actual layout direction, breakpoint, interaction, accessibility or design decisions, incomplete inspection, conflicting evidence and explicit assignments retain formal handling. Do not treat every RTL/responsive request as mechanical by expanding an allowlist unconditionally.
- Keep other specialist domains, risk floors and retained assignments/findings unchanged. The Head still inspects actual effects; supplied metadata is not automated proof of semantics.

**Likely components:** `scripts/specialist_manager.py`, `config/specialists.json`; router/planner outputs if needed; the participation sections in `SKILL.md` and `references/specialist-composition.md`; existing `tests/test_specialists.py` and affected routing/plan fixtures; corresponding portable resources.

**Acceptance:**

- The same inspected low-risk label/spacing correction has the same participation outcome whether the unchanged product context is described as UI, RTL or responsive. Selected guidance remains required, and the change still gets its relevant source/rendered observation.
- Changed direction/breakpoints/accessibility/flows, new design decisions, unknown effects, incomplete inspection or an explicit assignment cannot silently enter guidance-only.
- Security/data/API risk floors and existing formal obligations remain binding. Router and planner agree on participation and do not create a formal record for a qualifying guidance-only edit.
- The existing preparation-cache validity rules and specialist compatibility checks remain intact; no new freshness bypass or duplicate cache is introduced.

**Verification:** Extend the existing mechanical-participation fixture with contextual RTL/responsive variants and the corresponding material-change/uncertain-scope cases. Reuse existing risk-floor, explicit-selection, router/planner and retained-obligation checks. Run affected tests during Build; verify the changed route from the extracted package before acceptance. No live specialist installation, new visual testing framework or full-suite-per-edit requirement.

## R32: Assignment-isolated skill updates

<a id="w2-assignment-isolated-skill-updates"></a>

**Priority:** Second / Medium. **Complexity:** Medium. **Dependency:** Follows R31 acceptance by execution order; no functional dependency.

**Outcome:** Updating the default installation for new tasks does not require abandoning an unrelated open assignment. Active work continues against identifiable stable resources, or undergoes an explicit, safe migration.

**Correction:**

- Retain one discoverable default installation. Resolve the latest permitted source for new tasks under existing authorization and compatibility checks; public policy still contains no fixed specialist versions.
- Preserve the exact Head/specialist resources and provenance needed by open assignments outside skill discovery and product repositories. Reuse existing external state, manifests, locking, staging and recovery mechanisms.
- Bind actual script/resource lookup and handoff/resume to those retained resources. Copying files or recording a revision without controlling what continuation loads is insufficient.
- Before relaxing the replacement guard, prove a bounded two-project continuation scenario. If the host cannot preserve the binding, retain the guard and report the unsupported transition.
- Make migration explicit: retain the old contract, scope, findings, acceptance history and evidence bindings; reassess changed controls and invalidate only evidence affected by the transition. Migration success is not task acceptance.
- Preserve legacy records conservatively. An older active operation without a verified resource binding keeps its protection until a safe explicit transition is available. Never infer abandonment from age, delete markers to unlock installation or promote unresolved work to accepted.
- Keep retained resources while any assignment or required review history depends on them. Define bounded retention/cleanup using actual references; do not build a general multi-version package manager or install duplicate discoverable skills.

**Components:** `scripts/specialist_manager.py`, `scripts/specialist_handoff.py`, the retained-resource dispatcher `scripts/assignment_runtime.py`; affected state/resume, compatibility and receipt callers; `references/specialist-composition.md`, `references/shared-improvement-contracts.md` and relevant lifecycle/recovery guidance; existing specialist/handoff/state fixtures and portable routes.

**Acceptance:**

- With an open assignment in project A, a verified update can become the default for a new task in project B. Project A continues/resumes using its recorded resource revision; it is not falsely reported as using the new version.
- Active resource contents, lookup paths, findings and contract identity remain stable. Tampered/missing retained resources, unresolved compatibility or an unsupported host binding stop the affected continuation/update with a concrete reason.
- An authorized migration preserves unresolved required findings and history. Prior acceptance cannot qualify changed controls automatically; current release/security obligations remain enforceable.
- Interrupted staging/activation/binding transitions recover without mixed installations, lost markers or fabricated completion. Existing rollback, local-modification and concurrent-update protection remain effective.
- Legacy assignments and archived acceptances remain readable and correctly checked. Resources still referenced by active work or required history cannot be removed.
- New tasks keep current-source/compatibility checks. Stable resources for an open operation are explicit provenance, not an unreported outdated fallback or a permanent version pin.

**Verification:** Extend existing temporary-installation/handoff fixtures with two project roots, a default update and real continuation/resume through the retained resource path. Reuse current compatibility, marker, stale-evidence, local-modification and recovery cases; add only uncovered interruption, legacy-binding or missing-resource regressions. Use temporary local fixtures rather than changing real Together assignments or installed user skills. Check the affected extracted-package route once ready. Follow existing CI scope and release gates; do not add a platform matrix or broad suite after each edit.

## Delivered specifications

- [R28-R30 specifications through 1.6.1](archive/improvement-plan-through-1.6.1.md) and [delivery evidence](archive/improvement-roadmap-through-1.6.1.md).
- [R23-R27 specifications through 1.6.0](archive/improvement-plan-through-1.6.0.md) and [delivery evidence](archive/improvement-roadmap-through-1.6.0.md).
- [R18-R22 specifications through 1.5.0](archive/improvement-plan-through-1.5.0.md) and [delivery evidence](archive/improvement-roadmap-through-1.5.0.md).
- [Earlier implementation history](archive/improvement-plan-through-1.4.0.md) and [roadmap history](archive/improvement-roadmap-through-1.4.0.md).

Archived status, next actions and authorizations are historical. Use the [current roadmap](../ROADMAP.md) for active work.
