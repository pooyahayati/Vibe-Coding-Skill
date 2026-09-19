# GitHub Traceability Automation

## Goal

Use GitHub as execution history without making the Vibe Coding Skill itself part of the user's repository.

Traceability model:

`Requirement -> Issue -> Acceptance Criteria -> PR -> Tests -> Release`

Milestones group delivery outcomes. GitHub Projects may be used for workflow status when the user/project already uses them.

## Adapter

Status:

```bash
python scripts/github_traceability.py status --root . --json
```

Read-only snapshot:

```bash
python scripts/github_traceability.py snapshot --root . --json
```

The snapshot is stored locally under the Vibe workspace, not committed. It includes Issues, PRs, Releases, Milestones, and—when the authenticated `gh` scope permits—GitHub Projects.

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

Milestone creation is also dry-run by default:

```bash
python scripts/github_traceability.py create-milestone \
  --title "v0.8.0 Public Beta" \
  --description "Real-agent and real-world validation" \
  --root . \
  --json
```

Add an Issue/PR URL to an existing GitHub Project with a dry-run plan:

```bash
python scripts/github_traceability.py add-to-project \
  --project-number 1 \
  --url https://github.com/OWNER/REPO/issues/42 \
  --root . \
  --json
```

Actual mutation requires `--apply`. This prevents a planning pass from silently creating or moving GitHub objects.

GitHub Project operations depend on the authenticated `gh` scopes and account/project availability. Treat an unavailable Project API as a traceability warning, not as permission to invent state.

## Source of truth

GitHub objects are the execution source of truth when GitHub is used. The local traceability file is an index/cache used by the agent; it is not a replacement for the Issue, PR, test evidence, Milestone, Project, or Release itself.
