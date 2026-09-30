# Toolchain Version Resolution Policy

## Purpose

External tools are managed by capability and compatibility policy, not by a permanently pinned public operating version.

Current managed tools include:

- Graphify
- Trivy

## Resolution algorithm

Use:

`Latest Stable Published → Compatibility Contract → Exact Runtime Resolution`

1. Resolve the latest published release from the tool's authoritative stable distribution channel.
2. Run the tool-specific compatibility contract against that exact release.
3. If the contract passes, select that exact version for the current execution.
4. If the contract fails or the compatibility subprocess times out, convert that attempt into structured failure evidence, then resolve the recorded `last_known_good` version and verify that fallback against the same contract.
5. Attempt the fallback once. If both attempts fail, stop and surface the tool as unavailable/incompatible rather than silently using an untested release.

Compatibility subprocesses run with the current Python interpreter rather than assuming a platform-specific `python` command name.

The exact selected version is a runtime/session pin. This preserves reproducibility without forcing the repository's public documentation to age behind current stable releases.

## Configuration

`config/toolchain.json` defines:

- `channel`: stable distribution channel;
- `resolution`: `latest-compatible-stable`;
- `last_known_good`: exact fallback state;
- `policy`: human-readable policy intent;
- tool-specific optionality such as Trivy's `required`.

The configuration must not use a normal `approved` or `latest_seen` version as the operating source of truth.

## Authoritative sources

Use the tool's official published distribution channel:

- Graphify: PyPI package `graphifyy`;
- Trivy: official GitHub release stream and container image.

A Git tag alone is not sufficient when the runtime distribution is a package registry or published container.

## Compatibility failure

A failed latest candidate is evidence of incompatibility, not permission to force the upgrade.

The resolver must:

- retain the latest candidate failure evidence;
- verify the last-known-good fallback;
- report that fallback was used;
- keep the user/project workflow moving when the tool is optional and a documented fallback exists.

## Documentation rule

Do not place a normal operating version in user-facing instructions, Skill references, or examples.

Exact versions may appear in:

- machine-managed fallback state;
- runtime/session evidence;
- historical changelog entries;
- release or incident records.

## Runtime rule

Once selected, use the exact resolved version for the current execution. Do not silently switch versions halfway through an execution because a newer release appeared.

A later execution may resolve a newer stable release through the same compatibility gate.
