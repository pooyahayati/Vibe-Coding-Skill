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
