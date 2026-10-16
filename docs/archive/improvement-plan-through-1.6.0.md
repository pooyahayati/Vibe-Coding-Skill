# Implementation Archive through 1.6.0

Roadmap IDs were normalized on 2026-10-16 to the permanent R sequence. See the [canonical register](../../ROADMAP.md#roadmap-register) for legacy aliases. Recorded outcomes, evidence and delivery identities are unchanged; old heading anchors remain available. Finding IDs and runtime/schema identifiers retain their separate meaning.

Archived on 2026-10-16 after R23-R27 shipped in 1.6.0. The status, approval, next-action and concern statements below are historical snapshots. The partial-release concern is superseded by current F3/R30. Use the [current roadmap](../../ROADMAP.md) and [implementation plan](../improvement-implementation-plan.md) for active work.

Progress and the next action are maintained only in [ROADMAP.md](../../ROADMAP.md). This document prepares the five approved R23-R27 corrections; it does not implement them or authorize publication/installation. Follow the roadmap order and retain one owner for shared policy/state changes.

## Confirmed audit findings

Baseline: `e75a8cae9f27c3e5f6305fb5e14523ed9fe06401`, runtime `1.5.0`, reviewed 2026-10-15. Confidence is high in the behaviors below; their share of elapsed time in individual user projects has not been measured. The earlier F1-F7 findings belong to the closed [R18-R22 archive](improvement-plan-through-1.5.0.md#confirmed-audit-findings).

| Package | Evidence and realistic failure | Basis |
|---|---|---|
| <a id="r23"></a>R23 | `risk_classifier.classify` returns Tier 2 for an authentication-documentation typo and Tier 3 for a production-instructions typo despite explicit tiny/local/no-data/local-boundary facts. The router preserves the heavy route. | In-memory reproduction; `scripts/risk_classifier.py` combines text/path and fact tiers with `max`; `SKILL.md` treats it as a floor. |
| <a id="r24"></a>R24 | A label typo in `.tsx`, spacing in `.css`, and a comment typo under `src/auth/` select required specialists with formal handoff. Task preparation and assignment also independently resolve upstream versions. | Pure `select_specialists` reproductions; tracing `specialist_manager.py` and `specialist_handoff.assign`. Network latency was not benchmarked. |
| <a id="r25"></a>R25 | Tier 2/3 requires two evidence items and two semantic families. Two passing integration/contract items can be blocked solely by the family quota; schema-3 resolution delegates to the same gate. | In-memory declared-gate reproduction and schema-3 call tracing in `receipt_validation.py`. This is not a requirement for two automated tests: review can be a family. |
| <a id="r26"></a>R26 | `evidence_capture.capture` sends stdout/stderr to `DEVNULL` and retains a generic nonzero-exit reason. Checks without their own report lose actionable failure output. | Code tracing and existing fixture expectations; no claim about a particular user's failed test. |
| <a id="r27"></a>R27 | `validate-skill.yml` and `cross-platform-smoke.yml` run on unrestricted push and pull-request events. README-only PR #98 ran each twice: two validation jobs plus eight platform jobs. | Workflow definitions and [push](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/37600141507)/[PR](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/37600148384) validation and [push](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/37600141467)/[PR](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/runs/37600148420) platform runs for head `16497316b454a00a195d87915e264228a3e0c989`. This overhead belongs to the Skill repository. |

Additional instruction ambiguity supports R25: `packs/browser-js.md` lists configured build/lint/typecheck as required without a stage distinction, while the core asks for the cheapest relevant check. This establishes conflicting pressure, not proof that every agent executes all checks. Do not infer all project delays from these findings.

## R23: Risk grounded in actual change

<a id="t1-risk-grounded-in-actual-change"></a>

**Priority:** Very high. **Complexity:** Medium. **Dependency:** None.

**Correction:** Treat keywords and paths as discovery signals; distinguish discussion of a sensitive domain from changing its behavior. Use verified operation, affected behavior, data, environment and boundary facts to resolve incidental signals. Do not create another keyword allowlist or let a caller's unsupported `tiny` claim override actual sensitive/destructive effects.

**Components:** `scripts/risk_classifier.py`, affected context-router/planner and retained-state callers; `SKILL.md`, risk/classifier guidance and existing routing/risk fixtures.

**Acceptance:**

- Documentation and comment-only changes with inspected non-runtime scope use a focused route even when their text/path mentions authentication or production. Ambiguous scope remains explicit rather than silently downgraded.
- Real authorization, destructive-data, financial and production changes retain the appropriate controls despite cosmetic wording. Equivalent semantic facts behave consistently across supported task wording.
- Routing, planning and retained state agree. Previously retained false escalation can be reconciled explicitly with evidence; actual protected obligations and known material risk cannot disappear.

**Verification:** Extend the existing classifier/router/plan-state cases with paired harmless and real-risk scenarios. Exercise the affected portable route if runtime behavior changes. Do not run live services or broad suites merely to test classification.

## R24: Lightweight specialist participation

<a id="t2-lightweight-specialist-participation"></a>

**Priority:** High. **Complexity:** Medium. **Dependency:** Accepted R23 risk/scope semantics.

**Correction:** Separate use of accepted specialist guidance from a new formal domain assignment. Mechanical edits within settled decisions reuse the applicable guidance; new domain decisions or material boundary changes retain scoped assignment and Head acceptance. Reuse a valid freshness/compatibility result within the same assignment instead of repeating identical upstream checks.

**Components:** `scripts/specialist_manager.py`, `scripts/specialist_handoff.py`, routing callers, `config/specialists.json`; Head/composition/authority instructions and existing specialist/handoff fixtures.

**Acceptance:**

- A verified label, spacing or comment-only correction does not acquire a full assignment solely from its extension/directory. Material UI flows, permissions or public contracts still select the appropriate specialist.
- Head authority, one UI/UX specialist and latest-stable/default-branch policy remain. Current guidance is reused; no fixed specialist version pin, skipped required finding or broad autonomous delegation is introduced.
- Preparation and assignment can share a result while source, local resources, controls and scope remain valid. Changed inputs invalidate reuse. Preserve task-start freshness, due inventory and stable instructions during an assignment; cached or offline evidence must be labeled accurately.
- Existing formal assignments retain their commitments until explicit reconciliation; the lightweight route does not silently abandon accepted work.

**Verification:** Reuse selection, compatibility, resource-change and handoff tests. Add a same-assignment duplicate-resolution check with a stubbed upstream and paired small/material domain cases. No real downloads, host installs or model evaluation are needed for these regressions.

## R25: Outcome- and stage-based verification

<a id="t3-outcome--and-stage-based-verification"></a>

**Priority:** High. **Complexity:** Medium. **Dependency:** R23/R24 scope and participation decisions.

**Correction:** Use one canonical policy to derive checks from acceptance, material failure modes, affected boundaries and delivery stage. Remove fixed evidence-count/family requirements where they manufacture unrelated work; require independent corroboration when an identified risk or explicit project policy warrants it. Packs/specialists contribute relevant risks, not additive default suites. Separate everyday selection guidance from conditional receipt/release details.

**Components:** `scripts/completion_gate.py`, `scripts/receipt_validation.py`, affected behavior/plan/state callers; `SKILL.md`, execution/verification and shared-format guidance, relevant packs and existing completion/receipt tests.

| Context | Default verification | Escalation condition |
|---|---|---|
| Mechanical text/visual change | Concrete focused observation; normally no new automated test. | Behavior, accessibility, security, data or configuration impact. |
| Build / defect correction | Smallest existing check or missing regression that can falsify the change. | Failure, new risk or broader affected boundary. |
| Feature completion / integration | Relevant affected regressions and changed contracts/boundaries. | Shared dependencies or consequential cross-area impact. |
| Publication | Release-relevant build, final-artifact/security and core-flow checks; migration/recovery when applicable. | Actual target/product requirements. |
| Sensitive behavior at any stage | Relevant denial, integrity, idempotency or recovery evidence. | Do not postpone these checks until publication. |

**Acceptance:**

- Sufficient relevant evidence can satisfy the accepted outcome without manufacturing a second family. Missing, failed, stale or unrelated evidence still cannot satisfy a required outcome; provenance and actual receipt validation remain enforced.
- A stage transition alone does not force a rerun. Unchanged scoped inputs/artifacts and relevant context permit reuse; changed dependencies invalidate affected evidence. A finished implementation stage cannot claim release readiness.
- Check expansion names the changed risk, failed check, affected boundary or explicit project requirement. No fixed test count/coverage target or mandatory new per-edit planning document is added.
- New and retained completion routes have an explicit policy/compatibility decision; do not bypass schema 3, drop accepted obligations or resurrect old success claims to obtain a pass.

**Verification:** Adjust current gate/receipt tests to assert sufficient outcome coverage and rejection of missing real obligations, rather than quotas. Preserve existing stale-input, failed-check, handoff/resume and manual-route cases. Test policy decisions/observable behavior, not exact prose.

## R26: Bounded execution diagnostics

<a id="t4-bounded-execution-diagnostics"></a>

**Priority:** Medium. **Complexity:** Medium. **Dependency:** R25's evidence boundary; prefer the existing receipt format unless a documented compatible change is necessary.

**Correction:** Make bounded local command diagnostics available from the original execution. Keep output outside product source, with explicit truncation/retention and sensitive-output handling. Do not collect environment dumps, upload logs automatically or treat printed success as execution evidence.

**Components:** `scripts/evidence_capture.py`, receipt-validation/storage consumers only where needed, execution guidance and existing collector/receipt/portable fixtures.

**Acceptance:**

- A failing command without a separate report provides an actionable stdout/stderr diagnostic without rerunning solely to see it.
- Output limits are enforced while reading, with truncation visible; verbose output cannot create unbounded memory/disk use or deadlock. Timeout/process cleanup and exit-status distinctions remain accurate.
- Diagnostics stay local and respect sensitive-output controls. Existing receipts remain readable; added diagnostics do not loosen command, input or artifact qualification.

**Verification:** Extend the existing collector fixtures with ordinary failure, bounded verbose output, separate streams and timeout cases; reuse process-tree and receipt-integrity coverage. No new logging service or unrelated test suite.

## R27: Change-aware CI and release checks

<a id="t5-change-aware-ci-and-release-checks"></a>

**Priority:** Medium. **Complexity:** Medium. **Dependency:** Follow R26 in delivery order; technically independent of its runtime implementation.

**Correction:** Distinguish overview-only documentation, executable/routed skill instructions, runtime/packaging and release changes. Remove redundant branch/PR runs, select affected checks and retain a complete exact-revision publication route. A `.md` extension alone does not establish a harmless change: this repository's Markdown can be runtime instructions.

**Components:** `.github/workflows/validate-skill.yml`, `cross-platform-smoke.yml` and dependent release/contract workflows as needed; `scripts/release_readiness.py` only if its interface changes; contributor/validation guidance and existing workflow checks.

**Acceptance:**

- README/roadmap-only edits receive accurate structure/link/mirror checks without a full runtime suite or OS matrix. Changes to `SKILL.md`, routed policies, scripts, config, packaging or workflow logic still trigger their meaningful affected verification.
- A PR branch does not run the same baseline redundantly on push and PR events. Preserve verification of the intended merge result; obsolete runs may be cancelled without cancelling required publication evidence.
- Required-check names/statuses and branch protection cannot become indefinitely pending because of filters. Skipped/unavailable checks are not fabricated passes. Confirm actual repository protection before changing triggers.
- Publication still gathers all required workflows on the exact final revision and performs the native Trivy final-target scan. Selective development CI must not strand or weaken release readiness.

**Verification:** Inspect representative changed-path/event cases for docs, runtime, instructions and release. Reuse existing workflow/readiness fixtures; confirm actual affected CI when the authorized PR runs. Do not start duplicate live workflows solely to populate this plan.

## Implementation and validation boundaries

Start only R23 when implementation is requested. Reconfirm its smallest reproduction, implement, run affected checks and review before moving on in the approved sequence. Reuse existing tests and record only meaningful new failure scenarios. Broader required integration/publication checks belong at their existing gates, not after every edit. This cycle has no model evaluation, provider-key requirement, new scanner or test framework.

When a runtime resource changes, update canonical source and the portable mirror together and check the affected extracted entrypoint. Preserve release/local installation separation. Record measured command duplication or relevant elapsed time only when actually observed; do not promise a percentage improvement from source inspection.

The current instruction system already supports scoped evidence reuse, recovery and conditional product-installation checks. Preserve those mechanisms rather than replacing them. Historical partial-release retry concerns and other unverified ideas are outside this cycle.

## Current contract ownership

| Mechanism | Canonical instructions | Boundary to preserve |
|---|---|---|
| Formats / migration | [Shared contracts](../../references/shared-improvement-contracts.md) | Explicit identity, compatibility and trust limits; records grant no permissions. |
| Observable outcomes | [Behavior contract](../../references/operating-model.md#observable-behavior-contract) | Required behavior and material failures; tiny tasks can remain inline. |
| State / recovery | [State](../../references/project-state-automation.md), [recovery](../../references/recovery-and-resume.md) | Retain accepted criteria, required findings and scope across resume/reconciliation. |
| Execution / completion | [Collection](../../references/execution-and-verification.md#local-execution-receipts-e1), [completion](../../references/execution-and-verification.md#receipt-backed-completion-e2) | Actual outcomes, current scoped inputs/artifacts and truthful manual/legacy labeling. |
| Specialist acceptance | [Composition](../../references/specialist-composition.md), [authority](../../references/specialist-authority.md) | Head ownership and appropriate current guidance; retained formal commitments need explicit reconciliation. |
| Publication / installation | [Native release gate](../../references/security-and-dependencies.md#native-release-gate), [product installation](../../references/product-installation-and-runtime.md) | Real final-target security and selected exact-artifact/runtime evidence. |

## Delivered specifications

Closed [R18-R22 specifications and evidence](improvement-plan-through-1.5.0.md), [earlier implementation history](improvement-plan-through-1.4.0.md) and [delivery records](improvement-roadmap-through-1.5.0.md) remain available. Their old next-action/installation statements are historical snapshots. The [current roadmap](../../ROADMAP.md) is the only progress tracker.
