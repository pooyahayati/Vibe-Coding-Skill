# Vibe Coding Skill

[![Validate Skill](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/workflows/validate-skill.yml/badge.svg)](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/workflows/validate-skill.yml)
[![Graphify Compatibility](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/workflows/graphify-compat.yml/badge.svg)](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/workflows/graphify-compat.yml)
![Version](https://img.shields.io/badge/version-0.10.7-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A risk-adaptive Agent Skill for turning AI-assisted **vibe coding** into controlled, evidence-based software engineering.

Designed for **OpenAI Codex**, **Claude Code**, and other Agent Skills-compatible tools.

> Use the minimum process required by the current risk.

## Start here

- **Install:** [HOW_TO_INSTALL.md](HOW_TO_INSTALL.md)
- **What changed in each version:** [UPDATES.md](UPDATES.md)
- **Full technical changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Skill operating instructions:** [SKILL.md](SKILL.md)

Current version: `0.10.7`

## What it does

- adapts workflow depth to task risk;
- keeps large-project context focused instead of loading everything;
- preserves architecture, dependency, integration, and project-intelligence awareness;
- plans significant work before implementation;
- verifies dependencies and security-sensitive changes;
- requires evidence before declaring work complete;
- keeps generated graph, scan, benchmark, cache, and agent state outside product repositories;
- supports recovery, handoff, Git/GitHub traceability, and controlled multi-agent work.

## Workflow levels

| Tier | Typical work | Process |
|---|---|---|
| 0 — Tiny | copy, isolated fix | Understand → Change → Focused Check |
| 1 — Standard | normal feature | Objective → Impact → Implement → Test → Review |
| 2 — Significant | auth, schema, multi-module, integration | Spec → Impact → Plan → Implement → Review → Regression/Security |
| 3 — Critical | destructive, sensitive, production-critical | Tier 2 + approvals + rollback/recovery + stronger evidence |

## Large and mixed projects

The `Context Router` keeps **project complexity**, **task risk**, and **change scope** separate and loads only the minimum relevant capability packs.

Current packs cover:

`PHP` · `WordPress` · `WooCommerce` · browser JavaScript · WordPress REST · external HTTP · payments · web security · web performance

Large repositories retain project intelligence even when a local low-risk task stays lightweight. A new execution plan is driven by Tier 2/3 risk or demonstrated cross-boundary scope—not repository size alone.

## Tooling

Core requirement: `Git`.

Recommended when relevant:

- `Graphify` — project/code graph and impact analysis
- `Trivy` — vulnerabilities, secrets, containers, IaC, and licenses

Managed tools use a **latest-compatible-stable** policy:

```text
Latest Stable Published
→ Compatibility Contract
→ Exact Runtime Version
→ Use
```

If the newest stable version fails compatibility checks, the Skill falls back to a verified last-known-good version.

## Clean repository policy

Product repositories contain product code, real tests, migrations, manifests, lock files, and meaningful project documentation.

Generated Vibe/Graphify/Trivy/coverage/benchmark/cache/agent-state artifacts stay local under:

```text
~/.vibe-coding/projects/<project-id>/
```

## Documentation

- [Installation and lifecycle](HOW_TO_INSTALL.md)
- [Human-readable update catalog](UPDATES.md)
- [Technical changelog](CHANGELOG.md)
- [Context routing and execution](references/context-routing-and-execution.md)
- [Project intelligence](references/project-intelligence.md)
- [Security and dependencies](references/security-and-dependencies.md)
- [Validation and benchmarking](references/validation-and-benchmarking.md)
- [Toolchain version resolution](references/toolchain-version-resolution.md)

## Future work

The credentialed blind benchmark against real `Codex` and `Claude Code` runs remains deferred in Issue #12. Missing benchmark evidence is not treated as success.

## License

`MIT`

## Author

**Pooya Hayati | پویا حیاتی**

https://Pooyahayati.com
