# Improvement Roadmap

Canonical current status; closed specifications and historical verification live in the [roadmap archive](docs/archive/improvement-roadmap-through-1.4.0.md). Reviewed: 2026-10-07, Asia/Tehran.

## Current position

| State | Position |
|---|---|
| Published runtime | Stable `1.4.0`, release commit `9aa2c9db69ab14cb6530f7b1e84dd8effeb56ccb`. |
| Completed improvement work | Original nine packages + F1 shipped in `1.3.0`; R1-R4 shipped in `1.3.1`; three approved follow-ups shipped in `1.4.0`. |
| Current phase | Deep-audit remediation: planning prepared; implementation **Not started**. Repository documentation cleanup was merged in [PR #88](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/88). |
| Scope | Seven confirmed audit findings, grouped into five bounded packages below. This change prepares the plan only. |
| Next action | Start **A1: Retained-state and contract continuity**, using its [implementation sequence and acceptance criteria](docs/improvement-implementation-plan.md#a1-retained-state-and-contract-continuity). |
| Remaining work | **0/5 packages complete; 7/7 findings open.** Package status is maintained only in this roadmap. |

## Deep-audit remediation cycle A1-A5

Audit baseline: `a6e43fe73500367e52a257e0f9f725166d9c79dc` on 2026-10-07. The existing suite reported 287 tests, zero failures and three skips; structure validation and 16 deterministic scenarios passed. All 79 published runtime files matched the current portable mirror and local installation. These results establish the baseline, not acceptance of the corrections below.

Finding IDs **F1-F7** refer to the latest deep audit; they are separate from the historical **F1 feedback package** shipped in 1.3.0. Reproduction evidence, affected components and verification methods are retained in the [active implementation plan](docs/improvement-implementation-plan.md#confirmed-audit-findings).

| Order | Package | Intended correction | Audit findings / severity | Status |
|---|---|---|---|---|
| 1 | [A1: Retained-state and contract continuity](docs/improvement-implementation-plan.md#a1-retained-state-and-contract-continuity) | Preserve obligations through remote changes, recovery and authorized contract revisions; reconcile specialist assignments without losing findings. | F1, F2 / High | **Not started** |
| 2 | [A2: Reliable routing and graph inputs](docs/improvement-implementation-plan.md#a2-reliable-routing-and-graph-inputs) | Preserve literal hidden paths and governing instructions; bind graph freshness to the source actually analyzed. | F3 / High; F4 / Medium | **Not started** |
| 3 | [A3: Version-bound dependency decisions](docs/improvement-implementation-plan.md#a3-version-bound-dependency-decisions) | Use selected-version metadata and apply compound license policy without false acceptance. | F5 / Medium | **Not started** |
| 4 | [A4: WordPress command output integrity](docs/improvement-implementation-plan.md#a4-wordpress-command-output-integrity) | Parse complete structured stdout separately from diagnostic output. | F6 / Medium | **Not started** |
| 5 | [A5: Stage-aware integration controls](docs/improvement-implementation-plan.md#a5-stage-aware-integration-controls) | Align development health checks with the native publication gate and conditional graph requirements. | F7 / Medium | **Not started** |

Default execution order is A1 -> A2 -> A3 -> A4 -> A5, with focused review at each package. A1 establishes the state/migration decisions first. A2-A5 have no mutual implementation dependency; keep one active package unless a different order is explicitly selected. If A1 changes workspace identity, verify A2's graph storage against that accepted identity.

### Start and completion boundaries

- At package start, mark that row **In progress**, record the working branch/PR when available, and make its next action the single current objective. Reconfirm the affected reproduction against the current source before editing.
- A package becomes **Complete** only after its acceptance criteria pass and its implementation is merged. Record the PR/commit and relevant checks in its status cell; do not infer completion from test counts or a drafted fix.
- Keep unresolved findings visible. For a partial package, name the remaining finding/criterion; for a block, record the cause and resolving action. Update the open-finding count only when the linked criteria are satisfied and merged.
- Runtime changes must update canonical resources and the portable mirror together. Reuse relevant evidence and run affected regressions/integration plus existing required CI; no fixed test quota, model evaluation, new scanner or unrelated suite reruns.
- Preserve lightweight/manual and supported legacy routes, Head authority, required findings, scope-bound evidence and native Trivy before publication. Never regain a passing result by dropping obligations or weakening a gate.
- Release version, publication and local installation are separate delivery decisions after implementation. This planning change makes no runtime, release or installation claim.

The pre-existing-tag/partial-release retry concern remains **needs verification**, outside these seven confirmed findings and five packages. Live external-tool compatibility and full WordPress environment execution were not re-established by the local audit; temporary fixtures are not substitutes for that evidence. Do not expand the cycle on an unconfirmed concern.

## Approved delivery follow-ups — 1.4.0

| Work | Status / evidence |
|---|---|
| Native Trivy publication gate | Complete; PR #83 merged through [PR #85](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/85). Native scan/target-binding checks passed. |
| Document/runtime and excluded-domain routing | Complete; PR #84 merged through PR #85. Affected routing and portable checks passed. |
| Product installation / local Docker Compose | Complete; PR #85. Instructions/package integration verified; this is not execution of a separate product. |

## 1.4.0 delivery evidence

| Delivery | Verified snapshot |
|---|---|
| Release | [Stable v1.4.0](https://github.com/pooyahayati/Vibe-Coding-Skill/releases/tag/v1.4.0), published 2026-10-04, 13:35:08 UTC; source commit above. |
| Required checks | All six baseline workflows passed on that commit: [release-commit checks](https://github.com/pooyahayati/Vibe-Coding-Skill/commit/9aa2c9db69ab14cb6530f7b1e84dd8effeb56ccb/checks). Final portable package also passed the actual native Trivy gate. |
| Published ZIP | 79 files, 232,619 bytes; SHA-256 `1fca6cfe376685bc5a605664ada57067c06d7c9ea446c98f3c8fa11efe212387`. Downloaded archive, official checksum and validated candidate matched. |
| Local host, 2026-10-04 | `C:\Users\Pooya\.codex\skills\vibe-coding-skill`: `1.4.0`, all 79 release files matched; installation PASS with zero failures/warnings. Native Trivy `0.75.0` was available. This is a historical host snapshot, not automatic updates to every user or loaded agent. |

Roadmap/README-only changes do not change the released runtime. The [banner delivery](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/87) merged separately. Source completion, merge, publication and installation are separate claims.

## Completed audit packages

| Package | Correction | Delivery |
|---|---|---|
| <a id="r1-retained-contract-and-required-completion-controls"></a>R1 | New structured tasks use receipts; required specialist commitments survive handoff/completion. | [PR #77](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/77), `1.3.1`. |
| <a id="r2-bounded-discovery-without-silent-platform-loss"></a>R2 | Bounded discovery preserves large-file platform evidence and exposes incomplete inspection. | [PR #78](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/78), `1.3.1`. |
| <a id="r3-consistent-project-root-ownership"></a>R3 | Project-root ownership/containment and drift checks agree. | [PR #79](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/79), `1.3.1`. |
| <a id="r4-one-accurate-operational-validation-path"></a>R4 | Release/portable guidance matches actual tooling; obsolete benchmark mandates removed. | [PR #80](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/80), `1.3.1`. |

Specifications, reproductions, acceptance criteria and prior delivery hashes remain in the [closed roadmap](docs/archive/improvement-roadmap-through-1.4.0.md#package-specifications) and [original implementation plan](docs/archive/improvement-plan-through-1.4.0.md). Current runtime contracts remain in the [implementation index](docs/improvement-implementation-plan.md).

## How progress stays current

- Update this file when approved work starts, a blocker changes, implementation is merged or delivery is verified; it is not an automatic monitor.
- Use **Not started**, **In progress**, **Blocked**, **Complete**. Complete requires relevant acceptance evidence and merged implementation; show release/installation separately.
- Keep one current phase and next action consistent with the tracker. State the cause and resolving action for blockers; counts are not quality scores.
- Keep future scope/dependencies/acceptance in the implementation index; archive closed detail instead of appending a diary. [Contributor rule](CONTRIBUTING.md#roadmap-progress).

Improve actual software outcomes with proportionate checks. Receipts establish tested bindings/results; the Head still assesses relevance, semantic compatibility and evidence sufficiency. The active cycle is limited to A1-A5; no model evaluation, fixed test quota or speculative feature is planned.
