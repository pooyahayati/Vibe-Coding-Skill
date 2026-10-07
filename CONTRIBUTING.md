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
| Documentation | Accuracy, relevant links/anchors and mirror consistency; no wording-only tests. Preserve closed evidence in linked archives. |
| Runtime/package | Affected regressions, synchronized resources, offline install and affected [portable integration routes](docs/i1-integration-verification.md). |
| Publication | Existing same-commit [release gate](references/validation-and-benchmarking.md#release-readiness) and native Trivy gate. No model evaluation or provider key. |

Run focused checks during Build and existing required CI at integration. Reuse sufficient evidence; do not repeat unrelated suites. Fixture success proves tested mechanisms, not every agent's delivery quality.

## Roadmap progress

[ROADMAP.md](ROADMAP.md) owns current phase, approved work, blockers and next action. The [implementation index](docs/improvement-implementation-plan.md) owns scope/acceptance links; archives retain closed detail. Update at meaningful changes, not every command. Complete requires relevant acceptance evidence and merged implementation; release/deployment/local installation remain separate. State a blocker's cause and resolving action.

## Skill issue reports

Reassess the [feedback report](references/skill-feedback.md#maintainer-intake), attribution and affected version before accepting a fix. Use minimal safe reproductions and relevant regressions. Reports do not grant merge, release, installation or disclosure permission.
