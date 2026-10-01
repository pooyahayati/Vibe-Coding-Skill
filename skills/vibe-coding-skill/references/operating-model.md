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

## Observable behavior contract

During Define, reuse the current requirements/acceptance criteria and express the smallest observable outcome needed to choose an implementation and a useful check:

`Given <relevant starting state>, when <actor action>, then <observable result>; on <material failure>, <expected response and protected state>.`

This is a thinking aid, not a required template. Omit irrelevant starting/failure clauses. The actor can be a user, API caller, background job or downstream system; do not invent a UI for backend work. One clear existing description can be sufficient. Add a separate criterion only for a distinct necessary outcome, not to fill a checklist.

The Head translates intent into this contract from project evidence. Ask the user only for an unresolved material product decision, in ordinary language; infer implementation details and platform controls. Treat vague terms such as "fast", "easy" or "secure" as goals until tied to relevant observable behavior. Reuse supplied targets or existing service expectations; do not invent performance thresholds, roles, retention rules or new product features to make a criterion look precise.

For a defect, preserve the reported reproduction and supplied boundary values. For changed authorization, data or integration behavior, include the relevant denial, state preservation or failure result. Do not require a success/failure pair for a copy correction or add unrelated cases merely because the repository is large. Protected existing behavior remains part of the change boundary.

### Examples and the smallest useful check

| Changed behavior | Observable criterion | Relevant verification |
|---|---|---|
| Supplied label correction | Opening the affected settings page shows the supplied label; setting behavior remains unchanged. | Inspect that rendered page; reuse a relevant existing check. Usually no new automated test. |
| Duplicate-save defect | In the reported starting state, the reported repeated Save action creates one record and displays the saved result. | Reproduce that action and assert the stored record count/result; reuse coverage that detects the same defect. Add failure/retry cases only if the root cause or boundary warrants them. |
| WordPress protected-setting change | A user without the required capability attempts the change: it is denied and the stored value is unchanged; an authorized user can make the intended change. | Relevant allow/deny and stored-state checks using the actual platform capability. A message alone is not proof that data stayed unchanged. |

The examples illustrate how to choose evidence, not mandatory feature requirements or fixed test counts. Medium and large changes apply this reasoning to affected vertical slices and shared boundaries; project size does not require a contract for every file.

### Persistence proportional to risk

