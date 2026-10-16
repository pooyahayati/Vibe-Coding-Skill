# Improvement Implementation and Acceptance Index

Package numbers belong to the permanent [repository roadmap register](../ROADMAP.md#roadmap-register); they do not restart with a new release or cycle.

[ROADMAP.md](../ROADMAP.md) is the only current progress tracker. This document defines the approved R31-R32 scope and acceptance in priority order. Runtime behavior belongs to the canonical scripts and operating references; implementation evidence belongs in the roadmap.

## Confirmed workflow limitations

Baseline: main `8a7d51d978f651244842e6a743677718b6f1b14b`, installed/runtime version `1.6.1`, reviewed 2026-10-16. Both behaviors below are confirmed. They are workflow limitations, not evidence that the current safeguards should be removed. Speed improvements are expected benefits, not measured results.

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

## Execution and validation boundaries

1. Implement R31 first when requested; move to R32 after its scoped behavior is accepted. Use one owner for shared routing, authority and assignment-state changes. Record progress only in the roadmap.
2. Preserve the smallest sufficient architecture. R31 changes participation, not specialist ownership. R32 changes resource lifecycle, not completion requirements or user authorization.
3. Keep existing record compatibility; document any necessary format/transition policy before writing new records. Retain current behavior for unsupported legacy transitions instead of silently weakening a guard.
4. Planning changes require document structure, local links/anchors, repository purity and mirror consistency. Runtime implementation uses affected regressions and portable checks; existing full integration/publication gates apply at their existing triggers.
5. Before a package is marked Complete, retain relevant acceptance evidence and merged implementation. Commit, push, merge, publication and local installation need authorization for this cycle; prior-cycle permissions are not inherited.

## Deferred and excluded work

- **Verification-cost changes:** Existing receipts already contain execution timestamps; current policy supports scoped evidence reuse and multiple criteria per obligation. First establish unnecessary execution in an actual slow task using existing evidence. No new timing service, fixed global time cap, mandatory per-edit report or general testing-policy rewrite is approved.
- **Broader observability:** Add only for a concrete operational diagnosis requirement. No general monitoring stack, new specialist or production telemetry obligation belongs to this cycle.
- Do not add dependencies, scanners, model evaluation, provider keys, coverage/test-count quotas or unrelated cleanup. Preserve native Trivy before publication and the sole UI/UX specialist.

## Delivered specifications

- [R28-R30 specifications through 1.6.1](archive/improvement-plan-through-1.6.1.md) and [delivery evidence](archive/improvement-roadmap-through-1.6.1.md).
- [R23-R27 specifications through 1.6.0](archive/improvement-plan-through-1.6.0.md) and [delivery evidence](archive/improvement-roadmap-through-1.6.0.md).
- [R18-R22 specifications through 1.5.0](archive/improvement-plan-through-1.5.0.md) and [delivery evidence](archive/improvement-roadmap-through-1.5.0.md).
- [Earlier implementation history](archive/improvement-plan-through-1.4.0.md) and [roadmap history](archive/improvement-roadmap-through-1.4.0.md).

Archived status, next actions and authorizations are historical. Use the [current roadmap](../ROADMAP.md) for active work.
