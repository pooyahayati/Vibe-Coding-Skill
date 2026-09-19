# Risk and Autonomy

## Principle

User autonomy preference does not override task risk.

Effective permission is:

`User Preference × Task Risk × Action Risk × Environment Risk`

## Tier 0 — Tiny

Local, reversible, no security/data/architecture effect, very small diff.

Required:
`Understand → Change → Focused Check`

## Tier 1 — Standard

Normal feature with bounded module impact.

Required:
`Objective → Acceptance → Impact → Implement → Test → Review`

## Tier 2 — Significant

Any of:
- auth/authorization;
- schema/migration;
- multiple modules;
- new external integration;
- architectural contract;
- meaningful dependency;
- public API;
- background job;
- production-affecting configuration.

Required:
- explicit spec;
- impact/graph analysis;
- implementation plan;
- stronger testing;
- independent review where possible;
- security/regression checks.

## Tier 3 — Critical

Any of:
- destructive data operation;
- material production blast radius;
- sensitive personal/financial/security data;
- irreversible operation;
- IAM/secret/control-plane change;
- safety-critical behavior.

Required:
- explicit approval;
- rollback/recovery plan;
- strong evidence;
- human review when available;
- fail closed on missing critical verification.

## Approval classes

Routine — autonomous when permission exists:
- reading;
- local edits;
- tests;
- lint/format;
- low-risk fixes;
- reversible refactors.

Technical — normally autonomous; record significant decisions:
- local implementation detail;
- test structure;
- low-risk dependency patch update.

Product/Architectural — approval required unless already decided:
- scope change;
- removing a requirement;
- language/framework/database change;
- core architecture;
- security posture;
- destructive migration;
- significant recurring cost;
- production deployment;
- high-risk irreversible action.

## Fail-open vs fail-closed

Fail closed when missing evidence could reasonably cause data loss, privilege escalation, secret exposure, production outage, irreversible migration, or unsafe release.

Fail open with warning for non-critical tooling when a safe manual fallback exists.

## Multi-agent trigger

Use more than one agent only when the expected benefit exceeds coordination cost.

Valid reasons: independent review, specialist analysis, parallel tasks with clean boundaries, context isolation.

## Circuit breaker

Escalate after three materially different failed fixes, repeated tool failure without fallback, contradictory evidence, unexpected scope expansion, or a required approval boundary.
