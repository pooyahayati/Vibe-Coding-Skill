# Improvement Implementation and Acceptance Index

Package numbers belong to the permanent [repository roadmap register](../ROADMAP.md#roadmap-register); they do not restart with a new release or cycle.

[ROADMAP.md](../ROADMAP.md) is the only current progress tracker. This document defines the approved R33-R34 scope and acceptance in priority order and retains the delivered R31-R32 specifications below. Runtime behavior belongs to the canonical scripts and operating references; implementation evidence belongs in the roadmap.

## Review baseline and confirmed gaps

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

## Execution and validation boundaries

1. Start implementation with R33 when requested; move to R34 only after R33's scoped acceptance. Keep shared preparation edits sequential and record progress only in the roadmap. Planning approval alone does not start runtime work.
2. Reuse existing routing, preparation, inventory state and record compatibility. Define any necessary record transition before writing it; preserve conservative handling of unsupported legacy state.
3. This planning edit needs structure, relevant local links/anchors, repository purity and mirror consistency. Runtime work needs affected regressions and portable checks. Existing full integration/publication gates, including native final-artifact Trivy, retain their existing triggers.
4. Add only regressions for uncovered failure modes in these two packages. Reuse sufficient evidence; do not expand test quotas, run a platform matrix after each edit or introduce mandatory per-edit reports.
5. Complete means accepted behavior plus merged implementation, with evidence retained in the roadmap. Commit, push, merge, publication and local installation require authorization for this cycle and remain distinct outcomes.

## Deferred and excluded work

- **Broad instruction slimming:** Not an independent stage. R33 may clarify task-entry and conditional-reference wording needed for consistent routing; a general `SKILL.md` rewrite or further file splitting needs demonstrated benefit.
- **General verification-cost changes:** Use existing receipts to establish unnecessary execution in an actual slow task first. No general testing-policy rewrite, new timing service or fixed global time cap is approved.
- **Broader observability:** Requires a concrete operational diagnosis need. Do not add a monitoring stack, specialist, dependency, scanner, model evaluation, provider key or coverage quota. Preserve Head authority, the sole UI/UX specialist, required findings and release controls.

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
