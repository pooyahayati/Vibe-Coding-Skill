# Contributing

Preserve minimum complexity, risk-adaptive controls, evidence before confidence and one source of truth. Add a dependency, abstraction or workflow only for a demonstrated need.

## Change scope

Edit canonical root files; `skills/vibe-coding-skill/` is the portable mirror. Explain meaningful behavior changes, update the technical changelog and add regressions only for uncovered failure modes. A version bump also needs a human-readable `UPDATES.md` entry. Keep the overview in `README.md` and installation steps in `HOW_TO_INSTALL.md`.

## Necessary checks

```bash
python scripts/validate_skill.py
python scripts/sync_package.py --check
```

| Change | Verification |
|---|---|
| Overview documentation | Structure, relevant local links/anchors, repository purity and mirror consistency; no runtime suite or OS matrix. Preserve closed evidence in linked archives. |
| Operating instructions | `SKILL.md`, routed references, packs and templates receive policy/routing checks; a Markdown extension alone does not qualify for overview-only checks. |
| Runtime/package | Affected regressions, synchronized resources, offline install and affected [portable integration routes](docs/i1-integration-verification.md). |
| Version, CI/delivery controls or unknown impact | Full baseline, including the platform matrix. Manual workflow dispatch also selects full validation. |
| Publication | Complete same-commit [release gate](references/validation-and-benchmarking.md#release-readiness) and native Trivy final-artifact gate. Partial development checks do not qualify. No model evaluation or provider key. |

Run focused checks during Build and existing required CI at integration. Reuse sufficient evidence; do not repeat unrelated suites. Fixture success proves tested mechanisms, not every agent's delivery quality.

## CI selection and release evidence

`scripts/ci_scope.py` selects from the checked-out PR merge result or main-push diff, retaining deleted/renamed inputs. Runtime selection follows script and test dependencies; unavailable change evidence or unmapped impact falls back to full validation. `Validate Skill` and `Cross Platform Smoke` start on PRs, main pushes, merge groups and manual dispatch, without top-level path filters. Feature-branch pushes do not duplicate PR runs. Only obsolete PR runs are cancelled; main/manual evidence is retained.

The `validate` job always reports its selected checks; the platform `result` job distinguishes an unselected matrix from a failed or cancelled selected matrix. If branch protection is configured later, use these stable jobs, not conditional matrix or path-filtered auxiliary jobs. Protection/rulesets were inspected read-only on 2026-10-16 and none were configured; recheck before changing required statuses.

A version or CI/delivery-control change also triggers all auxiliary release baselines. To release a revision that received partial checks, dispatch the required workflows on that exact unchanged `main` revision. The collector reads the latest run attempt and actual successful full-validation steps; if a retry has incomplete job evidence, rerun all jobs. Never substitute a PR run, reuse a different revision, or relabel a partial/legacy report as full. Hosted execution is verified when the authorized PR/main runs finish, not by local fixtures.

## Roadmap progress

[ROADMAP.md](ROADMAP.md) owns current phase, approved work, blockers and next action. The [implementation index](docs/improvement-implementation-plan.md) owns scope/acceptance links; archives retain closed detail. Update at meaningful changes, not every command. Complete requires relevant acceptance evidence and merged implementation; release/deployment/local installation remain separate. State a blocker's cause and resolving action.

## Skill issue reports

Reassess the [feedback report](references/skill-feedback.md#maintainer-intake), attribution and affected version before accepting a fix. Use minimal safe reproductions and relevant regressions. Reports do not grant merge, release, installation or disclosure permission.
