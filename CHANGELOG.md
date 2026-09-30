# Changelog

## 0.10.6 — Language-independent routing and semantic completion evidence

- Added config-driven structured context facts for runtime, platform, capability, and concern routing so known semantics no longer depend on natural-language keywords.
- Added explicit Context Router CLI inputs for structured runtime/platform/capability/concern facts and rejects unsupported fact values instead of silently ignoring them.
- Propagated structured context facts into execution planning so routing and planning operate from the same semantic inputs.
- Added regression coverage proving equivalent English/Persian greenfield WordPress/WooCommerce payment tasks select the same capability packs and workflow floor when supplied the same structured facts.
- Replaced free-form completion evidence diversity with a controlled semantic evidence taxonomy and evidence families.
- Made Tier 2/3 evidence diversity count semantic families rather than raw labels, preventing multiple verification-test labels from manufacturing independent evidence.
- Added regressions that reject unknown evidence kinds and block higher-risk completion when all passing evidence belongs to only one semantic family.
- Kept canonical and portable routing, completion, configuration, references, and Skill contracts synchronized.

## 0.10.5 — Path-aware context routing for large and mixed repositories

- Made capability routing project-area aware so platform evidence stays local to the affected application/package in common monorepo layouts such as `apps/`, `packages/`, `services/`, `plugins/`, `themes/`, and scoped WordPress plugin/theme directories.
- Switched known-path routing to bounded path-scoped source scanning, added directory-level affected-path support, and kept the wider project scan only as the fallback when impact paths are still unknown.
- Refined change-scope detection so sibling applications under the same top-level container can correctly become `cross-boundary` and trigger execution planning without making repository size itself a planning requirement.
- Made repository-root and subtree-applicable `AGENTS.md` files explicit persistent instructions while excluding unrelated sibling agent instructions and preserving the standard `README.md` fallback context.
- Expanded context observability with scan strategy/areas plus separate Skill core, selected reference, selected pack, persistent-context upper-bound, and combined context upper-bound byte metrics.
- Added regressions for same-container mixed monorepos, directory-only paths, local platform evidence after more than 700 unrelated files, scoped `AGENTS.md`, and sibling-application execution planning.

## 0.10.4 — Release orchestration reliability

- Fixed release orchestration for GitHub Actions eventual consistency by trusting the successful triggering `workflow_run` event when the runs API still reports that same run with a temporary null conclusion; release-gate workflow changes now retrigger the full path-filtered baseline.
- Hardened live dependency contracts so rate-limited/unavailable optional GitHub source-health evidence passes only when the dependency decision explicitly degrades to `REVIEW REQUIRED` with a `repository.health_unavailable` signal; false `ACCEPT` remains a contract failure.

## 0.10.3 — Independent review remediation and delivery hardening

