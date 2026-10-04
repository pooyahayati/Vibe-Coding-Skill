# Toolchain Version Resolution Policy

## Purpose

External tools are managed by capability and compatibility policy, not by a permanently pinned public operating version.

Current managed tools include Graphify and Trivy.

## Resolution algorithm

Use:

`Latest Stable Published → Compatibility Contract → Exact Runtime Resolution`

1. Resolve the latest published release from the authoritative stable distribution channel.
2. Run the tool-specific compatibility contract against that exact release.
3. If the contract passes, select that exact version for the current execution.
4. If the candidate fails or times out, verify the recorded `last_known_good` version once.
5. If both fail, surface the tool as unavailable/incompatible rather than silently using an untested release.

Compatibility subprocesses run with the active Python interpreter.

## Execution session

A **toolchain session** is an explicit execution-scoped object owned by one compound operation. It is not a process-global cache.

Create one session at the start of a compound operation and pass/reuse it for every managed-tool resolution inside that operation. The first resolution records the exact selected version; later resolutions for the same tool in that session reuse it without another compatibility check.

A new session may resolve a newer compatible stable release.

Environment variables such as `VIBE_TOOLCHAIN_GRAPHIFY_SESSION_VERSION` are explicit external pins. They are reused by the session but are not silently created or mutated by the runtime.

One-shot calls without a supplied session remain one-shot by design. Do not describe those as automatically session-pinned.

## Runtime activation

After resolution, runtime execution must use the exact selected version.

For Graphify:

- use a matching native `graphify` executable when its reported version equals the selected version;
- otherwise use the isolated `uvx --from graphifyy==<version>` runtime;
- if neither is available, report the capability unavailable.

For Trivy:

- use a matching native `trivy` executable when its version equals the selected version;
- otherwise use the official `aquasec/trivy:<version>` container;
- if neither is available, report the capability unavailable.

These fallback rules are for compatibility/general tool execution. Publication has a stricter native-only requirement: `trivy_compat.py --check-local` is the planning preflight and `--release-target ... --output ...` performs the actual local release scan. A container compatibility pass does not satisfy that requirement. See [the security release gate](security-and-dependencies.md#native-release-gate).

A native installation therefore can satisfy the compatibility/runtime contract without `uvx` or Docker when it is the exact selected version.

## Filesystem targets

Host filesystem scans are target-aware operations.

A native Trivy scan receives the absolute host path directly. A containerized Trivy filesystem scan MUST bind-mount that host target read-only and scan the mapped container path (currently `/workspace`).

Do not pass a host filesystem path directly to an unmounted container. Generic Trivy command construction rejects `fs` so callers must use the filesystem-specific builder.

Use argument arrays rather than shell-quoted command strings; this preserves paths containing spaces. Docker bind-mount construction preserves native absolute Windows paths when running on Windows.

## Configuration

`config/toolchain.json` defines:

- `channel`: stable distribution channel;
- `resolution`: `latest-compatible-stable`;
- `last_known_good`: exact fallback state;
- `policy`: human-readable policy intent;
- tool-specific optionality.

Do not use normal `approved` or `latest_seen` values as the operating source of truth.

## Authoritative sources

- Graphify: PyPI package `graphifyy`
- Trivy: official GitHub release stream and official container image

A Git tag alone is insufficient when runtime distribution occurs through a registry/container channel.

## Evidence

Resolution evidence should record, when relevant:

- tool;
- selected version;
- resolution source;
- fallback use;
- compatibility verification status;
- runtime version;
- runtime version verification.

Graph state records the exact Graphify provider version used to build the graph, so later query/explain/path operations reuse that version instead of re-resolving.

## Documentation rule

Do not place a normal operating version in user-facing instructions, Skill references, or examples.

Exact versions may appear in machine-managed fallback state, execution evidence, graph/provider state, historical changelog entries, and release/incident records.
