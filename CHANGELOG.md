# Changelog

## 0.9.3 — Installation completeness hardening

- Expanded the offline installation check to require the complete portable runtime script set, including `release_readiness.py`.
- Required every reference document directly used by the Skill to be present before installation can pass.
- Added checks for runtime configuration, eval catalog/schema, Agent metadata, and project templates.
- Added JSON parse validation for runtime config/eval files.
- Added regression coverage so incomplete portable installations cannot silently pass installation validation.

## 0.9.2 — Stable benchmark orchestration hotfix

- Re-triggered validated release evaluation when the manual Real Agent Benchmark completes successfully, so stable readiness can advance after benchmark evidence arrives without requiring a redundant base-CI rerun.
- Bound stable readiness to the exact current eval scenario ID list rather than accepting an arbitrary positive scenario count.
- Required each stable Agent row to report expected, completed, and passed scenario counts equal to the current catalog size.
- Added regression coverage for benchmark-triggered release orchestration, scenario-set mismatch, and per-Agent scenario-count mismatch.

## 0.9.1 — Evidence correctness and release provenance hotfix

- Rejected malformed acceptance-criteria entries instead of silently ignoring non-object or non-boolean completion claims.
- Required Tier 2/3 completion reports to declare a target commit and excluded passing evidence bound to a different revision.
- Tightened Tier 3 evidence timestamps to require timezone-aware ISO-8601 values.
- Hardened benchmark aggregation so complete evidence requires valid runner envelopes, matching Agent/scenario provenance, and exactly one consistent Skill/version/hash identity set.
- Prevented unexpected per-scenario runner exceptions from aborting the remaining benchmark scenarios; internal failures are now recorded as failing raw evidence and execution continues.
- Changed release readiness to use the latest check result for each required workflow, so an older success cannot mask a newer failure on the same commit.
- Changed stable benchmark resolution to consider the latest Real Agent Benchmark run instead of falling back to an older successful run when a newer run failed.
- Added regression coverage for malformed completion claims, revision mismatch, ambiguous timestamps, benchmark envelope identity, runner exception isolation, and latest-run release semantics.

## 0.9.0 — Adaptive evidence and release readiness

- Hardened the real-agent benchmark workflow so Codex and Claude Code failure paths are isolated, aggregation still runs, raw evidence is preserved, and aggregate failures cannot be masked by `tee`.
- Added bounded benchmark tier policies that distinguish preferred behavior, legitimate conservative escalation, under-classification, and over-engineering.
- Added per-scenario tier ceilings with explicit rationale where conservative escalation is permitted.
- Added risk-aware completion evidence provenance: higher-risk Done claims require stronger, revision-bound, and timestamped evidence.
- Added deterministic beta, RC, and stable release-readiness gates.
- Required stable releases to have complete, fully conformant real Codex and Claude Code benchmark evidence.
- Bound stable benchmark evidence to the current Skill version, portable Skill tree, eval catalog, and output-schema hashes.
- Wired the validated release workflow to the release-readiness gate while keeping repository branch protection outside the release criteria by project decision.
- Extended regression, failure-injection, portable-package, Agent Skills compatibility, and cross-platform coverage for the new policies.
- Kept missing real-agent runs as missing evidence rather than treating them as success; the remaining real-agent evidence requirement stays tracked separately for 1.0 readiness.

## 0.8.0 — Real-agent benchmark execution and evidence hardening

- Added strict machine JSON Schema for live-agent behavior contracts.
- Added real Codex CLI and Claude Code benchmark adapters with blind prompt generation.
- Added provenance envelopes containing agent version, model override, Skill version, timing, hashes, and workspace-integrity evidence.
- Added raw stdout/stderr preservation outside the repository.
- Added strict benchmark completeness checks so missing scenarios or agents cannot produce a conformance rate.
- Added credential-safe preflight that records only credential variable names, never values.
- Added isolated temporary project-scoped Skill installation for benchmark runs.
- Added manual credential-gated GitHub Actions workflow for full Codex + Claude Code evaluation.
- Fixed non-JSON scorer output and added schema/integrity validation.
- Added regression coverage for prompt blindness, provenance integrity, missing evidence, and secret redaction.
- Kept actual Agent performance claims blocked until genuine raw runs exist.

## 0.7.0 — Dependency intelligence hardening

- Upgraded Dependency Guard from baseline registry/OSV checks to risk-adaptive multi-signal evidence.
- Added explicit dependency necessity and purpose as separate judgment fields.
- Added deps.dev package/version, license, advisory, deprecation, related-project, and verified-attestation evidence.
- Added GitHub source-repository health checks with authenticated mode when a token is available.
- Added maintenance/release-age and deprecated-package review signals.
- Added package-name similarity / typo-squatting signals using explicit trusted names and discovered project dependencies.
- Added project license allow/deny policy evidence without pretending to provide legal advice.
- Added Tier 2/3 evidence requirements and Tier 3 provenance-attestation review.
- Added deterministic unit/failure-injection coverage and live provider contract coverage.

## 0.6.1 — Audit hotfix and governance hardening

