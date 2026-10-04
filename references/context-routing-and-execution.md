# Context Routing and Execution Planning

## Required specialists

The router's `required_specialists` field is offline selection, not installation or execution evidence. The four registered domains are UI/UX, application security, interface contracts, and systematic debugging. Explicit semantic concerns, relevant task signals and affected surfaces select only matching specialists; documentation-only paths suppress runtime text signals unless an explicit concern/selection establishes real domain work. A stage alone never selects specialists.

Use `--stage discover|define|plan|design|build|verify|review|ship` (router defaults to Discover; execution-plan drafts default to Plan). Assignments carry stage, `active_in_stage`, protected authority and domain outcome; inactive assignments are preparation-only. The execution plan retains them as `specialist_assignments`. Re-route after impact analysis and stage changes. Structured concerns such as `ui`, `security`, `contracts`, `debugging` and `payments` avoid language-dependent guesses. Sensitive-data risk facts also select security without selecting UI. Platform packs remain independently evidence-gated.

Before actual use, resolve/install/read the selected current specialist and its `vibe-head-contract.md`; assign only the current boundary under `references/specialist-composition.md`. Backend-only changes do not require design, and an obvious contained bug does not automatically require debugging.

The router reduces irrelevant context without weakening project intelligence or risk controls.

## Independent dimensions

Keep these dimensions separate:

- **Project complexity** — how much architecture/project-intelligence context may be needed.
- **Task risk** — how strong approval, verification, security, and recovery controls must be.
- **Change scope** — whether known affected paths are local, bounded, or cross-boundary.
- **Delivery stage** — discovery, implementation, merge, release, or operation; each stage has different evidence needs.
- **Capability packs** — which platform/runtime/concern constraints are technically relevant.
- **Execution plan** — ownership, dependencies, contracts, and integration coordination when actually required.

A large repository can contain a tiny local task. A small repository can contain a critical task. Project size alone is never a substitute for risk or change scope.

## Context routing

Run before loading broad references when the task and repository are known:

```bash
python scripts/context_router.py \
  --root <project> \
  --task "<current task>" \
  --path <known-affected-path> \
  --json
```

The router uses repository/file/task evidence plus optional structured context facts. It reports confidence, risk, change scope, selected packs, and bounded context metrics. When affected paths are known, source-marker scanning is path-scoped: it inspects the affected project area plus shallow repository-root signals instead of scanning unrelated application areas. Re-run after impact analysis when affected paths were initially unknown.

For a greenfield project, estimate expected complexity from the problem, integration/deployment boundaries, data ownership, and known growth requirements. When that estimate matters before files exist, pass an explicit `--complexity <small|medium|large>` rather than treating an empty directory as proof of a small product.

### Platform gating

Platform-specific packs require platform evidence when configured with `activation_requires`.

For example, generic phrases such as `REST API` or `API route` must not activate the WordPress REST pack unless WordPress is also evidenced by the task, affected project area, or an explicit semantic include. This prevents a generic FastAPI/Node/backend task from inheriting WordPress/PHP rules.

When deterministic evidence is incomplete but the developer/agent has explicit semantic evidence, `--include-pack <name>` is additive. It may add context; it must not silently suppress detected risk or domain constraints.

For mixed repositories, project-scoped evidence is kept local to the affected area when path evidence is available. Common monorepo containers such as `apps/`, `packages/`, `services/`, `plugins/`, and `themes/` treat the contained application/package as the capability area; WordPress plugin/theme directories under `wp-content/` are scoped the same way. Repository-root platform evidence remains repository-wide. Documentation mentions alone are not source-level platform evidence.

Directory paths are valid affected-path evidence. The router inspects a bounded subset of text/source files inside that directory so a caller does not need an exact file path before routing.

### Bounded inspection and uncertainty

