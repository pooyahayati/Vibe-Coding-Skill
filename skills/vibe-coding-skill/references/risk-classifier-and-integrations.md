# Risk Classifier and Tool Integrations

## Risk classifier

The bundled classifier reports discovery signals and a conservative workflow floor until the Head resolves actual scope. It checks supplied input consistency; it does not verify source semantics or replace engineering judgment.

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

Structured material-risk facts establish a protected floor. Text/path detection supports English plus selected Persian phrases; it is conservative discovery evidence, not a semantic parser. Unknown or conflicting facts remain explicit uncertainty. Neither absent keywords nor an unsupported `tiny` claim establishes safety.

Context routing may raise the tier. Whenever it does, the final tier, approval requirement, reasons, and required controls are rebuilt from the same risk-policy source of truth.

### Resolving incidental signals

For a local prose/comment-only correction, inspect the requested edit and relevant source/diff, then supply two optional fields with all four known risk dimensions and affected paths: `change_effect=non-runtime` and a concrete `scope_evidence` summary. Record what was inspected and why executable behavior, operational instructions, data, contracts and protected outcomes are unchanged. This is an inline Head assessment, not a new mandatory file, test or approval. `behavioral` is the other supported effect value; it never suppresses signals.

```bash
python scripts/risk_classifier.py "Fix a production guide typo" --path README.md \
  --operation tiny --environment local --data-sensitivity none --change-boundary local \
  --change-effect non-runtime \
  --scope-evidence "Inspected README diff: spelling only; commands, deployment steps and behavior unchanged." --json
```

The classifier accepts this assessment only for `tiny`/`read-only` operations with complete valid facts, a nonempty inspection summary, known paths and no material-risk fact signal. Unsupported/missing/conflicting facts preserve discovery signals and emit uncertainty. An accepted review moves incidental matches to `resolved_signals`; known auth, destructive, financial, production or cross-module facts cannot be suppressed. Do not classify edited executable instructions, security requirements, data contracts, runtime Markdown or meaningful runbook steps as non-runtime. Reassess after scope/effect changes; a copied summary is not fresh evidence.

Router and planner use the same fields with the `--risk-` prefix, including `--risk-change-effect` and `--risk-scope-evidence`. An accepted review prevents incidental task/path/source mentions and project-wide platform relationships from manufacturing behavioral integration work. Platform context and governing instructions remain available. Incomplete affected-path inspection keeps the assessment unresolved; explicit context facts/pack requirements can still raise the floor. Specialist participation is governed separately.

Output `scope_assessment.semantics_verified` remains false: the tool validates consistency, while the Head must verify the review against the actual edit. Existing callers without an assessment keep conservative behavior. In an existing structured contract, retain the same input map as optional `risk_facts`; the planner reuses it and rejects conflicting overrides. A retained tier still wins until the [explicit state reconciliation](project-state-automation.md#correcting-an-incidental-risk-floor) succeeds.

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

PyPI, npm and crates.io license evidence belongs to the selected release. Latest-release dates are separate maintenance signals. crates.io repository metadata is project-wide and is labeled accordingly; do not interpret it as proof of the selected artifact's source commit.

## Integration guard

Use:

```bash
python scripts/integration_guard.py --root . --tier 2 --operation development --graph-use source --json
```

Health and development modes are read-only. They check:

- Git repository state;
- GitHub remote and optional `gh` authentication;
- Graphify availability and the configured resolution policy;
- graph-state freshness from the local Vibe Coding workspace;
- native Trivy executability/version preflight, without treating presence as a scan.

Omitting `--operation` preserves the legacy health-only route. Neither health nor development runs a scanner, refreshes graphs, installs tools, pushes or creates PRs. `PASS` means integration health only: `task_evidence_checked` remains false, `release_scan_verified` remains false and `publication_security_gate` is `NOT_CHECKED`. Required task security checks still belong to the retained contract and completion gate; a health result cannot replace them or authorize a sensitive action.

Operational state is read from the local workspace outside the repository. Missing Trivy is at most a development/health warning, including Tier 3; safe work can continue while task-required native security evidence and authorization remain mandatory.

Use `--graph-use authoritative` when relying on graph evidence: a missing or non-fresh graph blocks that reliance at every tier. Use `--graph-use source` for direct repository analysis, retaining actual impact evidence in the task contract. The default `auto` reports health only and does not certify either analysis route. A stale graph does not block a declared source-analysis fallback. Graph freshness uses the shared provider's current source/output checks.

For authorized publication only, the optional publication route delegates to the existing [native release gate](security-and-dependencies.md#native-release-gate):

```bash
python scripts/integration_guard.py --root . --tier 2 --operation publication \
  --graph-use source --release-target <prepared-release-dir> \
  --release-report <private-workspace>/security/trivy.json --scanners vuln,secret --json
```

This explicitly runs a local native scan and may update scanner data; it writes reports/cache only outside project source. Relative filesystem targets resolve against `--root`; report paths resolve against the calling directory. For images use `--target-type image` and an immutable digest. Use this route **or** `trivy_compat.py --release-target`, not both for the same evidence. No cached report input, presence-only result, Docker fallback or development equivalent can satisfy publication. Missing final target/report, an unqualified scan or a native gate warning requiring Head assessment blocks this route. It preserves the helper's target binding, scanner checks and finding policy; the Head still confirms scope, required receipts, other release gates and authorization.

Existing exit codes remain: `2` for blockers, `1` only when `--strict` promotes warnings, otherwise `0`. Strict warnings are diagnostics, not proof of missing task evidence. Unknown operation/graph-use values and release inputs without an explicit publication operation are rejected. Legacy Tier 3 health callers now receive warnings instead of an unconditional scanner/stale-graph failure; callers needing authority must declare graph reliance or publication explicitly.

## GitHub

GitHub is an adapter, not the core state model. The skill should still function in local-only or non-GitHub repositories.

When GitHub is detected and `gh` is authenticated, it may be used for issue/PR/release traceability according to the user's permissions.

## Graphify

Use the latest published stable Graphify release only after its compatibility contract passes. A compound graph operation owns an explicit toolchain session and resolves Graphify once. The exact selected version is recorded with graph state so later graph queries reuse it.

A matching native Graphify executable can satisfy the contract directly; otherwise the isolated `uvx` runtime is used. Do not refresh a graph simply to satisfy a check for Tier 0/1 work.

## Trivy

Development uses native project security controls and risk-relevant audits. Trivy is the only additional scanner in the Head workflow. Publication requires the [native release gate](security-and-dependencies.md#native-release-gate), including a working verified stable executable and scans of the final target.

The generic tool compatibility adapter can exercise an official versioned container, with read-only filesystem mounts. That compatibility result is not publication evidence and cannot replace the mandatory native scanner. The integration guard's publication route delegates directly to the native helper without container fallback.

A passing Trivy scan does not replace application-level security review or SAST where needed.

## Local-only tooling

Graphify output, Trivy reports, benchmark output, coverage reports, and Vibe Coding state are local-only. Initialize the local workspace with `python scripts/local_workspace.py init --root . --json` and verify purity before commit/push.
