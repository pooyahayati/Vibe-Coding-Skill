# Context Routing and Execution Planning

The router reduces irrelevant context without weakening large-project engineering controls.

## Separation of concerns

- **Project complexity** answers how much coordination/project intelligence is likely to be needed.
- **Task risk** answers how strong the approval, verification, security, and recovery controls must be.
- **Capability packs** answer which platform/runtime/concern constraints are technically relevant.
- **Execution plan** answers who owns what, which work depends on what, and which integration boundaries must be verified.

These dimensions must not be collapsed into one score.

## Context routing

Run before loading broad references when the task and repository are known:

```bash
python scripts/context_router.py \
  --root <project> \
  --task "<current task>" \
  --path <known-affected-path> \
  --json
```

The router uses repository/file/task evidence. It reports confidence and reasons; it does not claim semantic certainty. Re-run it after impact analysis when touched paths were initially unknown.

For large repositories, context reduction means **read more selectively**, not skip project intelligence. Project-wide invariants from project rules/state remain active even when a domain pack is not loaded.

## Capability packs

Packs live under `packs/`. They are short constraint bundles, not tutorials or mini-architectures.

Initial packs cover PHP, WordPress, WooCommerce, browser JavaScript, WordPress REST, external HTTP, payments, web security, and web performance.

Composition is expected. A WooCommerce payment integration may activate several packs at once. Duplicate integration points are deduplicated and interaction rules may raise the risk floor when concerns combine.

## Context budget

The router reports:

- candidate/loaded pack count;
- selected persistent/reference sources;
- estimated Skill-context bytes;
- selected integration-point count;
- preserved invariant/risk/project-intelligence coverage.

The target is **minimum sufficient context**, not minimum context.

## Execution planning

For medium/large projects, Tier 2/3 tasks, or tasks with several integration boundaries:

```bash
python scripts/execution_plan.py draft \
  --root <project> \
  --task "<current task>" \
  --json
```

The default remains one lead implementation agent. Add parallel agents only after explicit workstreams have disjoint ownership or stable producer/consumer contracts. Shared schemas, auth, manifests, central configuration, and shared contracts keep one writer.

A plan distinguishes:

`Task Done → Workstream Done → Objective Done`

Individual task success cannot imply objective success when integration/end-to-end evidence is still missing.

Validate a modified plan:

```bash
python scripts/execution_plan.py validate plan.json --json
```

Check material drift:

```bash
python scripts/execution_plan.py drift plan.json change.json --json
```

Scope, architecture, data semantics, public API, security posture, and significant recurring-cost changes require re-planning/approval rather than silent execution drift.

## WordPress / WooCommerce

The WordPress/WooCommerce packs emphasize interoperability, public platform APIs, authorization/input/output boundaries, request/query cost, compatibility with other plugins/themes, and relevant WooCommerce compatibility surfaces. They supplement Vibe Core and project intelligence rather than replacing them.
