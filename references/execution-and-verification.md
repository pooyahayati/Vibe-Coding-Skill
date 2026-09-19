# Execution and Verification

## Walking skeleton

For a new application, prove the narrowest end-to-end path early:

`App → Infrastructure → Data Store → Core Request → Persist → Read → Response/UI`

Do not build broad horizontal layers before one useful vertical slice works.

## Verification priority

Prioritize core business logic, critical integrations, regression paths, the main happy-path end-to-end, then extras where failure cost justifies them.

## Evidence hierarchy

Strong evidence:
- deterministic tests;
- reproducible build;
- security scanner;
- migration validation;
- health/smoke checks;
- concrete logs/metrics.

Weak evidence:
- agent statement;
- "looks correct";
- generated code;
- passing unrelated tests.

## Review

For meaningful changes, review requirement fit, correctness, unintended scope, architecture fit, error handling, tests, security, maintainability, and operational impact.

For Tier 2/3 work, prefer an independent reviewer/agent when available.

## Change budget

Use diff size as a signal, not an absolute quality metric.

Watch changed file count, added/deleted lines, modules touched, public contracts, manifests, migrations, auth/security, and CI/deployment.

If the change is too broad to review confidently, split it before integration.

## Debugging

`Reproduce → Evidence → Failing Layer → Root Cause → Smallest Safe Fix → Test → Regression Test`

Do not log secrets or unnecessary sensitive data.

## Performance

`Baseline → Change → Compare`

Do not optimize based on intuition alone.

## Data integrity

For schema/data changes verify migration reproducibility, referential integrity, uniqueness, import/export assumptions, backup/restore needs, and no unintended data loss.

Destructive migrations require explicit approval and recovery planning.

## Release gate

Before release, verify what is relevant: core workflow, tests, integration, no critical bug, security checks, reproducible deployment, environment documentation, migrations, rollback/recovery, and repository state.

## Deployment verification

`Deploy → Health Check → Smoke Test → Core Workflow → Accept`

If verification fails and rollback is safer, stop and roll back rather than layering speculative fixes in production.
