# Improvement Roadmap

Canonical current status; closed specifications and historical verification live in the [roadmap archive](docs/archive/improvement-roadmap-through-1.4.0.md). Reviewed: 2026-10-07, Asia/Tehran.

## Current position

| State | Position |
|---|---|
| Published runtime | Stable `1.4.0`, release commit `9aa2c9db69ab14cb6530f7b1e84dd8effeb56ccb`. |
| Completed improvement work | Original nine packages + F1 shipped in `1.3.0`; R1-R4 shipped in `1.3.1`; three approved follow-ups shipped in `1.4.0`. |
| Current phase | Repository documentation cleanup: **Complete** — [PR #88](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/88); this status takes effect upon merge. |
| Scope | Shorter overview/status pages, archived closed plans, accurate security guidance and working documentation links. |
| Next action | Gather meaningful feedback from actual use. This documentation-only change does not require a new release or local installation. |
| Remaining feature work | No new implementation package is approved. Gather meaningful feedback from actual use. |

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

Improve actual software outcomes with proportionate checks. Receipts establish tested bindings/results; the Head still assesses relevance, semantic compatibility and evidence sufficiency. No model evaluation, fixed test quota or speculative new package is planned.
