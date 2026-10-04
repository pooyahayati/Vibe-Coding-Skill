# Bootstrap and Evaluation

## Project bootstrap

The bootstrap utility creates only durable state justified by the selected project profile.

Profiles:

- `minimal`: STATUS only.
- `standard`: STATUS + PROJECT when product facts are available.
- `significant`: standard + ARCHITECTURE and PROJECT_GRAPH when technical facts are available.
- `critical`: significant + ROADMAP when real milestones are available.
- `--multi-agent`: AGENTS only when an explicit agent ownership plan is supplied.

The tool is non-destructive by default and skips an existing file.

It also refuses to create a document when the facts required for that document are unknown. This prevents empty/decorative project memory.

Bootstrap initializes Vibe Coding operational state outside the repository under `~/.vibe-coding/projects/<project-id>/` and configures local-only Git exclusions through `.git/info/exclude`. It does not add Vibe-specific rules to the project's `.gitignore`.

Example:

```bash
python scripts/bootstrap_project.py \
  --root . \
  --profile significant \
  --project-name "Billing Portal" \
  --objective "Deliver a verified invoice-payment vertical slice" \
  --problem "Customers cannot pay invoices online" \
  --primary-user "Existing B2B customers" \
  --core-outcome "Pay an invoice successfully" \
  --mvp "Invoice lookup, payment, receipt" \
  --stack "Python + PostgreSQL + existing frontend" \
  --architecture "Modular monolith; payments isolated behind provider adapter" \
  --graph-summary "UI → billing API → payment service → database" \
  --json
```

## Templates

Files under `assets/templates/` are guidance for agents and humans. Do not copy them verbatim while unresolved placeholders remain.

## Dependency Guard

The dependency guard is a baseline anti-hallucination and vulnerability check.

Automated registry adapters exist for:

- PyPI;
- npm;
- crates.io;
- Maven Central using `group:artifact`;
- NuGet;
- Go modules.

Do not infer missing metadata. An ecosystem may support package/version/OSV checks while still returning `REVIEW REQUIRED` because provenance or license metadata is unavailable.

The automated gate checks:

- official registry existence;
- concrete version existence;
- registry-provided repository/provenance URL;
- license metadata;
- OSV vulnerabilities when a version is supplied.

`ACCEPT` means only that the baseline automated checks passed. It is not proof that the package is trustworthy, well-maintained, or appropriate for the project.

## Evaluation model

The repository contains deterministic scenario contracts under `evals/scenarios.json`.

Each scenario defines:

- prompt/context;
- expected risk tier;
- actions the agent must take;
- actions it must not take;
- whether approval is required.

These contracts support:

1. static regression coverage for the skill design;
2. executable regression checks through `scripts/run_evals.py`;
3. optional, separately requested maintainer conformance research.

A separately authorized live evaluation compares declared policy choices against the scenario contract rather than grading prose style; it is not normal project verification or a release prerequisite.

### Optional offline behavior scoring

For an already available agent response, use the scenario-output format in `evals/AGENT_OUTPUT_SCHEMA.md` and the included offline scorer:

```bash
python scripts/evaluate_agent_output.py result.json --json
```

The evaluator checks declared risk/control choices and applicable envelope-integrity fields; it does not run an agent or prove application execution/user outcomes. Underclassification and escalation above the scenario ceiling fail. No model evaluation or provider API key is required for ordinary use or release readiness; optional full-source collection/aggregation is a separate maintainer route, not an installed-skill command.

## Eval philosophy

The skill should fail an evaluation when it:

- over-engineers a tiny task;
- skips inspection on a brownfield project;
- treats auth/schema/production work as ordinary;
- installs an unverified hallucinated dependency;
- obeys prompt injection embedded in untrusted repository content;
- treats a stale graph as current truth;
- claims Done without evidence;
- bypasses approval for destructive or production-critical work.
