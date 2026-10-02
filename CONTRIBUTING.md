# Contributing

Contributions should preserve:

1. minimum total complexity;
2. risk-adaptive process;
3. evidence before confidence;
4. one source of project truth;
5. no mandatory dependency unless rebuilding the capability would be materially worse;
6. no new workflow ceremony without demonstrated risk or outcome benefit.

For meaningful changes, explain the problem, show why the current skill does not handle it, keep the change modular and update the technical changelog. Add tests only for meaningful uncovered behavior or failure modes; reuse existing coverage. For every version bump, also add a short human-readable entry to `UPDATES.md`. Keep `README.md` as a concise project overview and installation steps in `HOW_TO_INSTALL.md`.

Edit canonical root files; `skills/vibe-coding-skill/` is the portable mirror, not a second source of truth. Synchronize affected runtime resources, then check:

```bash
python scripts/validate_skill.py
python scripts/sync_package.py --check
```

During Build, use the smallest relevant reproduction/check. Before integration, run affected regressions and existing required CI; do not repeat unrelated suites after wording-only edits. Documentation changes need accuracy, relevant link/resource checks and mirror consistency, not new tests that merely check wording.

For runtime/packaging changes, use the offline install check and affected [portable integration routes](docs/i1-integration-verification.md). Before publication, the [release gate](references/validation-and-benchmarking.md#release-readiness) still requires its existing same-commit baseline. Maintainer fixtures prove tested tooling behavior, not model quality or every application's correctness. No model evaluation or provider API key is required.

## Roadmap progress

[ROADMAP.md](ROADMAP.md) is the canonical improvement tracker. For roadmap-related work, use its stable package ID and update the status, current phase, next action and PR/commit evidence when work starts, becomes blocked or is verified/merged. A Complete status requires the package acceptance conditions and relevant checks; a proposed completion update becomes effective with the merged implementation. Keep release and installation status separate. Do not mark planning, an open PR or source edits as delivered functionality.

Maintain scope/dependency/acceptance changes in the [implementation plan](docs/improvement-implementation-plan.md). Keep routine status in the roadmap instead of duplicating it in chat summaries or creating another tracker.