- Added structured risk facts for operation, environment, data sensitivity, and change boundary, with supplemental English/Persian text signals and safer destructive-operation matching.
- Centralized tier policy generation so router escalation rebuilds the final tier, approval requirement, reasons, and required controls from one source of truth.
- Upgraded completion reports to schema v2 with explicit criterion IDs/descriptions/required status/evidence links and required evidence that blocks completion when it fails.
- Converted the toolchain resolver tests to discoverable `unittest` cases and added regressions for package imports, timeout fallback, and portable Graphify version lookup.
- Made Graphify compatibility version detection work from the portable Skill without a root `VERSION` file.
- Made toolchain compatibility timeouts structured failures so the resolver can attempt the verified last-known-good fallback, and switched child execution to the active Python interpreter.
- Gated WordPress REST routing on actual WordPress platform evidence so generic REST/API terminology does not inject WordPress/PHP context into unrelated backends.
- Added explicit task change-scope reporting and changed execution-plan requirements to depend on Tier 2/3 risk or demonstrated cross-boundary scope rather than repository size alone.
- Kept large-repository project intelligence active while allowing local low-risk work to stay on the light route.
- Reduced the canonical/portable `SKILL.md` entry point from roughly 480 lines to a 215-line routed core and added a 260-line validation guard against maintainer-detail creep.
- Added explicit execution-scoped toolchain sessions so compound operations resolve each managed tool once and reuse the exact selected version without a process-global cache.
- Made Trivy filesystem execution target-aware: container fallback now bind-mounts the host target read-only and generic Trivy command construction rejects ambiguous unmounted `fs` scans.
- Allowed Graphify and Trivy compatibility contracts to use an exact-version native executable when available instead of requiring `uvx` or Docker unconditionally.
- Added regressions for same-session version reuse, new-session re-resolution, Windows/space-containing bind mounts, native compatibility runtimes, and explicit filesystem command routing.
- Added a bounded technology-selection contract: existing capability/stack first, at most 2–3 realistic options when a material choice remains, constraint-based selection, official support/version verification when decision-critical, and explicit rejection of the nearest alternative.
- Added a stage interaction contract with concrete inputs, outputs, exit criteria, readiness status, limitations, evidence, and next-step reporting while keeping routine implementation details autonomous.
- Replaced test-count/coverage-quantity thinking with behavior/failure/boundary-based selection, deduplication against existing coverage, stage-specific execution, and an explicit verification stopping rule.
- Added behavior-contract eval scenarios for existing-stack technology decisions and proportionate bug verification, including regressions against rewrite-by-default, universal language rankings, fixed coverage quotas, duplicate tests, and unrelated E2E repetition.
- Added a WordPress delivery workflow that distinguishes discovery/bootstrap/implementation/security/lifecycle/UI/WooCommerce/delivery stages and requires verification against the exact installable ZIP for release/distribution work.
- Added `wordpress_artifact.py` to build deterministic single-root plugin ZIPs, verify embedded slug/version and SHA-256, perform safe install-shape smoke checks, and drive WP-CLI install/upgrade/deactivate/reactivate checks against exact artifacts.
- Added guarded uninstall execution for disposable environments and explicit project-specific data-retention verification; deactivation is never treated as uninstall.
- Added a real WordPress CI contract that builds two fixture releases, installs the first exact ZIP, upgrades to the second exact ZIP, and verifies activation/version behavior in a disposable WordPress runtime.
- Added observable code-structure invariants for clear responsibility, data/boundary ownership, entry validation, diagnosable failures, useful separation of decision logic from side effects, evidence-before-abstraction, and minimum safe refactoring in existing codebases.
- Made advanced structure concern-triggered: external integrations require timeout/failure/retry effects, multi-step data changes require transaction/consistency boundaries, multitenancy requires ownership/isolation, and performance structure requires measurement before optimization.
- Explicitly rejected interface-per-class, repository-per-table, service-per-function, DTO/layer ceremony, message/event buses, microservices, and Clean/DDD/layered architecture when no current requirement justifies them.
- Added mandatory behavior-contract eval coverage for small local structure, external integration structure, and multidomain module boundaries, including anti-overengineering regressions.
- Added proportional Plugin Check guidance, conditional HPOS/Cart-Checkout Blocks checks, and an explicit Composer/Packagist fallback because the bundled dependency guard does not claim Composer coverage.
- Hardened release readiness so RC/pre-1.0 releases require Validate Skill, Cross Platform Smoke, Real World Repository Validation, Agent Skills Spec Compatibility, Tool Contract Tests, and WordPress Artifact Contract on the exact target commit.
- Consolidated PR/release tool validation into Tool Contract Tests while keeping dedicated Graphify/Trivy workflows for scheduled/manual compatibility monitoring; removed the duplicate Live Integration Contracts workflow.
- Added release-trigger guarantees for path-filtered validation workflows, orphan-reference detection, and broader merged-branch cleanup for refactor/docs/release work branches.
- Corrected stale validation documentation so real-world routing coverage and bounded conservative eval escalation match current implementation.

## 0.10.2 — Latest-compatible-stable toolchain runtime binding

