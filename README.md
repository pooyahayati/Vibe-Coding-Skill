# Vibe Coding Skill

[![Validate Skill](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/workflows/validate-skill.yml/badge.svg)](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/workflows/validate-skill.yml)
[![Graphify Compatibility](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/workflows/graphify-compat.yml/badge.svg)](https://github.com/pooyahayati/Vibe-Coding-Skill/actions/workflows/graphify-compat.yml)
![Version](https://img.shields.io/badge/version-0.4.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A risk-adaptive Agent Skill that turns AI-assisted **vibe coding** into controlled, evidence-based software engineering.

Designed for **OpenAI Codex**, **Claude Code**, and other Agent Skills-compatible tools.

## Quick start

### OpenAI Codex

```text
Use $skill-installer to install this skill from:
https://github.com/pooyahayati/Vibe-Coding-Skill
Use $vibe-coding-skill to plan and build this project.
```

Install the repository locally as `vibe-coding-skill` so the directory matches the Agent Skills name.

### Claude Code

Global:

```bash
git clone --depth 1 https://github.com/pooyahayati/Vibe-Coding-Skill.git \
  "$HOME/.claude/skills/vibe-coding-skill"
```

Project-only:

```bash
git clone --depth 1 https://github.com/pooyahayati/Vibe-Coding-Skill.git \
  ".claude/skills/vibe-coding-skill"
```

Then invoke:

```text
/vibe-coding-skill
```

## Core principle

> Use the minimum process required by the current risk.

A typo should not need an architecture review. A destructive production migration should not be treated like a typo.

## What it covers

- product discovery and MVP boundaries;
- requirements prioritization;
- stack, database, and architecture decisions;
- risk-based workflow depth;
- project/code graph analysis;
- staged implementation;
- testing and evidence gates;
- dependency verification;
- security checks;
- Git/GitHub traceability;
- deployment/recovery discipline;
- persistent repository state and handoff;
- controlled multi-agent execution only when it adds value.

## Workflow tiers

| Tier | Typical work | Default process |
|---|---|---|
| 0 — Tiny | copy, isolated fix | Understand → Change → Focused Check |
| 1 — Standard | normal feature | Objective → Impact → Implement → Test → Review |
| 2 — Significant | auth, schema, multi-module, integration | Spec → Graph/Impact → Plan → Implement → Independent Review → Regression/Security |
| 3 — Critical | destructive, sensitive, production-critical | Tier 2 + approvals + rollback/recovery + stronger evidence |

## External dependencies

We deliberately keep them small.

Core:
- Git

Recommended when relevant:
- Graphify — project/code graph
- Trivy — vulnerability, secret, container, IaC, and license scanning

Data providers:
- official package registries
- OSV
- GitHub metadata
- deps.dev as optional additional evidence

The skill owns its decision logic rather than depending on another development methodology.

## Graphify update model

Graphify is the default graph provider, but the skill does not blindly follow new releases.

```text
Latest Stable Graphify
→ Contract Tests
→ Pull Request
→ Review/Merge
→ Approved Version
```

The approved version is stored in `config/toolchain.json`.

## Internal utilities

```text
scripts/
├── doctor.py
├── change_budget.py
├── graphify_compat.py
└── validate_skill.py
```

### Doctor

```bash
python scripts/doctor.py --root /path/to/project --json
```

### Change budget

```bash
python scripts/change_budget.py --root /path/to/project --base main --json
```

### Project bootstrap

```bash
python scripts/bootstrap_project.py \
  --root /path/to/project \
  --profile standard \
  --objective "Deliver the next verified vertical slice" \
  --json
```

The bootstrapper does not overwrite existing project documents by default and skips documents when it does not have enough real project context to populate them.

### Risk classifier

```bash
python scripts/risk_classifier.py "Change authentication from sessions to JWTs" --json
```

### Integration gate

```bash
python scripts/integration_guard.py --root /path/to/project --tier 2 --json
```

The integration gate is read-only and checks Git/GitHub context, Graphify version/freshness, and Trivy availability.

### Dependency Guard

```bash
python scripts/dependency_guard.py pypi requests --version 2.32.5 --json
python scripts/dependency_guard.py npm zod --version 4.1.5 --json
python scripts/dependency_guard.py maven junit:junit --version 4.13.2 --json
python scripts/dependency_guard.py nuget Newtonsoft.Json --version 13.0.3 --json
python scripts/dependency_guard.py go github.com/stretchr/testify --version v1.10.0 --json
```

A missing package/version is rejected. Missing security/provenance evidence becomes `REVIEW REQUIRED`, not a false positive approval.

### Evaluation contracts

`evals/scenarios.json` covers tiny changes, brownfield work, auth, destructive migrations, dependency hallucinations, prompt injection, stale graphs, and production deployment.

```bash
python scripts/validate_evals.py
python scripts/run_evals.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/evaluate_agent_output.py agent-result.json --json
```

### Real-project validation

```bash
python scripts/run_project_validations.py
```

Representative temporary Git repositories cover a tiny static change, brownfield feature work, authentication, destructive production migration, and a multi-module payment integration.

### Failure injection

```bash
python scripts/run_failure_injections.py
```

This deliberately exercises prompt injection, hallucinated packages, vulnerable dependency evidence, stale graphs, and unsupported `Done` claims.

### Completion evidence gate

```bash
python scripts/completion_gate.py completion-report.json --json
```

A `Done` report without acceptance criteria and passing evidence is blocked.

### Agent benchmark

Actual agent results can be aggregated without inventing results for agents that were not run:

```bash
python scripts/benchmark_agent_outputs.py benchmark-results --json
```

See `benchmarks/README.md` for the blind-run protocol.

## External contract tests

Normal CI is deterministic. Scheduled/manual live contracts smoke-test real registries, OSV, Graphify, and Trivy separately so external outages do not make ordinary PRs flaky.

Both Graphify and Trivy use approved-version tracking in `config/toolchain.json`.

## Portable package

The repository root remains the canonical source. `scripts/sync_package.py` generates and verifies the portable Agent Plugin mirror under:

```text
skills/vibe-coding-skill/
```

This prevents Codex/Plugin packaging from drifting away from the canonical skill.

```bash
python scripts/sync_package.py --check
```

## Repository structure

```text
Vibe-Coding-Skill/
├── SKILL.md
├── references/
├── scripts/
├── config/
├── assets/templates/
├── evals/
├── validation/
├── benchmarks/
├── agents/
├── skills/vibe-coding-skill/   # generated portable mirror
├── tests/
├── plugin.json
├── .github/workflows/
├── CHANGELOG.md
├── SECURITY.md
├── CONTRIBUTING.md
├── LICENSE
└── VERSION
```

## Status

Current version: `0.4.0`

This is the first implementation of the V11 direction derived from the Software Project Operating Protocol and the review of current vibe-coding failure modes.

## Author

**Pooya Hayati | پویا حیاتی**

https://Pooyahayati.com
