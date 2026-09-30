# Independent 0.10.7 Review: Remediation and Verification

> Historical report: version 1.0.0 removes model-based release qualification at the owner's request. Its former benchmark requirements below are not current publication requirements. The WordPress CI fixture install/upgrade subsequently passed.

Review date: 2026-09-30. Base commit: `4d0f5a78b2a519ede28bd67ec27eeb6f41eb135a`.

This change addresses the 13 reproduced defects in the independent review of the unpublished 0.10.7 candidate. The reviewed skill was treated as the subject of the review, not as the authority for reviewing itself. Runtime instructions remain concise; detailed evidence and limitations stay in maintainer references and this report. The version remains 0.10.7; this change does not publish or qualify a Stable release.

## Finding-to-fix coverage

| Finding | Correction | Verification |
| --- | --- | --- |
| R01: arbitrary nonempty risk values suppress uncertainty | Canonical value sets and bounded aliases preserve unresolved dimensions; the reported Persian destructive phrase raises Tier 3. | Unsupported-value, alias, and exact Persian request regressions. |
| R02: planning loses structured risk | Planner API and CLI carry the same facts to routing. | An ambiguous task with destructive production facts still requires a Tier 3 plan. |
| R03: sibling platform/scope leakage | Shared project-area discovery recognizes manifests/custom containers and distinct WordPress plugins; pack detection uses the scoped file set. | Generic runtime, custom API/plugin siblings, and cross-plugin scope regressions; existing routing tests. |
| R04: an all-optional checklist can pass Done | At least one required outcome is mandatory. Optional independent acceptance-baseline input detects removed, rewritten, or downgraded required outcomes. | All-optional, approved-outcome downgrade, and malformed-baseline rejection tests. |
| R05: WordPress keywords masquerade as implementation | Execute registration/sanitization/rendering through a trusted PHP harness against the exact built ZIP. | Broken baseline fails, known-good behavior passes, comment-only feature fails, and unsafe output fails. |
| R06: contradictory envelopes qualify as evidence | Validate maintained schema types, identities, timestamps, hash formats, counts, source fixture/grader hashes, and catalog check IDs; recompute success. Runner-owned executor classification prevents an injected executor from self-declaring real execution. | Mutation tests for contradictory exit/timeout/failure/check states, missing identity, malformed hashes/timestamps/counts, source identity mismatch, and executor spoofing. |
| R07: equal zero-success arms pass Stable | Catalog declares essential scenarios and a treatment success floor before the campaign; release gate recomputes rates/effects and verifies counts and model/CLI identities. | Zero-success neutral results, inconsistent rates, missing models, and existing Stable gate regressions. |
| R08: real adapters cannot perform their advertised workflow | Fix Codex global option placement. Claude permits local shell checks through a fail-closed sandbox with parser/version/isolation preflight. Campaigns require explicit CLI/model pins. | Command contract tests; actual local Codex CLI 0.159.2 parser-only preflight passed without model execution. Live Claude execution remains unverified. |
| R09: dependency evidence belongs to a different release | PyPI reads selected-version metadata; crates.io uses selected-version license evidence. Latest maintenance and project repository metadata are labeled separately. | Older selected versions with a different license/source return selected metadata. |
| R10: fresh-install evidence lacks preconditions | Record initial plugin state; distinguish plugin absence from clean-data evidence and leave full freshness unverified. | Initial plugin absent/present cases and existing upgrade lifecycle tests. |
| R11: Unix stubs fall through to host tools on Windows | Python-based test CLIs have Windows launchers and isolated PATH; smoke CI exercises them on every supported OS. | Fake GitHub and Graphify contract tests passed on Windows and Linux without network or live host calls. |
| R12: Agent commits hide product changes | Capture paths against the immutable initial commit; include both rename sides and hash canonical before/after contents. | A forbidden rename followed by an Agent commit remains visible and retains the same diff hash. |
| R13: latest-first CI blocks supported fallback | Tool-contract CI delegates candidate selection and fallback to the shared resolver. | Existing resolver candidate-failure/fallback tests; workflow diff confirms removal of preceding fail-fast latest calls. Live compatibility is checked by PR CI. |

## Verification performed

- Windows: `python -m unittest discover -s tests -p "test_*.py"`: 198 discovered; 195 passed and 3 skipped. The skips were two PHP execution tests (PHP absent on the host) and one symlink test (host capability unavailable).
- Linux: the same 198 tests all passed in an offline test container with Python 3.11 and PHP installed. The repository mount was read-only; `/tmp` was ephemeral and executable so test CLI shims could run. No host software was installed.
- Structure and evaluation catalog validation passed, including 16 behavior scenarios.
- Risk evaluations, representative-project validations, and failure-injection checks passed.
- Root/portable offline install checks, portable synchronization, and repository purity passed.
- Delivery catalog validation and deterministic framework self-test passed.
- Syntax compilation passed for 42 maintainer scripts/hidden graders; `git diff --check` passed.
- Added LF checkout rules for delivery fixtures after Linux verification exposed an operating-system-dependent fixture hash. Fixture contents are unchanged.

Portable runtime scripts and references are synchronized with their maintainer sources. New tests target distinct observed failure modes; they are not a requirement for every project using the skill. Existing guidance still stops verification once required outcomes and relevant risks have adequate evidence, without a fixed test-count or coverage target.

## Remaining qualification requirements

These fixes remove reproduced bypasses; they do not prove zero failure for inexperienced users or arbitrary projects.

1. Run both real-agent campaigns on the candidate commit with configured provider credentials and explicit CLI/model versions. No paid/credentialed model benchmark was run during this remediation. Parser and framework tests cannot substitute for it.
2. Verify Claude's sandbox on the chosen Linux/macOS/WSL2 runner. Unsupported parser or isolation capabilities block execution; there is no unsandboxed fallback. Native Windows remains unsupported for that adapter.
3. For a real plugin release, test the exact artifact in a known-clean WordPress fixture and use seeded project data for upgrade preservation. The PHP benchmark harness is bounded behavior evidence, not full platform integration.
4. Retain approved acceptance criteria independently when using the baseline gate. A baseline writable by the implementing Agent is not authenticated approval evidence.
5. Obtain real release evidence from trusted CI run/artifact identities. Envelope validation detects contradictions and stale scenario identities; arbitrary JSON is still not cryptographically authenticated evidence.

PR CI status and the final branch/commit are reported in the GitHub pull request, rather than embedded here as a permanently current assertion. Merge and release remain separate owner decisions.
