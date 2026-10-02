# Execution and Verification

## Walking skeleton

For a new application, prove the narrowest useful end-to-end path early:

`App → Infrastructure → Data Store → Core Request → Persist → Read → Response/UI`

Choose this slice from the agreed [observable behavior contract](operating-model.md#observable-behavior-contract): exercise the actor's action and inspect the promised result, including state preservation where relevant.

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

### From observable criterion to a check

For each required outcome, identify the observable assertion and choose the cheapest check that could falsify it. Inspect existing coverage first: a passing build or unrelated test is not evidence for a save, permission or data-retention outcome. A rendered/manual check can suffice for a visual correction. A denied write requires evidence that the protected value stayed unchanged, not just an error message.

Use the exact reported state/action for defects and the applicable boundary for material failures. Keep intended behavior separate from the actual result; a criterion stays unmet or unverified when its check fails or cannot run. Do not add new cases solely to populate an example, stage or risk-tier quota.

In current schema-2 completion reports, keep observable required outcomes in the existing criterion `description`, with stable `id`, `required`, actual `met` and linked `evidence_ids`. Use separate criteria only for distinct required outcomes. The gate itself does not validate `behavior` fields or resolve receipts; extra fields cannot substitute for a clear description, retained baseline or meaningful evidence. B2 preserves validated task behavior in plans/state/handoffs and labels imported schema-2 outcomes as reported, never receipt-verified. E1/E2 add execution collection/validation separately.

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

For roadmap implementation, [shared improvement contracts](shared-improvement-contracts.md) defines the behavior/receipt formats and migration. E1 records local execution; the current schema-2 gate still checks declared evidence/provenance and does not resolve receipts. E2 supplies that separate completion capability.

### Local execution receipts (E1)

Use `scripts/evidence_capture.py` only for a relevant, already-authorized local check whose retained task contract has an `origin: collected` obligation. It never executes command text from a contract/report, grants permissions, starts remote verification or changes task completion. A tiny visual/manual task need not use this runner or add an automated test.

The requirement's `input_paths` must cover relevant source, configuration, dependencies and test definitions; `input_excludes` are explicit justified subtree exclusions. Use concrete project-relative forward-slash paths, not globs, absolute input paths or parent traversal. Capture includes relevant untracked/ignored files and directory membership. At least one regular file must be in scope; missing expected files are recorded alongside it. Do not include secrets or generated receipts/logs. Scope/check relevance belongs to the Head, not a hashing algorithm.

Example contract obligation (within an accepted version-1 task contract):

```json
{"id":"settings-check","criterion_ids":["settings-preserved"],"kind":"unit-test","origin":"collected","required":true,"input_paths":["src/settings","tests/settings_test.py","pyproject.toml"],"input_excludes":[]}
```

Run the explicit command after `--`, from an explicit project root (optional `--cwd` stays inside it):

```bash
python /path/to/skill/scripts/evidence_capture.py run --root /path/to/project --task-contract /path/to/local/task.json --requirement settings-check --timeout 60 -- python -m unittest tests.settings_test
```

The runner uses argument-list execution with `shell=False`, closed stdin and discarded stdout/stderr; it does not use an output pipe or unlimited log. Prefer a checked-in test script rather than a long inline command. Never put credentials in command arguments, contract/context values or unavailable reasons: these are stored exactly. The command inherits the current environment without recording it; use existing host controls for secret access. Optional `--context` accepts an explicit JSON object with relevant runtime/check/dataset identity, not an environment dump. Hashes cannot identify mutable remote service/dataset state unless the Head supplies the relevant identity and check.

Results are `pass`, `fail`, `timeout`, `error` or `unavailable`. A pass requires exit code zero, unchanged scoped input/artifact snapshots and complete collection. A zero exit code does not prove assertion relevance, coverage or product acceptance. Timeout attempts terminate the launched process group/tree and record whether termination was confirmed; this runner is not a sandbox against a process escaping that group/tree. No automatic retry follows. The command timeout defaults to 60 seconds and must be finite, positive and at most 86,400 seconds. Collection is bounded to 10,000 manifest entries and 1 GiB of hashed input bytes per snapshot; exceeding a limit is an error, never a narrower successful receipt.

`artifact_paths` names the exact preexisting files being checked, either relative to the project or explicit authorized absolute files. Capture hashes them before and after; a missing/changed artifact is an error. Build/package first, then run the check against those exact bytes. Artifact lists have the same count/total hashing bound. For an installable WordPress ZIP, add `--wordpress-artifacts` to reuse `wordpress_artifact.py` validation/version identity; ZIP inspection is bounded to 10,000 entries, 1 GiB expanded size and 8 MiB per PHP member. Packaging/version evidence does not establish installation, runtime or seeded-data preservation.

Receipts are unique JSON files under the existing external local project workspace, `test-artifacts/receipts/<task-hash>/`. Task IDs are hashed for safe, short paths, with full task/contract identities retained in each receipt. An explicitly configured local workspace inside product source is rejected. The command returns receipt identity/digest and its local reference/root; it does not write product documents, modify Git excludes, invoke another agent or claim completion. Store referenced receipts under project retention rules; host write controls remain necessary because a privileged writer can forge records and inputs.

When a collected check cannot run, record the actual limitation without inventing a command, exit code or input snapshot:

```bash
python /path/to/skill/scripts/evidence_capture.py unavailable --root /path/to/project --task-contract /path/to/local/task.json --requirement settings-check --reason "Required runtime is unavailable on this host"
```

The CLI exits zero only for a collected pass, and two for other results/configuration errors. E1 does not relabel manual/reported obligations, import CI results, or treat its receipts as schema-2 completion evidence automatically. Manual/legacy routes remain available under their existing rules. E2 must resolve receipt/contract/requirement identities and recompute relevant input/artifact/context bindings at delivery; E1 collection alone cannot establish later freshness.

`Done` requires at least one required acceptance criterion; an all-optional checklist cannot pass. For Tier 2/3 or scope-changing work, retain the approved criteria before implementation and pass that independently retained JSON array to `completion_gate.py report.json --acceptance-baseline approved-criteria.json --json`. The gate blocks removed, downgraded, or rewritten required outcomes. The caller must protect that baseline from implementation edits; the gate reports whether it was supplied and does not authenticate an agent-written checklist by itself.

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
