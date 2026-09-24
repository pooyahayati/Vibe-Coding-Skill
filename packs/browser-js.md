# Browser JavaScript Capability Pack

## Activation
Browser JavaScript/TypeScript, React/Gutenberg, or package metadata is present.

## Constraints
Preserve the project's bundler/runtime conventions, public API contracts, accessibility, localization, and loading boundaries.

## Risks
Bundle growth, duplicated framework copies, stale client/server contracts, hydration/state bugs, inaccessible UI, and scripts loaded outside their needed screen.

## Integration points
Browser UI ↔ server/API contract.

## Required checks
Build/lint/typecheck when configured, focused UI behavior, and API-contract regression for changed calls.

## Avoid
Global browser state without ownership, unconditional site-wide bundles, and adding a framework/library for a local interaction already supported by the stack.
