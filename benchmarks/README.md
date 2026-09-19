# Agent Benchmark

This benchmark measures whether a real coding agent follows the Vibe Coding Skill's behavioral contract. It does not score writing style and it never fabricates results for an agent that was not actually run.

## Supported real adapters

- OpenAI Codex CLI
- Anthropic Claude Code

Adapter metadata lives in `config/agent-benchmarks.json`.

The runner uses project-scoped temporary Skill installs inside an isolated temporary Git repository. No user project repository is modified.

## Blind-run integrity

For each scenario in `evals/scenarios.json`:

1. Give the evaluated agent only the installed skill, scenario ID, scenario prompt, and output schema.
2. Do not reveal `expected_tier`, `required_controls`, `forbidden_controls`, or scorer output.
3. Require the strict JSON shape in `evals/agent-output.schema.json`.
4. Run in a temporary Git repository with minimal permissions.
5. Preserve raw stdout/stderr plus the structured contract.
6. Record CLI version, model override, Skill version, timing, hashes, and workspace-integrity evidence.
7. Score only after the agent run has finished.

## Authentication

For reproducible non-interactive runs:

- Codex: `OPENAI_API_KEY`
- Claude Code: `ANTHROPIC_API_KEY` or supported Claude Code automation credentials

The runner only records credential-variable names that are present. It never records credential values.

## Local run

```bash
python scripts/run_agent_benchmark.py preflight \
  --agent codex \
  --require-env-auth \
  --json

python scripts/run_agent_benchmark.py run \
  --agent codex \
  --scenario all \
  --results-dir ~/.vibe-coding/benchmarks/vibe-coding-skill/0.8.0/my-run \
  --require-env-auth \
  --json
```

Repeat for `claude-code`.

## GitHub Actions run

`.github/workflows/agent-benchmark.yml` is manual-only because real-agent evaluation consumes provider usage.

The workflow requires repository secrets:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

It installs the requested CLI versions, executes all scenarios for both agents, requires complete evidence, and uploads raw results as a GitHub Actions artifact. The artifact is not committed to the repository.

## Evidence directory

```text
RESULTS_DIR/
├── codex/
│   ├── tiny-copy-fix.json
│   ├── tiny-copy-fix.stdout.txt
│   ├── tiny-copy-fix.stderr.txt
│   ├── ...
│   └── run-summary.json
├── claude-code/
│   └── ...
└── aggregate.json
```

## Aggregation

```bash
python scripts/benchmark_agent_outputs.py RESULTS_DIR \
  --required-agent codex \
  --required-agent claude-code \
  --require-complete \
  --json
```

A conformance rate is emitted only for a complete evidence set. A partial run can still be inspected, but it is reported as incomplete.

This benchmark is a conformance test, not a model leaderboard.
