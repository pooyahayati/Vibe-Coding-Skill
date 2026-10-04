# Optional Maintainer Benchmarks

Normal skill use and release readiness require no model evaluation or provider API key. The active publication policy is the [release-readiness gate](../references/validation-and-benchmarking.md#release-readiness), implemented by [release_readiness.py](../scripts/release_readiness.py) and [release.yml](../.github/workflows/release.yml). Use the latest required workflow results on the exact target commit; optional benchmark evidence cannot substitute for missing software checks.

The former credentialed benchmark workflows and `.github/benchmark-trigger` route have been removed. Their historical Phase 9D benchmark prerequisite is obsolete; there is no automatic or mandatory real-agent campaign.

## Full-source maintainer boundary

The full repository retains optional research tools for separately requested maintainer evaluation. These are not installed-skill entrypoints and do not belong to ordinary project execution or release qualification:

| Purpose | Full-source resources |
|---|---|
| Collect scenario behavior from a real agent | [run_agent_benchmark.py](../scripts/run_agent_benchmark.py), [adapter metadata](../config/agent-benchmarks.json) |
| Aggregate existing behavior results | [benchmark_agent_outputs.py](../scripts/benchmark_agent_outputs.py) |
| Delivery fixture contract and optional real-agent collection | [run_delivery_benchmark.py](../scripts/run_delivery_benchmark.py), [delivery fixtures and grading contract](../evals/delivery/README.md) |
| Aggregate existing control/treatment delivery results | [benchmark_delivery_outputs.py](../scripts/benchmark_delivery_outputs.py) |

A real-agent run may consume provider usage and needs its own authorized CLI/authentication setup. Do not start one, install an agent, request credentials or infer permission from this guide. Consult the relevant full-source runner's command help only when that optional work has been explicitly requested. No runner or provider configuration is added to the portable package.

## Evidence limits

For optional conformance research, use the [scenario-output contract](../evals/AGENT_OUTPUT_SCHEMA.md). Keep expected policy and scorer output out of the evaluated prompt; score only after the response. Retain scenario/agent/source identity and available provenance outside product source. Missing or partial runs remain incomplete, never synthetic success.

Behavior scoring checks declared policy choices, not successful application execution. Delivery research compares the same agent's control and treatment fixtures with separate hidden graders; it is not a model leaderboard or a guarantee for arbitrary projects. Deterministic fixtures and injected self-tests prove tested tooling, not live-agent competence.

## Deterministic maintainer checks

These existing full-source commands validate the delivery framework without calling a model; they are not required for every change:

```bash
python scripts/run_delivery_benchmark.py validate --json
python scripts/run_delivery_benchmark.py self-test --json
```

Use affected fixtures and existing CI when the delivery framework changes. The installed package includes only the offline behavior scorer documented in the scenario-output guide; collection and aggregate runners remain maintainer-only.
