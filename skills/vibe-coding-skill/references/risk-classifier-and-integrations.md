# Risk Classifier and Tool Integrations

## Risk classifier

The bundled classifier provides a deterministic workflow floor. It does not replace engineering judgment.

For ordinary tasks:

```bash
python scripts/risk_classifier.py "Change authentication from sessions to JWTs" --json
```

For ambiguous, multilingual, or sensitive work, provide structured facts when known:

```bash
python scripts/risk_classifier.py "Delete customer records" \
  --operation delete-all \
  --environment production \
  --data-sensitivity personal \
  --change-boundary system \
  --json
```

Supported structured dimensions are operation, environment, data sensitivity, and change boundary. The agent should derive these facts from the request and relevant project evidence rather than asking the user for implementation details that can be inferred.

Canonical values (defined in `scripts/risk_classifier.py`):

| Dimension | Values |
| --- | --- |
| `operation` | `tiny`, `feature`, `read-only`, `refactor`, `destructive`, `auth`, `migration`, `external-integration`, `dependency`, `security`, `payment` |
| `environment` | `local`, `development`, `test`, `staging`, `production`, `control-plane` |
| `data_sensitivity` | `none`, `public`, `internal`, `personal`, `sensitive`, `financial`, `payment`, `health`, `credentials`, `private-key`, `secret` |
| `change_boundary` | `local`, `module`, `cross-module`, `system`, `application-wide` |

Bounded aliases such as `delete-all`, `live`, and `pii` normalize to canonical values. Unsupported nonempty values remain unresolved; they do not count as evidence that a dimension is safe. Preserve the same facts in routing and planning: `execution_plan.py draft` accepts `--risk-operation`, `--risk-environment`, `--risk-data-sensitivity`, and `--risk-change-boundary`.

Structured facts are authoritative inputs to the workflow floor. Text/keyword detection is supplemental and supports English plus selected Persian risk phrases. Unknown or unresolved facts must be surfaced as uncertainty; absence of a keyword is not evidence that a sensitive operation is low risk.

Context routing may raise the tier. Whenever it does, the final tier, approval requirement, reasons, and required controls are rebuilt from the same risk-policy source of truth.

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

PyPI and crates.io license evidence belongs to the selected release. Latest-release dates are separate maintenance signals. crates.io repository metadata is project-wide and is labeled accordingly; do not interpret it as proof of the selected artifact's source commit.

## Integration guard

Use:

```bash
python scripts/integration_guard.py --root . --tier 2 --json
```

The integration guard is read-only. It checks:

- Git repository state;
- GitHub remote and optional `gh` authentication;
- Graphify availability and the configured resolution policy;
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

Use the latest published stable Graphify release only after its compatibility contract passes. A compound graph operation owns an explicit toolchain session and resolves Graphify once. The exact selected version is recorded with graph state so later graph queries reuse it.

A matching native Graphify executable can satisfy the contract directly; otherwise the isolated `uvx` runtime is used. Do not refresh a graph simply to satisfy a check for Tier 0/1 work.

## Trivy

Trivy remains the broad baseline scanner. The integration guard checks availability; actual scanning is run only when justified by risk and scope.

A matching native Trivy executable can satisfy the exact-version contract; otherwise the official versioned container is used. Containerized filesystem scans bind-mount the requested host target read-only and scan its mapped container path.

A passing Trivy scan does not replace application-level security review or SAST where needed.

## Local-only tooling

Graphify output, Trivy reports, benchmark output, coverage reports, and Vibe Coding state are local-only. Initialize the local workspace with `python scripts/local_workspace.py init --root . --json` and verify purity before commit/push.
