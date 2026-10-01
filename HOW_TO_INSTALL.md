# How to Install

Current Skill version: `1.1.0`

Keep the Skill installation outside the repositories you use it on. Vibe Coding operational state is intentionally local-only.

## Portable release ZIP

Download `Vibe-Coding-Skill-1.1.0.zip` and its SHA-256 checksum file from the [1.1.0 release](https://github.com/pooyahayati/Vibe-Coding-Skill/releases/tag/v1.1.0).
Extract the contained `vibe-coding-skill` directory into your agent's user-level skills directory. Preserve that directory name. The ZIP includes the complete runtime and does not include credentialed model-evaluation runners.
Run the offline installation check below from the extracted directory. Optional tool warnings do not block installation.

## OpenAI Codex

Use the Skill installer with this repository:

```text
Use $skill-installer to install this skill from:
https://github.com/pooyahayati/Vibe-Coding-Skill
```

Then invoke the Skill for a project:

```text
Use $vibe-coding-skill to inspect, plan, and build this project.
```

If installing manually, keep the directory name as `vibe-coding-skill` so it matches the Agent Skill name.

## Claude Code

Recommended global installation:

```bash
git clone --depth 1 https://github.com/pooyahayati/Vibe-Coding-Skill.git \
  "$HOME/.claude/skills/vibe-coding-skill"
```

Do not clone the Skill into a product repository's tracked `.claude/skills/` directory.

Invoke it with:

```text
/vibe-coding-skill
```

## Update an existing Git installation

From the Skill checkout:

```bash
git pull --ff-only
```

The Skill resolves managed external tools such as `Graphify` and `Trivy` using its compatibility-gated latest-stable policy. You do not need to pin their normal operating versions manually.

## Verify the installation

Run the offline installation check from the Skill directory:

```bash
python scripts/install_check.py --skill-root . --json
```

Baseline requirements are `Python 3.10+` and `Git`. `Graphify` and `Trivy` are optional/recommended depending on project risk and task type.

## Local working state

Vibe Coding keeps generated operational state outside your product repository under:

```text
~/.vibe-coding/projects/<project-id>/
```

This includes graph, security, cache, test-artifact, worktree, and agent state.

For lifecycle, rollback, and recovery details, see [references/installation-and-lifecycle.md](references/installation-and-lifecycle.md).
