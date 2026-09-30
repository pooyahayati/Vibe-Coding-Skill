# Context Routing and Execution Planning

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

### Structured context facts

When platform/runtime/capability/concern semantics are known but wording is ambiguous or language-dependent, pass canonical facts instead of adding more natural-language keyword variants:

```text
--context-runtime php
--context-platform wordpress
--context-capability woocommerce
--context-concern payments
```

Supported fact fields are `runtime`, `platform`, `capability`, and `concern`. Values are config-driven by each capability pack and invalid values fail explicitly instead of being silently ignored. Structured facts are semantic routing evidence; text/path/source signals remain supplemental discovery evidence.

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

The default remains one lead implementation agent. Parallel agents require disjoint ownership or stable producer/consumer contracts. Shared schemas, auth, manifests, central configuration, and shared contracts keep one writer.

A plan distinguishes:

`Task Done → Workstream Done → Objective Done`

Individual task success cannot imply objective success while required dependencies or integration evidence remain incomplete.

Validate or check drift:

```bash
python scripts/execution_plan.py validate plan.json --json
python scripts/execution_plan.py drift plan.json change.json --json
```

Material changes to scope, architecture, data semantics, public API, security posture, or significant recurring cost require re-planning/approval.

## Context metrics

The router reports candidate/loaded pack count, selected persistent/reference sources, integration points, project scanning cost, and preservation of project invariants/risk/project intelligence. It keeps the legacy selected Skill-context byte estimate and also reports separate core/reference/pack byte counts, a persistent-project-context upper bound, a combined context upper bound, and whether scanning used `path-scoped` or `fallback-project-scan` mode.

Use these metrics to detect context bloat or missing coverage; do not optimize them at the expense of correctness.

## WordPress / WooCommerce

WordPress/WooCommerce packs supplement Vibe Core and project intelligence. They apply only when platform evidence exists and emphasize public APIs, interoperability, authorization/input/output boundaries, lifecycle, request/query cost, plugin/theme compatibility, and relevant WooCommerce order/payment compatibility surfaces.
