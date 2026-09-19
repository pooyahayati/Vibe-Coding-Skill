# Changelog

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
