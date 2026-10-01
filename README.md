# Vibe Coding Skill

An engineering skill for reliable AI-assisted development of small, medium, and large software projects, including WordPress plugins. Works with OpenAI Codex, Claude Code, and compatible skill-based agents.

Current version: `1.0.0`

## Start

Install the skill outside your product repository using [the installation guide](HOW_TO_INSTALL.md), then ask your agent:

```text
Use $vibe-coding-skill to inspect and build this project.
```

Vibe inspects the existing system, chooses a suitable approach, implements a small working slice, and verifies the outcome. Workflow depth follows the task's risk and affected boundaries; project size alone does not force extra planning or testing.

## Engineering controls

- Reuse the existing stack and the simplest architecture that meets the requirements.
- Load relevant context, preserve project constraints, and plan significant changes.
- Choose tests from changed behavior and material failure modes; no fixed test or coverage quota.
- Require actual evidence before completion, with recovery and approval controls where risk warrants them.
- Keep generated graphs, scans, caches, and agent state outside product source control.

## UI/UX specialist — unreleased

Vibe remains the project manager and senior engineering Head. The sole design specialist is [UI-UX-Skill](https://github.com/pooyahayati/UI-UX-Skill), which owns UI/UX methods and product routing for supported websites, apps, dashboards, WordPress settings, and other interfaces. Vibe retains scope, architecture, risk, integration, and final acceptance.

For affected UI, the agent must load and use the specialist in Head-delegated mode. The new preflight checks the latest stable Head and required specialists, installs/updates within authorization, and reconciles installed registered skills daily during active tasks. It preserves local edits and records provenance without fixed specialist version pins. See [the composition contract](references/specialist-composition.md).

This functionality is not included in the published `1.0.0` release. Idle update checks require a host scheduler.

## Requirements

Python 3.10+ and Git. Graphify supports impact analysis; Trivy supports security scanning. These tools are optional and used when relevant. Latest-source and dependency checks need network access.

## Documentation

- [Operating instructions](SKILL.md)
- [Version updates](UPDATES.md)
- [Technical changelog](CHANGELOG.md)

MIT · [Pooya Hayati](https://Pooyahayati.com)
