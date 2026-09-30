# Real Delivery Benchmark Contract

Phase 9A defines the benchmark contract only. Representative product scenarios are added in Phase 9B and real Codex/Claude execution adapters in Phase 9C.

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

## Phase boundaries

Phase 9A contains no provider credentials and no real-agent delivery result. The deterministic self-test exercises the contract with a fake executor.

Phase 9B adds representative fixtures and hidden graders.

Phase 9C adds real Codex/Claude workspace-write adapters plus enforceable OS/network sandbox behavior and credentialed repetitions.

Phase 9D analyzes failures and converts Skill defects into deterministic regressions where possible.