- Replaced normal operating-version pins for Graphify and Trivy with latest-compatible-stable resolution.
- Added a shared resolver that tests the latest published stable candidate and falls back to a verified last-known-good version when compatibility fails.
- Bound runtime execution to the exact resolved version instead of silently invoking whichever local executable happens to be installed.
- Added exact Graphify execution through a matching local binary or an isolated `uvx --from graphifyy==<version>` runtime, and exact Trivy execution through a matching local binary or versioned official container image.
- Added execution-scoped session pins so a resolved tool version remains stable for the current run without re-resolving mid-execution.
- Removed misleading integration-guard claims that merely detecting an installed executable meant the runtime version was pinned.
- Packaged the resolver, runtime adapter, and Graphify/Trivy compatibility contracts in the portable skill and extended install/sync validation so portable installations cannot omit these runtime dependencies.
- Removed fixed current tool versions from normal user-facing documentation while retaining machine-managed last-known-good fallback state and historical release evidence.
- Expanded CI coverage for latest-compatible-stable resolution, fallback behavior, exact runtime binding, portable installation, cross-platform smoke tests, and live Graphify/Trivy compatibility contracts.
- Kept the credentialed Codex/Claude Code benchmark deferred in Issue #12; deterministic, cross-platform, tool-contract, and pinned real-repository validation remain the active pre-1.0 release baseline.

## 0.10.1 — Real-world routing validation hardening

- Added pinned real-world routing validation against a large Django repository and the official WooCommerce Stripe gateway.
- Extended real-world validation to execute the Context Router and Execution Plan and record project complexity, selected capability packs, pack-reduction ratio, selected context size, integration points, project-intelligence preservation, and execution-plan requirements.
- Added selectivity regressions showing that small WooCommerce admin UI work avoids payment/security/external-HTTP concern packs while payment webhook/refund work composes the sensitive packs and escalates to Tier 3.
- Expanded CI triggers so routing configuration, capability packs, execution planning, and project-intelligence changes automatically run the real-world validation suite.
- Kept product repositories clean while validating pinned external repositories at exact commits.
- Deferred the credentialed blind Codex and Claude Code benchmark to future work in Issue #12; it is not a blocker for the current pre-1.0 release path.

## 0.10.0 — Composable context routing and execution coordination

- Added an evidence-based Context Router that keeps project complexity separate from task risk and selects minimum sufficient context instead of loading broad references by default.
- Added composable Capability Packs for PHP, WordPress, WooCommerce, browser JavaScript, WordPress REST, external HTTP, payments, web security, and web performance.
- Kept Vibe Core authoritative for scope, risk, project intelligence, evidence, recovery, and delivery; domain packs only add relevant constraints, risks, integration points, and checks.
- Added interaction rules so overlapping concerns can raise the workflow floor without making small UI/copy tasks inherit unnecessary payment/security ceremony.
- Added Context Plan metrics for selected packs/references, approximate context bytes, integration points, and preserved invariant/risk/project-intelligence coverage.
- Added lightweight Execution Planning for medium/large projects, Tier 2/3 work, or multi-boundary tasks with explicit workstreams, dependencies, integration ownership, completion levels, and plan-drift approval triggers.
- Kept one implementation agent as the default and required explicit ownership/stable contracts before parallelization.
- Changed the existing-project startup protocol to route context before broad architecture/domain loading while preserving project-wide invariants and large-project impact analysis.
- Added WordPress/WooCommerce constraints for public platform APIs, HPOS/modern compatibility surfaces, plugin/theme interoperability, authorization/input/output boundaries, request/query cost, remote-call failure modes, and payment-state integrity.
- Added deterministic regressions for tiny WooCommerce UI tasks, overlapping WooCommerce payment flows, WordPress REST plus external APIs, browser-JS overlap, large generic repositories, execution-plan dependency validation, and plan drift.
- Added portable packaging and installation/structure validation for routing config, packs, router, planner, and routing reference documentation.

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
