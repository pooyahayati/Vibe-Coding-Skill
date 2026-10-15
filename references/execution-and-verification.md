# Execution and Verification

## Walking skeleton

For a new application, prove the narrowest useful end-to-end path early:

`App → Infrastructure → Data Store → Core Request → Persist → Read → Response/UI`

Choose this slice from the agreed [observable behavior contract](operating-model.md#observable-behavior-contract): exercise the actor's action and inspect the promised result, including state preservation where relevant.

Do not build broad horizontal layers before one useful vertical slice works.

## Testing policy

### Core rule

Derive verification from:

`accepted outcomes + material failure modes + affected boundaries + delivery stage + explicit project requirements`

This is the canonical check-selection policy for the Head, capability packs and specialists. Do **not** derive a quota from changed file count, lines of code, project size, risk tier, evidence count/families or coverage percentage. A configured command is available, not automatically required for every edit. Packs contribute applicable risks and assertions; their activation does not require every listed check.

"Test count" is ambiguous: commands, test functions, parameterized cases, and behavioral scenarios are different measures. Optimize for detection power, not count.

### New-test rule

Use:

`New scenarios = required scenarios not already covered + new regression scenarios + relevant new boundary scenarios − duplicates`

An existing test is sufficient when it exercises the same behavior and would detect the same meaningful failure mode. Do not rewrite or duplicate equivalent tests merely to increase evidence volume.

A new test should expose behavior or a failure mode, not mirror internal implementation structure.

### From observable criterion to a check

For each required outcome, identify the observable assertion and choose the cheapest check that could falsify it. Inspect existing coverage first: a passing build or unrelated test is not evidence for a save, permission or data-retention outcome. A rendered/manual check can suffice for a visual correction. A denied write requires evidence that the protected value stayed unchanged, not just an error message.

Use the exact reported state/action for defects and the applicable boundary for material failures. Keep intended behavior separate from the actual result; a criterion stays unmet or unverified when its check fails or cannot run. Do not add new cases solely to populate an example, stage or risk-tier quota.

Name the required outcome, changed risk/boundary, observed failure or explicit project rule that justifies expanding checks. Use the existing plan/requirement description when one exists; no per-edit checklist or new document is required. If a consequential risk or project rule requires independent corroboration, retain that specific review/observation as a required obligation linked to its outcome. Different evidence labels do not prove independence; assess the actual reviewer/source and detection value. This does not authorize another agent or model evaluation.

For the supported legacy schema-2 route, keep observable required outcomes in the criterion `description`, with stable `id`, `required`, actual `met` and linked `evidence_ids`. Use separate criteria only for distinct required outcomes. This route validates declared linkage/provenance, not `behavior` fields or actual receipts; extra fields cannot substitute for a clear description, retained baseline or meaningful evidence. B2 preserves validated task behavior in plans/state/handoffs and labels imported schema-2 outcomes as reported, never receipt-verified. New structured completion uses the [E2 schema-3 route](#receipt-backed-completion-e2) with independently retained criteria and local receipts; it still requires Head judgment about check relevance.

## Verification by change type

| Change type | New tests usually needed | Checks to execute |
|---|---|---|
| Text/copy/isolated visual spacing | usually zero | one focused source/rendered observation; another check only if it adds needed detection value |
| Reproducible bug fix | regression scenario for the defect; extra edges only when root cause justifies them | failing reproduction/new regression + affected existing tests |
| New local logic | uncovered meaningful input/boundary classes | lowest suitable unit/component tests |
| API/integration change | contract and important failure/timeout/auth cases not already covered | component/contract tests + focused integration check |
| Auth/authorization | allow + deny + role/tenant boundary relevant to the change | security-focused regression + affected integration tests |
| Persistence/schema/migration | invariants, migration/rollback or recovery cases relevant to risk | migration/data-integrity checks + affected domain tests |
| Payment/stateful webhook | idempotency, authentication, retry/failure, state consistency where relevant | contract/integration tests + state/recovery checks |
| Build/deployment/config | failure-prone configuration and compatibility cases | build + smoke/health + rollback/recovery evidence when risk requires |
| Refactor with no intended behavior change | only gaps discovered during impact/root-cause analysis | affected regression suite; compare observable behavior |

The table sets a floor only where the concern exists. Do not add every listed test type to every task.

## Stage-specific execution

| Stage / target | Select | Expand only for |
|---|---|---|
| Build / defect correction | Cheapest existing observation or focused regression that can falsify the change. | An uncovered outcome, failure, changed boundary or explicit project requirement. |
| Verify / Review / integration | Evidence for all accepted outcomes and affected contracts/invariants; reuse valid earlier results. | Missing coverage, an identified risk needing independent corroboration, or mandatory project checks. |
| Ship / publication | Relevant production build, final-artifact/security and core-flow evidence; installation, migration/recovery when applicable. | The actual delivery target and its retained requirements. Implementation completion does not establish release readiness. |
| Sensitive behavior at any stage | Relevant denial, state integrity, idempotency or recovery cases. | Do not postpone an affected security/data control until publication. |

Publication additionally requires the [native Trivy release gate](security-and-dependencies.md#native-release-gate), bound to the final delivery source/artifact as required security evidence. A successful compatibility smoke or an install warning does not qualify. Keep native application security checks; tool/scan unavailability blocks publication without blocking unrelated development.

An activity-stage change alone does not invalidate evidence. Reuse it while its scoped source, test definitions, configuration/dependencies, artifact and relevant runtime/dataset context still match. Recheck affected evidence after those inputs change; unrelated edits do not force reruns. Do not change a retained contract or runtime context merely to record a new activity stage. Changing the actual outcome or delivery target does require explicit reconciliation; old task receipts cannot be relabeled to satisfy new release obligations.

## Verification priority

Prioritize:

1. acceptance behavior;
2. root-cause regression for defects;
3. core business invariants;
4. changed trust/data/integration boundaries;
5. main happy-path end-to-end when it provides unique detection value;
6. broader regression where failure cost or change impact justifies it.

## Deduplication and stopping rule

Before adding a test, ask:

- Which acceptance criterion or failure mode does this detect?
- Is that behavior already detected by an existing test at an equal or better level?
- Is a cheaper/lower-level test sufficient?
- Does this test cover a real boundary, or only restate implementation details?

Stop verification when:

- every required acceptance criterion has qualified evidence;
- identified risk-relevant failure modes are covered;
- changed integration/data/security boundaries have relevant evidence;
- no required check is failing or unverified.

Do not continue merely to reach a target test count, test pyramid ratio, or coverage percentage. Coverage may reveal blind spots; it is not an acceptance criterion by itself unless the project explicitly defines one.

## Evidence hierarchy

Strong evidence:

- deterministic behavior/regression tests;
- reproducible build;
- contract/integration checks;
- security scanner tied to the relevant surface;
- migration/data-integrity validation;
- health/smoke/recovery checks;
- concrete logs/metrics for runtime behavior.

Weak evidence:

- agent statement;
- "looks correct";
- generated code;
- passing unrelated tests;
- duplicated tests with the same detection power.

Evidence used for completion should link to the acceptance criterion it proves.

For roadmap implementation, [shared improvement contracts](shared-improvement-contracts.md) defines the formats and migration. E1 records local execution; E2 resolves local receipts for schema-3 tasks. In-flight schema-2 checks remain explicitly declared evidence.

### Local execution receipts (E1)

For an already-authorized check with a retained collected-evidence obligation, read [local execution receipts](execution-receipts.md#local-execution-receipts-e1). Tiny/manual work does not acquire a runner or new automated test merely from this format.

`Done` requires at least one required acceptance criterion; an all-optional checklist cannot pass. Schema 3 uses its independently retained task contract. For legacy schema-2 Tier 2/3 or scope-changing work, supply the approved criteria with `--acceptance-baseline`; the gate rejects removed, downgraded or rewritten required outcomes. Protect the baseline from implementation edits: structural checks do not authenticate an agent-written checklist.

### Completion evidence kinds

The Completion Gate accepts a controlled semantic evidence taxonomy rather than arbitrary free-form kind names. Supported kinds map into broader families such as verification, integration, delivery, review, security, runtime, data, recovery, performance, static analysis, and manual/visual checks.

The gate reports counts and families for interpretation, not quotas. One relevant, qualified check can cover a required outcome; multiple integration/contract checks may cover distinct outcomes without adding an unrelated review or test type. Every explicitly required check and schema-3 retained obligation must still qualify. Failed, missing or stale required evidence cannot be offset by extra passing items; required provenance remains risk-dependent. Unknown evidence kinds do not qualify.

Results identify `verification_policy: outcome-and-obligation-v1` and a task/criteria `completion_scope`. A pass covers only those accepted outcomes, not later merge/publication/deployment targets or permission to perform them.

## Review

For meaningful changes, review requirement fit, correctness, unintended scope, architecture fit, error handling, tests, security, maintainability, and operational impact.

For code-structure review, check only observable properties relevant to the change:

- responsibilities are understandable;
- new boundaries/abstractions map to a real requirement, ownership boundary, failure mode, testing need, or established repetition;
- important data/state ownership and cross-boundary contracts are explicit;
- entry inputs are validated at the owning boundary;
- boundary failures are diagnosable without secret leakage;
- concern-specific controls (timeouts/retries, transactions, tenant isolation, performance structure) exist only when that concern is present;
- no unused interface/repository/service/layer/message-bus/deployment abstraction was added for ceremony.

Use independent corroboration for a named consequential risk or explicit project requirement, as defined in the testing policy above. Retain already accepted review obligations; do not add another review merely to create a second evidence family.

## Change budget

Use diff size as a signal, not an absolute quality metric.

Watch changed file count, added/deleted lines, modules touched, public contracts, manifests, migrations, auth/security, and CI/deployment.

If the change is too broad to review confidently, split it before integration.

## Debugging

`Reproduce → Evidence → Failing Layer → Root Cause → Smallest Safe Fix → Regression Scenario → Verify`

Do not log secrets or unnecessary sensitive data.

## Performance

`Baseline → Change → Compare`

Do not optimize based on intuition alone.

## Data integrity

For schema/data changes verify migration reproducibility, referential integrity, uniqueness, import/export assumptions, backup/restore needs, and no unintended data loss.

Destructive migrations require explicit approval and recovery planning.

## Release gate

### Receipt-backed completion (E2)

For schema-3 completion, manual observations or retained schema-2 migration, read [receipt resolution and compatibility](execution-receipts.md#receipt-backed-completion-e2). All retained required obligations still apply; task acceptance does not imply publication readiness.

Before release, verify only what is relevant to the changed product: core workflow, affected regression, integrations, build/deployment, security, migrations, recovery, environment documentation, and repository state.

A broad suite may still be required by project policy; do not confuse that policy requirement with evidence that every test was newly necessary for this change.

## Deployment verification

For a selected product-installation or local container outcome, follow `references/product-installation-and-runtime.md` and retain its real startup/core-workflow evidence in the existing completion route. A local run proves only the verified local target; production deployment needs its own relevant evidence.

`Deploy → Health Check → Smoke Test → Core Workflow → Accept`

If verification fails and rollback is safer, stop and roll back rather than layering speculative fixes in production.
