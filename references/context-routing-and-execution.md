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

The router uses repository/file/task evidence. It reports confidence and reasons; it does not claim semantic certainty. Project scanning is bounded and its file/byte cost is reported in metrics. Re-run routing after impact analysis when touched paths were initially unknown.

For large mixed/monorepo projects, project-scoped platform/runtime packs are kept local to the task area when path evidence is available; the presence of an unrelated WordPress/PHP subproject must not pollute another service's task context. Documentation mentions alone are not treated as source-level platform evidence.

When deterministic evidence is incomplete but a developer/agent has explicit semantic evidence, add a pack with `--include-pack <name>`. This override is additive only: routing may add missing relevant context, but there is no symmetric command for silently suppressing detected risk/domain packs.

For large repositories, context reduction means **read more selectively**, not skip project intelligence. The router extracts explicit invariant/constraint bullets from existing project documents when present, carries them in the Context Plan, and keeps large-project project-intelligence policy active even for a low-risk domain task.

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

For medium/large projects or Tier 2/3 tasks:

```bash
python scripts/execution_plan.py draft \
  --root <project> \
  --task "<current task>" \
  --json
```

The draft is a **coordination skeleton**, not an approved architecture. Candidate integration boundaries must be confirmed, assigned a concrete contract/evidence expectation, and the edited plan should pass `execution_plan.py validate` before parallel execution or shared-contract changes.

The default remains one lead implementation agent. Add parallel agents only after explicit workstreams have disjoint ownership or stable producer/consumer contracts. Validation rejects dependency cycles, conflicting ownership scopes, and incomplete integration contracts. Shared schemas, auth, manifests, central configuration, and shared contracts keep one writer.

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

Scope, architecture, data semantics, public API, security posture, and significant recurring-cost changes require re-planning/approval rather than silent execution drift. Changed paths outside declared workstream ownership are also treated as scope drift.

## WordPress / WooCommerce

The WordPress/WooCommerce packs emphasize interoperability, public platform APIs, authorization/input/output boundaries, request/query cost, compatibility with other plugins/themes, and relevant WooCommerce compatibility surfaces. They supplement Vibe Core and project intelligence rather than replacing them.
