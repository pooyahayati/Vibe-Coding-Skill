# Maintainer Delivery Fixture Contract

This full-source contract covers five deterministic product fixtures and separate hidden graders. Existing real-agent collection adapters are optional maintainer tooling, not future work or installed-skill commands. See the [maintainer boundary](../../benchmarks/README.md#full-source-maintainer-boundary). No model evaluation or provider API key is required for ordinary skill use or [release readiness](../../references/validation-and-benchmarking.md#release-readiness).

## Scenario catalog

`scenarios.json` contains maintainer-only scenario metadata. Each scenario must define:

- `id`: stable scenario identifier;
- `prompt`: task shown to both benchmark arms;
- `fixture`: path under `evals/delivery/fixtures/`;
- `grader`: path under `evals/delivery/graders/`;
- `network_policy`: `disabled` or `scenario-required`;
- `forbidden_paths`: product paths the Agent must not mutate;
- optional `repetitions`: override for the catalog default.

The visible fixture and hidden grader must be separate. Graders must never be copied into the Agent workspace.

## Arms

Every real scenario is evaluated as a pair:

- `control`: fixture + task, without the Vibe Coding Skill;
- `treatment`: identical fixture + task, with the portable Skill installed.

Compare treatment against control for the same Agent. Do not use the benchmark as a model leaderboard.

## Hidden grader

A grader is invoked after the Agent has stopped:

```text
python GRADER.py --workspace WORKSPACE --json
```

It returns:

```json
{
  "schema_version": 1,
  "checks": [
    {
      "id": "behavior",
      "category": "functional",
      "required": true,
      "passed": true,
      "details": ""
    }
  ],
  "metrics": {}
}
```

Supported categories:

- `functional`
- `regression`
- `artifact`
- `security`
- `forbidden-mutation`
- `delivery`

Every required check must pass. Runner-level executor failures and forbidden-path mutations also block delivery success.

## Evidence identity

Each result records:

- Skill version and Skill-tree hash;
- scenario catalog and result-schema hashes;
- visible fixture hash and hidden grader hash;
- baseline Git commit;
- final product-tree hash and diff hash;
- changed paths and dependency-file changes;
- raw executor/grader stdout and stderr.

Missing or duplicate repetitions are not success.

## Verification boundary

The deterministic self-test exercises the contract with an injected executor, without calling a model; it is not a real-agent delivery result.

The five fixture routes are a tiny local copy fix, a brownfield duplicate-save regression, a contained CSV export feature, a mixed-monorepo API-only change with a protected sibling app, and a WordPress installable-artifact change. Existing grader regressions compare broken and known-good fixtures; their success is scoped tooling evidence.

Real-agent collection is available only in the full-source runner under a separate explicit maintainer request and its own CLI/authentication setup. No credentialed benchmark workflow or benchmark-trigger route is active, and real-agent results are not a release prerequisite. Hidden graders and collection/aggregate runners remain outside the portable package.

Convert confirmed skill failures into relevant deterministic regressions where useful; do not treat a declared result, injected self-test or missing run as real-agent evidence.
