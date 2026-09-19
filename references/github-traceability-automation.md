# GitHub Traceability Automation

## Goal

Use GitHub as execution history without making the Vibe Coding Skill itself part of the user's repository.

Traceability model:

`Requirement -> Issue -> Acceptance Criteria -> PR -> Tests -> Release`

## Adapter

Status:

```bash
python scripts/github_traceability.py status --root . --json
```

Read-only snapshot:

```bash
python scripts/github_traceability.py snapshot --root . --json
```

The snapshot is stored locally under the Vibe workspace, not committed.

## Requirement mapping

Record links locally:

```bash
python scripts/github_traceability.py record REQ-014 \
  --issue 42 \
  --pr 57 \
  --test "pytest tests/billing" \
  --release v0.8.0 \
  --root . \
  --json
```

Verify GitHub objects and visible linkage:

```bash
python scripts/github_traceability.py verify --requirement-id REQ-014 --root . --json
```

The verifier checks that recorded Issues, PRs, and Releases exist. When both Issue and PR are recorded, it warns if the PR does not visibly reference the Issue.

## Safe mutation

Issue creation is dry-run by default:

```bash
python scripts/github_traceability.py create-issue \
  --title "[REQ-014] Add invoice export" \
  --body "Acceptance criteria..." \
  --root . \
  --json
```

Actual creation requires `--apply`. This prevents a planning pass from silently creating GitHub objects.

## Source of truth

GitHub objects are the execution source of truth when GitHub is used. The local traceability file is an index/cache used by the agent; it is not a replacement for the Issue, PR, test evidence, or Release itself.
