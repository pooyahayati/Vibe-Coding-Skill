# Execution and Verification

## Walking skeleton

For a new application, prove the narrowest useful end-to-end path early:

`App → Infrastructure → Data Store → Core Request → Persist → Read → Response/UI`

Do not build broad horizontal layers before one useful vertical slice works.

## Testing policy

### Core rule

Derive verification from:

`changed behavior + important failure modes + integration boundaries + acceptance criteria`

Do **not** derive the number of tests from changed file count, lines of code, project size, or a fixed coverage percentage.

"Test count" is ambiguous: commands, test functions, parameterized cases, and behavioral scenarios are different measures. Optimize for detection power, not count.

### New-test rule

Use:

`New scenarios = required scenarios not already covered + new regression scenarios + relevant new boundary scenarios − duplicates`

An existing test is sufficient when it exercises the same behavior and would detect the same meaningful failure mode. Do not rewrite or duplicate equivalent tests merely to increase evidence volume.

A new test should expose behavior or a failure mode, not mirror internal implementation structure.

## Verification by change type

| Change type | New tests usually needed | Checks to execute |
|---|---|---|
| Text/copy/isolated visual spacing | usually zero | focused rendered/visual check + directly relevant existing check if any |
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

### During implementation

Run the smallest test/check that can falsify the change quickly. Prefer focused unit/component/reproduction checks over repeatedly running the entire suite.

### Before integration

Run the affected-area regression set plus checks for changed contracts, data boundaries, security boundaries, or integrations.

### Before release/deployment

Run release-relevant build, migration, security, integration, smoke/health, and recovery checks according to risk and what changed.

Do not repeat an expensive full suite after every edit when no affected behavior has changed since the last run.

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

### Completion evidence kinds

The Completion Gate accepts a controlled semantic evidence taxonomy rather than arbitrary free-form kind names. Supported kinds map into broader families such as verification, integration, delivery, review, security, runtime, data, recovery, performance, static analysis, and manual/visual checks.

For higher-risk completion, diversity is measured by **semantic evidence family**, not by raw labels. For example, `test` and `regression-test` both belong to the verification family and cannot satisfy a two-family requirement by themselves. Unknown evidence kinds do not qualify.

This prevents unrelated or invented labels from manufacturing evidence diversity while still allowing the evidence type appropriate to the actual change.

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

For Tier 2/3 work, prefer an independent reviewer/agent when available.

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

Before release, verify only what is relevant to the changed product: core workflow, affected regression, integrations, build/deployment, security, migrations, recovery, environment documentation, and repository state.

A broad suite may still be required by project policy; do not confuse that policy requirement with evidence that every test was newly necessary for this change.

## Deployment verification

`Deploy → Health Check → Smoke Test → Core Workflow → Accept`

If verification fails and rollback is safer, stop and roll back rather than layering speculative fixes in production.
