# I1: portable workflow integration

Historical verification snapshot: implementation verified on 2026-10-03 (Asia/Tehran), against main baseline `3676be55d0499f9a25ccba94732f6dc90fba2526`. I1 subsequently merged in PR #72, merge `512272202f9fc178dd6ec191e4a9f0d0f411b881`. D1 documentation and follow-up F1 merged in [PR #73](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/73); the completed cycle shipped in `1.3.0`. See [the roadmap](../ROADMAP.md) for current release and local-delivery status.

[Implementation PR #72](https://github.com/pooyahayati/Vibe-Coding-Skill/pull/72) records the I1 source revision, CI and merge evidence.

## What changed

`tests/test_portable_integration.py` builds the current source ZIP using the existing release builder, which runs the extracted package's offline installation check. It then extracts that exact ZIP and exercises actual runtime entrypoints from outside the maintainer repository. The existing cross-platform smoke matrix runs these routes on Linux, macOS and Windows. No new runtime module, specialist, host dependency or universal product-test mandate is added.

| Representative route | Package-level integration exercised | Meaningful failure checks |
|---|---|---|
| Light / legacy | Retained criterion → lightweight plan → schema-2 declared completion → external handoff → resumed task identity. | No forced execution plan or receipt workflow; a legacy claim never becomes receipt-verified evidence. |
| Bounded / receipt-backed | Actual failing/successful command on a literal `[id]` input → schema-3 gate → retained state → resume. | Failed checks, schema downgrade and changed tested inputs block; an unrelated document does not invalidate scoped evidence. |
| Cross-boundary specialist | Bound plan/criterion/assignment → retained specialist return → installed review CLI → separate Head decision → installed completion CLI. | Dropping a required assignment, omitting scope/shared-contract reconciliation, premature completion and stale accepted inputs block. |

The cross-boundary route reuses the existing specialist test fixture with explicit offline upstream responses. Runtime modules are preloaded exclusively from the extracted ZIP and their file origins are asserted before the fixture runs; review and completion use separate installed CLI processes. This tests deterministic instruction/return bindings and local execution, not live specialist freshness, autonomous agent competence or semantic sufficiency of arbitrary Head decisions.

## Verification and stop rule

- All three new representative routes passed locally on Windows/Python 3.13. After extending the cross-boundary route with plan-binding checks, that affected route alone was rerun and passed.
- Building the test ZIP also verified the existing portable mirror, required runtime resources and extracted offline installation. Optional tool warnings remain warnings; required failures fail the integration setup.
- Existing B2/E1/E2/S1/S2 and WordPress checks remain in the repository's validation workflows. No WordPress adapter was changed: existing exact-ZIP/runtime tests are reused, and these integration fixtures do not claim WordPress installation or upgrade behavior.
- At the original I1 verification, the source ZIP was a temporary integration candidate; its unchanged `VERSION` metadata did not make it a new published release or the already published 1.2.0 artifact.
- The I1 verification itself involved no model evaluation, API key, live tool installation, automatic old-version fallback, release or global skill installation. Test fixtures/state stayed outside product source and were cleaned up. Subsequent release/local installation is recorded separately in the roadmap.

Run the focused integration check:

```sh
python -m unittest discover -s tests -p "test_portable_integration.py" -v
```

Required CI remains unchanged apart from adding this package-level smoke to the existing OS matrix. Stop after the representative routes and existing required checks pass; do not repeat unchanged suites or invent a test-count/coverage target. This acceptance is integration/package evidence, not a claim that vibe-coding mistakes have been eliminated.
