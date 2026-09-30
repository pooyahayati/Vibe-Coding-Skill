# Update Catalog

A short, human-readable summary of what changed in each release.

For full technical details, see [CHANGELOG.md](CHANGELOG.md).

## 0.10.5 — Smarter context locality in large projects
- Mixed and monorepo projects now keep platform rules local to the application or package actually being changed, reducing irrelevant WordPress/WooCommerce context in neighboring services.
- Known affected paths now use bounded local scanning, including directory paths, while cross-application changes are recognized as real planning boundaries.
- Applicable `AGENTS.md` instructions and clearer context-size metrics make selective context safer and easier to audit.

## 0.10.4 — More reliable release automation
- Release creation now handles GitHub Actions' short-lived workflow-status lag without skipping an otherwise complete validated release.
- Live dependency checks now treat unavailable optional GitHub source-health as an explicit review state instead of a false pass or a flaky hard failure.

## 0.10.3 — More reliable decisions, lighter context, real WordPress delivery
- Risk, completion, routing, and tool-version controls were tightened so the Skill's reported policy matches what it actually enforces.
- Large projects now keep project intelligence without forcing heavy planning for small local work, and the core Skill instructions are much shorter.
- Technology selection, testing, and code structure now favor requirement-driven decisions and explicitly avoid architecture/test ceremony.
- WordPress plugin delivery can now build and verify the exact installable ZIP, test real install/upgrade behavior, and release validation now requires the full baseline on the same commit.

## 0.10.2 — Safer automatic tool versions
- `Graphify` and `Trivy` now use the latest stable release only after compatibility checks pass.
- Runtime execution stays on the exact verified version, with a verified fallback when needed.
- Portable installations include the full toolchain resolver and runtime layer.

## 0.10.1 — Real-world routing validation
- Context routing was tested against large real repositories, including `Django` and the `WooCommerce Stripe` gateway.
- Small UI tasks avoid unrelated payment/security context, while sensitive payment work loads the required safeguards.

## 0.10.0 — Smarter context for large projects
- Added the `Context Router` so agents load only task-relevant parts of the Skill.
- Added composable packs for `PHP`, `WordPress`, `WooCommerce`, browser JavaScript, REST, payments, security, performance, and external HTTP.
- Added lightweight execution planning for large projects and higher-risk work.

## 0.9.3 — More reliable portable installs
- Installation validation now catches missing scripts, references, configuration, templates, and evaluation files.

## 0.9.2 — Better release automation
- Release readiness can re-evaluate after benchmark evidence arrives and requires the current scenario set.

## 0.9.1 — Stronger evidence correctness
- Higher-risk completion evidence must match the exact target commit.
- Benchmark provenance and latest-run release checks were tightened.

## 0.9.0 — Risk-aware completion and release gates
- Added stronger evidence requirements for significant and critical work.
- Added deterministic `beta`, `RC`, and stable release-readiness gates.

## 0.8.0 — Real-agent benchmark framework
- Added executable benchmark adapters for `Codex` and `Claude Code`.
- Added provenance, raw-output preservation, schema checks, and completeness validation.

## 0.7.0 — Dependency intelligence
- Dependency review now combines registry, vulnerability, maintenance, provenance, source-health, license, and typo-squatting signals.

## 0.6.1 — Governance and audit hardening
- Strengthened Skill validation, repository purity, lifecycle safety, Action pinning, and Agent Skills compatibility checks.

## 0.6.0 — Recovery and cross-platform support
- Added repository-first resume, local-state recovery, rollback support, and portable smoke tests on `Linux`, `macOS`, and `Windows`.

## 0.5.0 — Project intelligence and traceability
- Added the provider-neutral graph layer with `Graphify` as the default provider.
- Added GitHub traceability plus project-state snapshots, drift detection, and handoff support.

## 0.4.1 — Clean project repositories
- Moved Vibe operational state outside product repositories and added repository-purity checks.

## 0.4.0 — Validation and failure testing
- Added representative project validation, failure-injection testing, and structured completion evidence.

## 0.3.1 — Agent behavior evaluation
- Added machine-checkable behavior contracts for evaluating real coding agents.

## 0.3.0 — Risk classifier and broader dependency support
- Added deterministic Tier 0–3 risk classification and broader ecosystem dependency checks.

## 0.2.0 — Bootstrap and portable packaging
- Added non-destructive project bootstrap, dependency guarding, evaluation catalogs, and the portable Agent Skill package.

## 0.1.0 — Initial release
- Introduced the risk-adaptive Vibe Coding operating model and the initial project-intelligence, security, state, and validation foundations.
