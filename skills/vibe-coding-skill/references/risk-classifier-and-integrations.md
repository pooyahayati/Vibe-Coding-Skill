# Risk Classifier and Tool Integrations

## Risk classifier

The bundled classifier provides a conservative, deterministic workflow floor.

Use:

```bash
python scripts/risk_classifier.py "Change authentication from sessions to JWTs" --json
```

It must not replace engineering judgment. Context may raise a tier; automated classification should not silently lower an explicitly recognized risk.

## Dependency adapters

The executable dependency guard supports:

- PyPI
- npm
- crates.io
- Maven Central (`group:artifact`)
- NuGet
- Go modules

Registry checks verify package/version existence. OSV checks use ecosystem-native identifiers.

Metadata availability differs by ecosystem. Missing license/provenance evidence returns `REVIEW REQUIRED`.

## Integration guard

Use:

```bash
python scripts/integration_guard.py --root . --tier 2 --json
```

The integration guard is read-only. It checks:

- Git repository state;
- GitHub remote and optional `gh` authentication;
- Graphify availability/version against the approved toolchain version;
- graph-state freshness from the local Vibe Coding workspace;
- Trivy availability.

It does not automatically run destructive commands, push, create PRs, refresh a graph, or scan/send project content.

Operational state is read from the local workspace outside the repository. Integration checks must not create `.vibe/` or tool report files in the project tree.

For Tier 2, missing Graphify/Trivy is a warning when a safe fallback exists.

For Tier 3, missing required security verification or a stale graph used as evidence is a blocker unless an explicit equivalent has been established.

## GitHub

GitHub is an adapter, not the core state model. The skill should still function in local-only or non-GitHub repositories.

When GitHub is detected and `gh` is authenticated, it may be used for issue/PR/release traceability according to the user's permissions.

## Graphify

Use the approved Graphify version where reproducibility matters. If another version is installed, surface the difference rather than silently changing the user's environment.

Do not refresh a graph simply to satisfy a check for Tier 0/1 work.

## Trivy

Trivy remains the broad baseline scanner. The integration guard checks availability; actual scanning is run only when justified by the risk and scope.

A passing Trivy scan does not replace application-level security review or SAST where needed.

## Local-only tooling

Graphify output, Trivy reports, benchmark output, coverage reports, and Vibe Coding state are local-only. Initialize the local workspace with `python scripts/local_workspace.py init --root . --json` and verify purity before commit/push.
