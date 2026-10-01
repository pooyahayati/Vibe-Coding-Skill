# Contributing

Contributions should preserve:

1. minimum total complexity;
2. risk-adaptive process;
3. evidence before confidence;
4. one source of project truth;
5. no mandatory dependency unless rebuilding the capability would be materially worse;
6. no new workflow ceremony without demonstrated risk or outcome benefit.

For meaningful changes, explain the problem, show why the current skill does not handle it, keep the change modular, update validation/tests, and update the technical changelog.\n\nFor every version bump, also add a short human-readable entry to `UPDATES.md`. Keep `README.md` as a concise project overview and keep installation steps in `HOW_TO_INSTALL.md`.

Run:

```bash
python scripts/validate_skill.py
python -m py_compile scripts/*.py
```

## Roadmap progress

[ROADMAP.md](ROADMAP.md) is the canonical improvement tracker. For roadmap-related work, use its stable package ID and update the status, current phase, next action and PR/commit evidence when work starts, becomes blocked or is verified/merged. A Complete status requires the package acceptance conditions and relevant checks; a proposed completion update becomes effective with the merged implementation. Keep release and installation status separate. Do not mark planning, an open PR or source edits as delivered functionality.

Maintain scope/dependency/acceptance changes in the [implementation plan](docs/improvement-implementation-plan.md). Keep routine status in the roadmap instead of duplicating it in chat summaries or creating another tracker.
