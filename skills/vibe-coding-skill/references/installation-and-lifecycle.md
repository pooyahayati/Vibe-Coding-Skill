# Installation, Cross-platform Support, Upgrade, and Rollback

## Supported baseline

Runtime baseline:

- Python 3.10 or newer;
- Git;
- filesystem access to a local Vibe workspace.

Graphify, Trivy, and GitHub CLI are optional and only required for their respective capabilities.

## Offline installation check

For managed non-Git installations, use `scripts/specialist_manager.py prepare --task "<task>" --project-root <project> --apply --json` before new work. It verifies the current Head and required specialists, preserves backups/local edits, and records provenance outside product source. Read `references/specialist-composition.md`; Head changes require reload before delegation. Existing Git lifecycle commands remain available for explicit checkout maintenance and rollback, but an older checkout is not proof of upstream currency.

Run:

```bash
python scripts/install_check.py --skill-root . --json
```

The check is intentionally offline. It validates:

- Python baseline;
- Git availability;
- Skill metadata;
- the complete portable runtime script set, including release readiness;
- every reference document used by the Skill;
- runtime configuration, eval catalog/schema, Agent metadata, and project templates;
- JSON parseability for runtime config/eval files;
- Python compilation and `--help` import smoke;
- local workspace initialization;
- repository purity behavior.

Missing optional tools produce warnings, not a false installation failure.

An offline PASS/WARN establishes package validity on this host, not upstream currency, specialist instruction compatibility or product correctness. A source checkout and a published ZIP may share a version string while containing different unreleased resources; retain the installed ref/revision and package provenance. Reload changed instructions before use. Publishing or merging does not replace existing local installations.

## Cross-platform policy

Portable core behavior is tested on Linux, macOS, and Windows.

Full external-tool contract tests remain separate because Graphify/Trivy/GitHub availability can vary by platform and environment.

Use `pathlib`, Python subprocess argument arrays, and Git path discovery rather than shell-specific path assumptions.

## Last-known-good installation

Before upgrading a Git-based installation:

```bash
python scripts/skill_lifecycle.py record-good --skill-root . --json
```

The command now runs the offline installation validator first. A dirty or invalid checkout cannot be recorded as last-known-good.

The validation evidence is stored outside the skill repository with the recorded commit/version.

## Upgrade planning

Upgrade planning is local/offline:

```bash
python scripts/skill_lifecycle.py plan-upgrade \
  --skill-root . \
  --target-ref origin/main \
  --json
```

The command does not fetch. If the target ref is absent, fetch/update it explicitly with the installation mechanism first.

A dirty skill installation blocks upgrade planning.

The target commit is checked out into an isolated Git worktree and must pass `install_check.py` before the plan can return PASS/WARN.

## Rollback

Rollback is dry-run by default:

```bash
python scripts/skill_lifecycle.py rollback --skill-root . --json
```

Explicit rollback:

```bash
python scripts/skill_lifecycle.py rollback --skill-root . --apply --json
```

Rollback uses a detached checkout of a previously validated last-known-good commit. It refuses to proceed with local modifications or with a legacy record that contains no validation evidence.

If a shallow/fresh clone no longer contains the recorded commit, reinstall or fetch that version rather than pretending rollback succeeded.

## Installation independence

User project state remains under `~/.vibe-coding/projects/` and is not coupled to the skill checkout.

Reinstalling or rolling back the skill must not delete user project local workspaces.

Keep the Skill checkout outside product repositories. Global/user-level agent skill directories are preferred.

## External tool version resolution

Managed external tools such as Graphify and Trivy use a shared resolution policy:

`Latest Stable Published → Compatibility Contract → Exact Runtime Resolution`

Public instructions do not pin a normal operating version. At install or upgrade time, resolve the latest published stable release and run the tool-specific contract test. The exact version selected for that execution is treated as a runtime pin for reproducibility.

If the latest candidate fails compatibility, use the recorded last-known-good fallback and surface that fallback in the evidence. Do not silently install an untested release.

See `references/toolchain-version-resolution.md`.