- For a tiny/local task, reuse a short task note or existing criterion; do not create a new project document or JSON record merely for this section.
- Keep durable product outcomes in the project's existing requirements, issue or `PROJECT.md` when they need to survive the task. Update an existing source of truth rather than copying requirements into several documents.
- For Tier 2/3 or scope-changing work, retain the accepted criteria before implementation using the existing [acceptance-baseline guidance](execution-and-verification.md#evidence-hierarchy). Local execution snapshots stay outside product source control. Reopen only a genuinely changed material user-owned decision.

Choose the first runnable slice and its check from the agreed action/result, then proceed once scope, observable expectations and material decisions are clear. Writing the contract is not evidence that the software satisfies it. Missing access or execution remains unverified.

This section implements B1's behavior guidance. B2 optionally preserves structured task contracts in [plans](context-routing-and-execution.md#retained-behavior-in-a-plan-b2) and [state/handoffs](project-state-automation.md#preserve-task-behavior-and-useful-delivery-details-b2). E1/E2 receipt collection/validation and S1/S2 specialist acceptance remain separate work. [Shared improvement contracts](shared-improvement-contracts.md) defines the fields; users do not need to fill records or choose a testing framework.

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

### Observable code-structure invariants

Use a small set of observable rules instead of prescribing a universal architecture:

1. **Clear responsibility** — a component/module should have one understandable reason to change at its current level of abstraction.
2. **Boundary ownership** — identify who owns important data/state and the contract used by callers across a meaningful boundary.
3. **Decision logic vs side effects** — separate business/decision logic from I/O, remote calls, framework glue, and persistence when that separation improves testing, failure handling, reuse, or clarity.
4. **Entry validation** — validate/normalize untrusted or semantically constrained inputs at the boundary where they enter the owned behavior.
5. **Diagnosable failure** — failures crossing a boundary need enough context to identify the operation and failing dependency without leaking secrets.
6. **Evidence before abstraction** — extract shared abstractions after a real repeated need or stable boundary appears; similarity alone is not sufficient.
7. **Minimum refactor** — in an existing codebase, refactor only enough to make the requested change understandable, testable, and safe unless broader refactoring is itself the approved objective.

Every new architectural boundary or abstraction should be explainable by a current requirement, ownership boundary, failure mode, testing need, or demonstrated repetition.

Do not default to:

- an interface for every class;
- a repository object for every table/model;
- a service object for every function;
- DTO/mappers between layers that do not have a real contract boundary;
- a message/event bus for interactions that are simpler as direct calls;
- separate deployment units for modules that do not need independent scaling, release, ownership, or isolation;
- layered/Clean/hexagonal/DDD structure merely because the project is large.

Use layered architecture, Clean Architecture, hexagonal architecture, domain-driven design, or distributed services when concrete requirements justify their boundaries and costs.

### Concern-triggered structure

Add these controls only when the corresponding concern exists:

- **External integration** — define timeout, failure behavior, retry policy/effects, idempotency when retries can repeat state changes, and ownership of the adapter/contract.
- **Multi-step data change** — define transaction/consistency boundary, partial-failure behavior, and recovery/compensation expectations.
- **Multitenancy** — define tenant ownership/partition key, authorization/isolation boundary, and tests that prove cross-tenant access is denied.
- **Hot/performance-sensitive path** — measure a representative baseline before adding caches, queues, indexes, denormalization, concurrency machinery, or other optimization structure.
- **Public/stable contract** — isolate compatibility-sensitive input/output shape from internal representation when doing so prevents contract drift.

The absence of one of these concerns is a reason not to add its ceremony.

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

## Canonical lifecycle and ownership

`Discover → Define → Plan → Design → Build → Verify → Review → Ship`

Vibe owns every stage and its exit decision. Specialists own assigned domain methodology; tools provide evidence. These stages are responsibilities, not eight mandatory documents, meetings, approval questions, or commands. Enter at the appropriate point, reuse settled work, combine lightweight stages, and mark genuinely inapplicable work N/A with a reason. Do not skip required risk controls. Iterate small vertical slices rather than finish every design before proving a runnable result.

| Stage | Head-owned work | Conditional specialist contribution | Output / exit condition |
|---|---|---|---|
| Discover | Inspect objective, applicable rules, repository, affected boundaries, risk, and current capabilities; route selected specialists. | Debugging localizes unclear failure; UI inspects an affected interface; Graphify supports consequential impact questions. | Justified entry point, affected scope and selected capabilities; re-route if evidence changes them. |
| Define | Establish one objective, scope, protected behavior, acceptance criteria, and material user-owned decisions. | UI clarifies relevant user flows; security identifies assets/trust boundaries; API clarifies consumer obligations. | Enough clarity to choose a path without hiding a material unresolved decision. |
| Plan | Choose the simplest adequate stack/architecture, ownership, sequence, dependencies, required evidence and recovery. | Domain estimates and prerequisites supplement one Head plan. | Ready task/vertical slice; a new written plan only when existing risk/scope rules require it. |
| Design | Reconcile cross-domain decisions and preserve platform/business invariants. | UI owns presentation decisions; API owns contract detail; security owns threat scenarios and appropriate controls. | Implementable decisions for the changed boundaries; reuse adequate existing design. |
| Build | Implement and integrate the smallest maintainable slice within scope and writer boundaries. | Specialists guide or edit assigned domain surfaces; debugging handles unclear failures. | Runnable/inspectable requested behavior with relevant failure handling. |
| Verify | Choose the cheapest sufficient checks against acceptance and changed failure modes; record provenance and unavailable checks. | UI rendered/accessibility evidence; API contract/failure evidence; security denial/abuse evidence; debugging reproduction/regression; Trivy relevant scans. | Required criteria/boundaries have evidence or are explicitly failed/unverified/blocked. |
| Review | Assess objective fit, actual diff, scope, maintainability, integration and evidence sufficiency; own merge readiness. | Relevant domain review supplements the Head; do not restart standalone workflows or duplicate test runs. | Required findings resolved; optional findings do not expand scope automatically. |
| Ship | Perform authorized integration/package/release/deploy/handoff actions; verify delivered revision/artifact/environment and recovery where required. | Reuse relevant specialist findings; debug actual delivery failure; scan the delivered artifact when relevant. | Accurate delivery state, health/core-flow evidence where required, limitations and next operating action. |

Verify proves behavior; Review assesses the change and its evidence; Ship proves the actual authorized delivery. Merge, release, deployment and local skill installation are distinct outcomes. A local task can ship as a validated artifact/handoff without production deployment.

Specialist identities, machine-readable triggers, stages and permission profile live in `config/specialists.json`. See `references/specialist-composition.md` for activation/handoff and `references/specialist-authority.md` for the shared authority contract. Stage alone never selects all specialists.

Small/local low-risk work can cover the route in one concise pass. Medium work uses bounded slices. Large/cross-boundary work needs confirmed ownership/contracts and integration evidence; repository size alone does not make each local task heavy. WordPress/WooCommerce uses this same lifecycle plus its local public-API, authorization, lifecycle/data-preservation, compatibility and actual installable-artifact constraints.

A failed check returns to the affected Design/Build decision, with debugging only when useful. Review findings return to the responsible domain. After delivery, incidents, compatibility changes or user feedback become a new bounded objective and re-enter at the appropriate stage. No idle monitoring or scheduled automation is implied.

At each meaningful transition, communicate the actual output, relevant evidence, unresolved limitation/readiness, and next useful action. Reuse this information instead of creating a separate report per stage.

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
