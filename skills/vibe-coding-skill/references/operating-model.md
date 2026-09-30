# Operating Model

## Primary objective

Build the smallest reliable product or change that achieves the required user outcome with minimum total complexity.

Every meaningful milestone should be Runnable, Testable, Demonstrable, and Diagnosable.

## Current Objective

Maintain exactly one Current Objective. Every active task must support it directly or be identified as necessary enabling work.

## Startup interaction contract

For a new project or other material body of work, explain four things in a few sentences before implementation:

1. what will be delivered;
2. the recommended approach or technology and the main reason for it;
3. the first visible/runnable result;
4. how that result will be accepted.

Do not delegate inferable implementation details to the user. Ask for a product, data, security, scope, or recurring-cost decision only when it is materially user-owned.

Seek approval for a material decision once with a concrete option. Do not repeatedly reopen a decision that is already settled unless new evidence materially changes it.

Within approved boundaries, choose routine implementation details autonomously.

## Discovery stop condition

Discovery is complete when problem, primary user, core outcome, core workflow, MVP boundary, critical constraints, and observable success criteria are clear enough to make an implementation decision.

Do not continue discovery merely to produce more documentation.

## Requirements discipline

Classify requirements as Must, Should, Could, Later, or Rejected. Do not silently remove requested behavior.

After MVP approval, new non-essential features go to backlog unless the core outcome cannot work without them.

## Solution and technology selection

Technology selection is a short decision, not a language popularity exercise.

Before choosing a new language, framework, service, or custom subsystem, check this order:

1. Can the existing product/platform already satisfy the need through configuration or a current capability?
2. Is there a reputable, bounded extension/plugin/package/service that satisfies it with acceptable ownership and exit cost?
3. Can a small extension to the existing stack satisfy it?
4. Only then consider a new custom stack or deployment unit.

For an existing product, keep the current stack unless there is a demonstrable blocker.

When a meaningful technology decision remains, compare **no more than two or three realistic options** against the constraints that actually matter:

- existing platform and conventions;
- workload/data shape and scale;
- deployment/runtime environment;
- required ecosystem/integrations;
- security, privacy, and data ownership;
- maintainer/team expertise;
- build and operational complexity;
- recurring/vendor cost and lock-in;
- migration and exit difficulty.

Verify current version/support status from official sources when the decision depends on it.

Do not assign one universal "best language" to small, medium, or large projects. Select databases separately from application language using the data model, transaction/concurrency needs, search/query needs, recovery, and deployment environment.

For uncertain performance or specialized workloads:

`Question → Minimal representative spike → Evidence → Decision`

### Decision record

Keep the decision concise:

- **Need/constraints**
- **Options considered** — maximum 3
- **Chosen option and why**
- **Nearest alternative rejected and why**
- **Evidence/assumptions that could change the decision**

Do not create a technology-comparison document when the existing stack is clearly adequate and no material technology choice exists.

## Architecture

Prefer the simplest architecture compatible with known requirements.

For multi-domain products, consider a modular monolith before distributed architecture.

Do not add by default microservices, CQRS, event sourcing, Kafka/RabbitMQ, Elasticsearch, Kubernetes, GraphQL, Redis, or new deployment units.

Before adding complexity, answer: Which current requirement requires this?

## Technical spikes

`Question → Minimal Experiment → Evidence → Decision`

A spike is bounded and disposable.

## Task sizing

Small: execute directly.

Medium: decompose when it improves ownership or verification.

Large: decompose before implementation.

Task/change scope is separate from repository size. A local task in a large repository may remain lightweight.

## Ready check

A task is Ready when objective, scope, dependencies, acceptance criteria, blockers, required verification, and expected output are clear enough to execute.

Otherwise clarify, split, spike, or mark Blocked.

## Stage interaction contract

Each stage has an inspectable output and an exit condition. Do not replace these with a long command log.

| Stage | Minimum input | Output | Exit criterion |
|---|---|---|---|
| Frame | user outcome + known constraints | Current Objective + acceptance direction | objective and MVP/change boundary are clear enough to decide |
| Decide | objective + material constraints | approach/technology decision only when needed | chosen path is defensible; user-owned material decision approved |
| Implement | ready task + relevant context | runnable/inspectable vertical result | requested behavior exists without known blocking defect |
| Verify | acceptance criteria + changed behavior/boundaries | relevant evidence linked to criteria | required scenarios pass or status is explicitly Unverified/Blocked |
| Integrate/Handoff | verified result + repository state | integrated state, limitation, readiness, next step | another competent agent/user can continue without hidden context |

At every stage report:

- actual result;
- relevant evidence;
- remaining limitation;
- readiness status;
- next useful step.

## Change impact

For significant work:

`Requirement → Product → Architecture → Module/Graph → Data/API → Tests → Deployment/Release`

Record only decisions that matter later.

## Stop conditions

Stop discovery when enough information exists to decide.

Stop implementation when acceptance criteria are implemented and no blocking defect is known.

Stop testing when all risk-relevant scenarios and boundaries have sufficient evidence; do not continue merely to increase counts or coverage percentages.

Stop refactoring when the requested change is safe, understandable, and maintainable.

Stop documentation when another competent agent can resume without hidden context.

Stop optimization until a meaningful baseline shows a problem.

## Blocker format

### Blocker
...

### Cause
...

### Evidence
...

### Options
A ...
B ...

### Recommendation
...
