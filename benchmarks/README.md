# Agent Benchmark

This benchmark measures whether an agent follows the Vibe Coding Skill's behavioral contract. It does not score writing style and it does not fabricate results for agents that were not actually run.

## Blind run

For each scenario in `evals/scenarios.json`:

1. Give the evaluated agent only the scenario prompt/context and the installed skill.
2. Do not reveal `expected_tier`, `required_controls`, or `forbidden_controls`.
3. Require the JSON output shape documented in `evals/AGENT_OUTPUT_SCHEMA.md`.
4. Save each result in the project's local Vibe Coding workspace, not in the Git repository:

```text
~/.vibe-coding/projects/<project-id>/benchmarks/
├── codex/
│   ├── tiny-copy-fix.json
│   └── ...
└── claude-code/
    ├── tiny-copy-fix.json
    └── ...
```

5. Aggregate using that local path:

```bash
python scripts/benchmark_agent_outputs.py \
  ~/.vibe-coding/projects/<project-id>/benchmarks \
  --json
```

A missing run is reported as missing data, not as a failure or success. Keep raw outputs for reproducibility.
