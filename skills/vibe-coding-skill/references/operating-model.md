# Operating Model

## Primary objective

Build the smallest reliable product or change that achieves the required user outcome with minimum total complexity.

Every meaningful milestone should be Runnable, Testable, Demonstrable, and Diagnosable.

## Current Objective

Maintain exactly one Current Objective. Every active task must support it directly or be identified as necessary enabling work.

## Discovery stop condition

Discovery is complete when problem, primary user, core outcome, core workflow, MVP boundary, critical constraints, and observable success criteria are clear enough to make an implementation decision.

Do not continue discovery merely to produce more documentation.

## Requirements discipline

Classify requirements as Must, Should, Could, Later, or Rejected. Do not silently remove requested behavior.

After MVP approval, new non-essential features go to backlog unless the core outcome cannot work without them.

## Architecture

Prefer the simplest architecture compatible with known requirements.

For multi-domain products, consider a modular monolith before distributed architecture.

Do not add by default microservices, CQRS, event sourcing, Kafka/RabbitMQ, Elasticsearch, Kubernetes, GraphQL, or Redis.

Before adding complexity, answer: Which current requirement requires this?

## Technical spikes

`Question → Minimal Experiment → Evidence → Decision`

A spike is bounded and disposable.

## Task sizing

Small: execute directly.

Medium: decompose when it improves ownership or verification.

Large: decompose before implementation.

## Ready check

A task is Ready when objective, scope, dependencies, acceptance criteria, blockers, required tests, and expected output are clear enough to execute.

Otherwise clarify, split, spike, or mark Blocked.

## Change impact

For significant work:

`Requirement → Product → Architecture → Module/Graph → Data/API → Tests → Deployment/Release`

Record only decisions that matter later.

## Stop conditions

Stop discovery when enough information exists.

Stop implementation when acceptance criteria are met.

Stop testing when risk-appropriate evidence is sufficient.

Stop refactoring when the requested change is safe and maintainable.

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
