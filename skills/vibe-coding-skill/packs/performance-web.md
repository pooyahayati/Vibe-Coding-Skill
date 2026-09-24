# Web Performance Capability Pack

## Activation
Performance/query/request/cache/cron work is requested or another active pack introduces a hot-path latency/resource concern.

## Constraints
Measure regression against the project baseline rather than applying universal magic numbers. Track new database queries, remote requests, cache behavior, asset loading, repeated loop work, autoloaded state, and background jobs that the change introduces.

## Risks
N+1 queries, synchronous remote latency, repeated uncached work, global asset loading, cache stampedes, oversized autoloaded options/state, and duplicate scheduled jobs.

## Integration points
Request path ↔ database/cache; application ↔ external latency.

## Required checks
Before/after evidence when performance is material, request/query delta for hot paths, cache/failure behavior, and activation/deactivation comparison where practical.

## Avoid
Hard-coded global query budgets detached from baseline, premature caching without invalidation semantics, and moving work to cron/background without observability or duplicate protection.
