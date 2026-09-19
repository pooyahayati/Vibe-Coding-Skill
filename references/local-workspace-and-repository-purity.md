# Local Workspace and Repository Purity

## Principle

Tooling state is local engineering intelligence, not project source.

The project repository should contain only assets that another developer needs to build, test, understand, deploy, or maintain the product.

Keep these local-only:

- the Vibe Coding Skill checkout itself;
- Graphify generated graph data, HTML, cache, and provider state;
- Trivy reports and caches;
- coverage and test-run reports;
- agent benchmark outputs;
- temporary worktrees;
- AI scratch/debug state;
- Vibe Coding operational state.

Keep these in Git when they are real project assets:

- source code;
- product tests;
- migrations;
- manifests and lock files;
- README and meaningful project documentation;
- Docker/deployment configuration when the product actually uses it;
- CI configuration that belongs to the product.

## Local workspace

Default root:

`~/.vibe-coding/projects/<project-id>/`

Override for CI/tests or custom setups:

`VIBE_CODING_HOME=/custom/path`

Structure:

```text
<project-id>/
├── state/
├── graph/
├── security/
├── test-artifacts/
├── benchmarks/
├── worktrees/
├── cache/
└── metadata.json
```

Initialize:

```bash
python scripts/local_workspace.py init --root /path/to/project --json
```

The project ID is derived from the Git remote plus the resolved local project path so same-named repositories do not collide accidentally.

## Local Git excludes

The workspace initializer writes only to:

`.git/info/exclude`

It does not edit the project's `.gitignore`.

This keeps local tooling artifacts invisible to normal Git status without imposing Vibe Coding-specific ignore rules on other contributors.

Typical local-only exclusions include:

- `.vibe/`
- `graphify-out/`
- `.trivy/`
- `benchmark-results/`
- generated coverage/report directories;
- `.claude/skills/vibe-coding-skill/`
- `.codex/skills/vibe-coding-skill/`
- `.agents/skills/vibe-coding-skill/`

The last three are defensive exclusions for accidental project-local Skill checkouts. The recommended installation remains outside the product repository.

## Repository purity gate

Before commit or push:

```bash
python scripts/repository_purity.py --root . --json
```

For a stricter local setup check:

```bash
python scripts/repository_purity.py --root . --strict-excludes --json
```

The gate blocks tracked or staged Vibe/tool artifacts and project-local Vibe Skill checkouts. It deliberately does not block product tests such as `tests/`.

## Graphify

Graphify runs against a shadow source copy in the local Vibe workspace. Generated `graphify-out/` must not be committed.

Graph freshness metadata belongs in:

`<local-workspace>/state/graph-state.json`

not in the project repository.

## Trivy

Write scan output to the local workspace, for example:

`<local-workspace>/security/trivy.json`

Do not commit scan reports merely to prove a local scan ran. Record only the human-relevant security decision or remediation in normal project artifacts when necessary.

## Tests

Product tests belong in Git.

Generated test artifacts do not.

```text
tests/                 ← Git
coverage/              ← local-only
htmlcov/               ← local-only
test-results/          ← local-only
playwright-report/     ← local-only
```

## CI

Do not add Graphify, Trivy, Vibe Coding state, or AI benchmark workflows to a user's GitHub repository by default.

Product CI should contain only checks justified by the product itself.

The Vibe Coding Skill repository is different: it may run compatibility tests for Graphify/Trivy because those tools are dependencies of the skill itself.