Oversized sources are read as bounded binary prefixes, not discarded or read completely before slicing. Each scan has its own hard limits: area-header discovery uses at most 600 files, 8 KiB per file and 4 MiB total; project markers use 600 files, 64 KiB per file and 8 MiB total; affected paths use 120 files, 64 KiB per file and 1 MiB total; invariant extraction uses 120 documents, 256 KiB per file and 1 MiB total. A remaining byte budget may shorten the last prefix. Header discovery prioritizes known affected paths; project-marker locality and root signals remain unchanged.

`context_plan.inspection.scans` distinguishes attempted/read files, actual bytes read, truncated prefixes, unreadable files and omissions caused by file/byte limits. Path samples are capped at 20 per scan. `project_text_files_scanned` counts successfully read project candidates, including readable empty files; `project_text_bytes_scanned` counts actual input bytes. Separate scans may read the same file; their metrics describe read operations, not unique repository coverage. These limits bound content reads, not the existing filename inventory.

Incomplete inspection appears in `task.routing_uncertainties` and as warnings in non-JSON CLI output. The Head must assess whether a limitation affects the task's platform, entrypoints or governing instructions before treating missing evidence as absence. Inspect the specific missing region/source, provide confirmed structured context facts or explicit pack inclusion as appropriate, then re-route; retain unresolved limitations. Do not select WordPress merely because a PHP prefix is incomplete, or suppress a known platform because its marker was not reached. Routing uncertainty is separate from the risk-classifier floor; it does not automatically raise a tier or require a new execution plan. Invariant extraction is supplemental: applicable `AGENTS.md` instructions still require full reading.

Custom sibling areas are inferred from package manifests and WordPress plugin headers. For layouts that cannot be inferred, set `project_area_roots` (for example `["components/api", "components/store"]`) or `project_area_containers` (for example `["components"]`) in the routing configuration. Each WordPress plugin under `wp-content/plugins/` is a distinct area. These are discovery hints, not proof of dependency isolation; confirm actual shared contracts during impact analysis.

### Structured context facts

When platform/runtime/capability/concern semantics are known but wording is ambiguous or language-dependent, pass canonical facts instead of adding more natural-language keyword variants:

```text
--context-runtime php
--context-platform wordpress
--context-capability woocommerce
--context-concern payments
```

Supported fact fields are `runtime`, `platform`, `capability`, and `concern`. Ordinary runtime identifiers such as `python`, `go`, and `rust` are valid even when no specialist pack exists; they do not manufacture a pack. Platform/capability/concern values remain config-driven and invalid values fail explicitly. Structured facts are semantic routing evidence; text/path/source signals remain supplemental discovery evidence.

Equivalent requests in different human languages should select the same packs when supplied the same structured context facts.

## Project intelligence under context reduction

Context reduction means **read selectively**, not ignore architecture.

Large repositories retain project-intelligence policy even for low-risk local work. Tier 2/3 work also retains it regardless of repository size. Existing project invariants are extracted and carried into the Context Plan without forcing the whole project documentation set into every task.

Applicable `AGENTS.md` files are not reduced to invariant extraction: the repository-root file and any file governing the affected subtree are selected as full persistent instructions. Unrelated sibling `AGENTS.md` files are excluded.

The target is **minimum sufficient context**, not minimum context.

## Capability packs

Packs under `packs/` are short constraint bundles, not tutorials or alternative methodologies.

Current packs cover PHP, WordPress, WooCommerce, browser JavaScript, WordPress REST, external HTTP, payments, web security, and web performance.

Composition is expected when evidence overlaps. Interaction rules may add concern packs or raise the risk floor. Duplicate packs and integration points are deduplicated.

## Change scope

The router reports a task-scope level:

- `local` — one known affected path;
- `bounded` — multiple known paths inside one project area;
- `cross-boundary` — affected paths span project areas or explicit cross-module/system impact is detected;
- `unknown` — affected paths are not known yet.

Scope is evidence, not a permanent label. Re-route when new affected paths are discovered.

## Execution planning

A **new** execution plan is required when:

- final task risk is Tier 2 or Tier 3; or
- the known change scope is `cross-boundary`.

Project complexity alone does not require a new plan. A local typo or contained Tier 1 change in a medium/large repository stays on the light route while retaining relevant project intelligence.

