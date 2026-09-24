# External HTTP Capability Pack

## Activation
The task touches a remote API, webhook, SaaS integration, or HTTP client.

## Constraints
- Use the platform's HTTP facilities when they improve portability/interoperability.
- Set explicit timeout/error handling appropriate to the user flow.
- Define retry/idempotency semantics before retrying writes.
- Cache reusable remote reads when freshness requirements allow it.
- Do not make synchronous remote calls on hot page/request paths when background or cached behavior can satisfy the requirement.
- Respect provider rate limits and failure modes.

## Risks
Latency, rate limits, partial failure, duplicate writes, leaked credentials, stale cache, and remote outages cascading into local availability.

## Integration points
Application ↔ remote service; callback/webhook ↔ local state.

## Required checks
Timeout/failure path, authentication/secret handling, request budget, retry/idempotency for writes, and cached/background behavior where applicable.

## Avoid
Unbounded retries, default-long timeouts, remote calls per render/loop item, and logging secrets or sensitive payloads.
