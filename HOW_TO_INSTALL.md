# How to Install

Current Skill version: `1.4.0`, the release package. Main-branch changes under [Unreleased](CHANGELOG.md#unreleased) are separate from this release. Choose the published package for a stable installation; a source checkout follows its selected ref, even if `VERSION` has not yet changed.

Keep the Skill installation outside the repositories you use it on. Vibe Coding operational state is intentionally local-only.

## Portable release ZIP

Download `Vibe-Coding-Skill-1.4.0.zip` and its SHA-256 checksum file from the [1.4.0 release](https://github.com/pooyahayati/Vibe-Coding-Skill/releases/tag/v1.4.0).
Extract the contained `vibe-coding-skill` directory into your agent's user-level skills directory. Preserve that directory name. The ZIP includes the complete runtime and does not include credentialed model-evaluation runners.
Run the offline installation check below from the extracted directory. Optional tool warnings do not block installation.

## OpenAI Codex

Use the Skill installer with this repository:

```text
Use $skill-installer to install this skill from:
https://github.com/pooyahayati/Vibe-Coding-Skill
Use ref v1.4.0 and path skills/vibe-coding-skill for the published version.
```

Then invoke the Skill for a project:

```text
Use $vibe-coding-skill to inspect, plan, and build this project.
```

If installing manually, keep the directory name as `vibe-coding-skill` so it matches the Agent Skill name.

## Claude Code

Recommended global installation:

```bash
git clone --depth 1 --branch v1.4.0 https://github.com/pooyahayati/Vibe-Coding-Skill.git \
  "$HOME/.claude/skills/vibe-coding-skill"
```

Do not clone the Skill into a product repository's tracked `.claude/skills/` directory.

Invoke it with:

```text
/vibe-coding-skill
```

## Update an existing Git installation

Inspect the current installation, preserve local edits and record a validated backup before replacing it. A published-tag installation is detached; reinstall the chosen latest stable ZIP/tag through the installation mechanism rather than running `git pull` there.

For an explicitly chosen source branch installation, from its clean Skill checkout:

```bash
git pull --ff-only
```

This updates that branch, not necessarily the latest stable release. The task-start Head/specialist preflight resolves stable upstream currency separately; an offline installation check cannot establish it. Reload updated instructions and rerun preflight before delegation. See [upgrade and rollback guidance](references/installation-and-lifecycle.md).

The Skill resolves managed external tools such as `Graphify` and `Trivy` using its compatibility-gated latest-stable policy. You do not need to pin their normal operating versions manually.

## Verify the installation

Run the offline installation check from the Skill directory:

```bash
python scripts/install_check.py --skill-root . --json
```

Baseline installation requirements are `Python 3.10+` and `Git`; Graphify is conditional. A missing Trivy warning does not prevent installing the Skill or safe development. Before publishing software, however, install a verified native Trivy executable on the delivery host and pass the [local release gate](references/security-and-dependencies.md#native-release-gate). Presence or an offline installation check alone is not security approval.

## Local working state

Vibe Coding keeps generated operational state outside your product repository under:

```text
~/.vibe-coding/projects/<project-id>/
```

This includes graph, security, cache, test-artifact, worktree, and agent state.

For lifecycle, rollback, and recovery details, see [references/installation-and-lifecycle.md](references/installation-and-lifecycle.md).
