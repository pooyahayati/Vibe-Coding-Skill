# Project Gate Integration

`scripts/project_gate.py` is the executable integration point for risk, project graph, security scan, Git state, and GitHub detection.

## Inspect only

```bash
python scripts/project_gate.py \
  --root . \
  --change "Change authentication from sessions to JWT" \
  --base main \
  --json
```

This classifies risk, inspects changed files, checks graph freshness, detects Trivy and GitHub state, and reports `PASS`, `WARN`, or `BLOCK`.

## Execute relevant tools

```bash
python scripts/project_gate.py \
  --root . \
  --change "Refactor payment authorization" \
  --base main \
  --execute \
  --json
```

For Tier 2+ work, `--execute` runs `graphify update .` and a Trivy filesystem scan when those tools are installed.

The gate fails closed when a significant change has an installed graph provider but the graph remains stale, or when the Trivy report contains secrets or critical vulnerabilities.

If Graphify or Trivy is unavailable, the gate warns and requires an explicit equivalent fallback rather than pretending the check happened.

GitHub is detected from the Git remote. The `gh` CLI is reported when present but is not required for core operation.