When a current plan already covers the objective, scope, ownership, dependencies, and contracts, reuse and validate it instead of producing a duplicate plan.

Draft when required:

```bash
python scripts/execution_plan.py draft \
  --root <project> \
  --task "<current task>" \
  --path <known-affected-path> \
  --json
```

The draft is a coordination skeleton, not an approved architecture. Candidate integration boundaries must be confirmed and assigned concrete contract/evidence expectations before parallel execution or shared-contract changes.

Pass the same structured risk facts used for routing through the planner's `--risk-*` options. Reclassifying ambiguous task text without those facts can lose a previously established workflow floor.

The default remains one lead implementation agent. Parallel agents require disjoint ownership or stable producer/consumer contracts. Shared schemas, auth, manifests, central configuration, and shared contracts keep one writer.

A plan distinguishes:

`Task Done → Workstream Done → Objective Done`

Individual task success cannot imply objective success while required dependencies or integration evidence remain incomplete.

Validate or check drift:

Ownership and drift scopes are project-relative. `.` owns the whole project; `./` and backslash/dot-component equivalents have the same meaning. A root owner overlaps any nested owner, while disjoint sibling scopes remain valid. Retained-contract containment uses the same dot-component normalization without changing stored contracts or their fingerprints. Bracket and hidden names stay literal. Root coverage never covers absolute/parent-escaping changed paths or bypasses material architecture/security/other drift triggers; unresolved placeholder scopes remain discovery hints, not concrete ownership.

```bash
python scripts/execution_plan.py validate plan.json --json
python scripts/execution_plan.py drift plan.json change.json --json
```

Material changes to scope, architecture, data semantics, public API, security posture, or significant recurring cost require re-planning/approval.

### Retained behavior in a plan (B2)

When a structured task contract is useful, reuse the accepted `vibe-task-contract` version-1 record described in [shared contracts](shared-improvement-contracts.md). Keep its snapshot outside product source control. No extra JSON document is required for a tiny task that already has a clear inline criterion.

```bash
python scripts/execution_plan.py draft --root <project> --task-contract <accepted-contract.json> --json
python scripts/execution_plan.py validate <plan.json> --task-contract <accepted-contract.json> --json
```

The draft derives the objective/scope from the contract, preserves its full criteria/behavior and fingerprint, and links workstreams to criterion/evidence-requirement IDs. Refine those links when splitting work: every required outcome and its obligation must remain owned. Out-of-scope draft paths and missing/unknown required links are errors. The effective `planning_basis.risk_tier` and `risk_policy` retain the higher of the accepted risk floor and router classification; the context plan remains the classification snapshot. A retained Tier 2/3 floor requires planning even when task wording sounds tiny.

Validate reused/edited plans against the independently retained contract to detect removed/rewritten required outcomes, protected behavior, evidence obligations or binding. `task_contract_checked` and `acceptance_baseline_checked` distinguish binding validation from legacy unbound reading. A hash alone does not protect an agent-editable baseline or authenticate approval; caller/host writer controls remain necessary. Legacy plan version 1 remains supported without a contract; that route does not establish retained-behavior validation. Receipt verification remains E1/E2 work.

## Context metrics

The router reports candidate/loaded pack count, selected persistent/reference sources, integration points, project scanning cost, and preservation of project invariants/risk/project intelligence. It keeps the legacy selected Skill-context byte estimate and also reports separate core/reference/pack byte counts, a persistent-project-context upper bound, a combined context upper bound, and whether scanning used `path-scoped` or `fallback-project-scan` mode.

Use these metrics to detect context bloat or missing coverage; do not optimize them at the expense of correctness.

## WordPress / WooCommerce

WordPress/WooCommerce packs supplement Vibe Core and project intelligence. They apply only when platform evidence exists and emphasize public APIs, interoperability, authorization/input/output boundaries, lifecycle, request/query cost, plugin/theme compatibility, and relevant WooCommerce order/payment compatibility surfaces.
