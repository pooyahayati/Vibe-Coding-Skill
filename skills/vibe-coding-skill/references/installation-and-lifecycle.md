# Installation, Cross-platform Support, Upgrade, and Rollback

## Supported baseline

Runtime baseline:

- Python 3.10 or newer;
- Git;
- filesystem access to a local Vibe workspace.

Graphify, Trivy, and GitHub CLI are optional and only required for their respective capabilities.

## Offline installation check

Run:

    python scripts/install_check.py --skill-root . --json

The check is intentionally offline. It validates:

- Python baseline;
- Git availability;
- Skill metadata;
- required runtime scripts/references;
- Python compilation and --help import smoke;
- local workspace initialization;
- repository purity behavior.

Missing optional tools produce warnings, not a false installation failure.

## Cross-platform policy

Portable core behavior is tested on Linux, macOS, and Windows.

Full external-tool contract tests remain separate because Graphify/Trivy/GitHub availability can vary by platform and environment.

Use pathlib, Python subprocess argument arrays, and Git path discovery rather than shell-specific path assumptions.

## Last-known-good installation

Before upgrading a Git-based installation:

    python scripts/skill_lifecycle.py record-good --skill-root . --json

This records the clean current commit/version outside the skill repository.

## Upgrade planning

Upgrade planning is local/offline:

    python scripts/skill_lifecycle.py plan-upgrade --skill-root . --target-ref origin/main --json

The command does not fetch. If the target ref is absent, fetch/update it explicitly with the installation mechanism first.

A dirty skill installation blocks upgrade planning.

## Rollback

Rollback is dry-run by default:

    python scripts/skill_lifecycle.py rollback --skill-root . --json

Explicit rollback:

    python scripts/skill_lifecycle.py rollback --skill-root . --apply --json

Rollback uses a detached checkout of the recorded last-known-good commit. It refuses to proceed with local modifications.

If a shallow/fresh clone no longer contains the recorded commit, reinstall or fetch that version rather than pretending rollback succeeded.

## Installation independence

User project state remains under ~/.vibe-coding/projects/ and is not coupled to the skill checkout.

Reinstalling or rolling back the skill must not delete user project local workspaces.