- Fixed literal escaped-newline corruption in `SKILL.md` and added semantic validation to prevent recurrence.
- Clarified the project-intelligence graph policy while keeping machine-generated graph data local-only.
- Removed the recommended Claude project-local checkout and hardened repository purity against local Vibe Skill checkouts.
- Pinned core GitHub Actions by commit SHA and made Graphify/Trivy contract tests read approved versions dynamically.
- Added automatic latest-stable Trivy compatibility proposals.
- Added official Agent Skills reference-validator compatibility workflow pinned to a known upstream commit.
- Hardened last-known-good recording with offline installation validation and isolated target validation before upgrades.
- Added validated-release automation and safe cleanup of unchanged merged work branches.
- Extended GitHub traceability snapshots and dry-run mutations to Milestones and GitHub Projects.
- Improved private security-reporting guidance.
- Removed stale hard-coded internal version identity from dependency/tool requests.

## 0.6.0 — Recovery, resume, cross-platform, and installation hardening

- Added repository-first resume context generation that does not depend on chat history.
- Added safe local-state inspection, quarantine, and recovery.
- Added offline installation validation for canonical and portable skill installs.
- Added last-known-good recording, local upgrade planning, and explicit rollback support.
- Added Linux, macOS, and Windows portability smoke tests across supported Python versions.
- Added portable-install validation in CI.
- Documented Python 3.10+ baseline, offline behavior, recovery semantics, and rollback limits.

## 0.5.0 — Graph provider contract, GitHub traceability, and project state automation

- Added a provider-neutral graph contract with Graphify as the default adapter.
- Added local shadow-source graph refresh so Graphify output never needs to live in the user project working tree.
- Added working-tree fingerprint freshness, including uncommitted and untracked non-ignored source changes.
- Added local graph query/path/explain routing with stale-graph blocking by default.
- Expanded Graphify compatibility contracts to cover explicit graph queries and incremental update.
- Added GitHub traceability snapshots, requirement mapping, verification, and dry-run-by-default Issue creation.
- Added local project-state capture, drift detection, and handoff snapshots without repository churn.
- Refactored doctor and integration guard to consume shared graph/GitHub adapters.
- Added end-to-end tests for graph shadowing, GitHub traceability, and local state automation.

## 0.4.1 — Local-only tooling and clean project repositories

- Moved Vibe Coding operational state from project-local `.vibe/` to `~/.vibe-coding/projects/<project-id>/`.
- Added a Local Workspace Manager for graph, security, test artifacts, benchmarks, caches, worktrees, and state.
- Added clone-local exclusions through `.git/info/exclude` without modifying project `.gitignore`.
- Added Repository Purity Gate to block tracked/staged Graphify, Trivy, benchmark, coverage, and Vibe state artifacts.
- Updated bootstrap, doctor, integration guard, stale-graph tests, and failure injection to use external local state.
- Clarified that real product tests remain in Git while generated test/coverage reports remain local.
- Added worktree-safe Git exclude path resolution.

## 0.4.0 — Real-project validation, failure injection, and agent benchmark

- Added representative project validation fixtures and deterministic runner.
- Added failure-injection coverage for prompt injection, hallucinated dependencies, vulnerable packages, stale graphs, and unsupported Done claims.
- Added a structured completion evidence gate.
- Added vendor-neutral aggregation for real Codex/Claude Code behavior contracts.
- Added validation and benchmarking guidance without fabricated agent results.
- Added CI coverage for project validation and failure injection.
- Cleaned duplicate changelog heading.

## 0.3.1 — Live agent behavior evaluation

- Added a vendor-neutral JSON behavior contract for real Codex/Claude Code evaluation.
- Added deterministic scoring of agent tier, approval requirements, required controls, and forbidden actions.
- Added machine-checkable control contracts to every eval scenario.
- Added regression tests for passing and failing live-agent outputs.


## 0.3.0 — Risk classifier, full dependency adapters, and hardened tool contracts

- Added deterministic, explainable risk classification with Tier 0–3 workflow floors.
- Added Maven Central, NuGet, and Go module support to Dependency Guard.
- Added read-only GitHub/Graphify/Trivy integration health gate.
- Added executable scenario evals against the risk classifier.
- Added network-backed registry/OSV smoke tests.
- Added Trivy contract testing and approved-version toolchain tracking.
- Added unit tests for risk classification and stale-graph integration behavior.

## 0.2.0 — Bootstrap, dependency guard, evals, and portable packaging

- Added non-destructive adaptive project bootstrap.
- Added executable dependency guard with PyPI/npm/crates.io registry checks and OSV verification.
- Added deterministic behavior-contract eval catalog.
- Added unit tests for dependency decisions and bootstrap safety.
- Added portable Agent Plugin packaging for Codex-compatible discovery.
- Added package drift validation to CI.

## 0.1.0 — Initial core

- Added the risk-adaptive Vibe Coding Skill operating model.
- Added Tier 0–3 workflow classification.
- Added Graphify project-intelligence policy and automated compatibility proposal workflow.
- Added Trivy/OSV/package-registry security and dependency guidance.
- Added persistent project-state and traceability rules.
- Added doctor, change-budget, Graphify compatibility, and skill-validation utilities.
- Added GitHub Actions validation.
