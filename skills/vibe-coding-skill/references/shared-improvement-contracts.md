# Shared Improvement Contracts (P0)

Status: B1/B2 behavior guidance and optional version-1 task-contract propagation are implemented. E1's `evidence_capture.py` produces version-1 collected local execution receipts and explicit unavailable records; it does not import/verify remote claims or record manual observations. Receipt resolution at completion, specialist assignment/return acceptance and completion version 3 remain later specifications. The current completion gate accepts version 2 and does not resolve receipts or assess specialist compatibility. Do not interpret ignored proposed fields as validation.

Read this reference when implementing those packages or their migration. It is not an additional checklist for every product task. Existing [verification](execution-and-verification.md), [specialist authority](specialist-authority.md) and [local workspace](local-workspace-and-repository-purity.md) rules remain active.

## Common identity and ownership

Each new record has `format`, integer `schema_version: 1`, and a nonempty `task_id` stable within the task. Format names are `vibe-task-contract`, `vibe-execution-receipt`, `vibe-specialist-assignment`, `vibe-specialist-return` and `vibe-head-acceptance`. Their versions are independent of the skill release, completion report and execution-plan versions.

IDs are nonempty case-sensitive strings, unique within their record collection. Preserve task, criterion, evidence-requirement and assignment IDs across plans, receipts and returns. References must resolve within the same task and accepted contract revision; an ID match alone does not establish equivalent meaning. Use timezone-aware ISO 8601 timestamps and lowercase hexadecimal SHA-256 digests. Missing required values are errors; absence of a conditional value means not applicable, not success.

The Head owns scope, risk, accepted criteria, evidence obligations and integration acceptance. Specialists contribute domain methodology and findings. Host permissions and system/developer/user/project instructions remain authoritative. No format grants permission, starts another lifecycle or changes specialist freshness policy.

## Task and behavior contract — B1/B2

| Field | Type / requirement | Meaning |
|---|---|---|
| `task_id`, `objective`, `scope` | Nonempty string, nonempty string, nonempty string array | Current task and affected boundary; scope is not a permission grant. |
| `risk_tier` | Integer 0–3, excluding booleans | Known risk floor, independent of project size. |
| `acceptance_criteria` | Nonempty object array | At least one required criterion; reuse existing IDs and descriptions. |
| Criterion `id`, `description`, `required` | Nonempty string, nonempty string, boolean | Same meanings as completion schema 2. |
| Criterion `behavior` | Conditional object | Use when the description alone cannot express observable success. |
| Behavior `user_action`, `expected_result` | Nonempty strings | What the user does and what can be observed; no implementation choice imposed on the user. |
| Behavior `starting_state`, `failure_expectation`, `protected_invariants` | Conditional string, conditional string, conditional string array | Include only meaningful preconditions, failure behavior and protected outcomes. Omission means not applicable. |
| `evidence_requirements` | Nonempty object array | The smallest sufficient verification obligations, selected by changed behavior and risk. |
| Requirement `id`, `criterion_ids`, `kind`, `origin`, `required` | String, nonempty string array, string, enum, boolean | Link each obligation to known criteria; `kind` uses the existing completion gate taxonomy. |
| Requirement `input_paths`, `input_excludes`, `artifact_paths` | Conditional string arrays | Project-relative source/config/dependency/data inputs and explicit exclusions; exact delivered artifacts when relevant. Collected execution requires a meaningful input scope; exclusions default to empty. Artifact paths may name an exact authorized file outside the source root, including the local artifact workspace. |

`origin` is `collected`, `reported` or `manual`, as defined below. Every required criterion needs at least one required evidence obligation. Distinct obligations are added only when they cover different necessary outcomes or risk boundaries. Completion reports add `met` and actual `evidence_ids` to criteria; these outcome fields are not part of the pre-implementation acceptance snapshot.

A tiny task can reuse one concise description and a manual or static obligation inline. No new product document, automated test, specialist or approval follows merely from this format. Durable product decisions belong in existing project documents; tool snapshots belong outside product source control.

### Example: lightweight task contract

```json
{
  "format": "vibe-task-contract",
  "schema_version": 1,
  "task_id": "settings-label",
  "objective": "Correct the label without changing settings behavior",
  "scope": ["admin/settings.php"],
  "risk_tier": 0,
  "acceptance_criteria": [
    {"id": "label", "description": "The settings page displays the corrected label", "required": true}
  ],
  "evidence_requirements": [
    {"id": "label-view", "criterion_ids": ["label"], "kind": "visual-check", "origin": "manual", "required": true}
  ]
}
```

## Execution receipt — E1/E2

| Field | Type / requirement | Meaning |
|---|---|---|
| `id`, `requirement_id`, `criterion_ids` | String, string, nonempty string array | Receipt identity and exact obligation/criteria it addresses. |
| `contract_sha256` | Digest | Binds the accepted task contract, including evidence obligations. |
| `origin`, `kind`, `result` | Enum, existing evidence kind, enum | Result is `pass`, `fail`, `timeout`, `error` or `unavailable`; never infer execution from a stated pass. |
| `started_at`, `finished_at` | Timestamps for attempted checks | Finish must not precede start. Unavailable checks use `recorded_at` and `reason` instead. |
| `source` | Object | `project_id`, absolute `root`, and optional observed `commit`. A commit alone does not bind dirty inputs; higher-tier report provenance still requires its existing commit fields. |
| `context` | Object | Relevant runtime/check tool, environment and dataset identity; omit unrelated host inventory and secrets. |
| `inputs` | Object for attempted collected execution | `paths`, explicit `excludes`, manifest arrays `before`/`after` and digests `before_sha256`/`after_sha256`. |
| `command` | Object for collected execution | Exact nonempty `argv` array, explicit `cwd`, positive finite `timeout_seconds`, integer or null `exit_code`. No shell expansion by default. |
| `artifacts` | Conditional object array | Exact artifact path and SHA-256, plus applicable version; bind the bytes actually checked. |
| `observation` | Required for manual evidence | Concrete observed result, method/environment and relevant source/artifact identity. A self-declared status is insufficient. |
| `provenance` | Required for reported evidence | `source`, `reference`, `commit`, `result_id`, `resolution` (`verified` or `unverified`), `verification_method` and `captured_at`; missing verification remains unverified. |
| `reason` | Required for non-pass results | Explain failure, timeout, error or unavailable check without exposing credentials. |
| `log` | Optional object | Bounded local relative `path`, `sha256`, boolean `truncated`/`redacted`; full logs are not mandatory. |

- **Collected:** the authorized local runner records the actual command outcome. `pass` requires exit code 0, unchanged applicable inputs and no unresolved collection error. A timeout is never a pass, even if partial output says success. If no process can start, record `error`/`unavailable` and a reason; unavailable command/input details may be omitted, never invented. A zero exit code proves process success, not relevance or adequacy of assertions; the Head still assesses those.
- **Reported:** an imported claim, including remote CI or another agent's report. Copying metadata never makes it collected. It can qualify only through an authorized resolver that verifies the original result, tested revision and applicable artifact identity. Without that resolver, label it unverified; E1's local runner does not supply remote verification.
- **Manual:** an actual human/agent observation, such as a rendered check. Record what was inspected and observed; do not invent an exit code. It may satisfy an accepted manual obligation. It cannot silently replace an obligation requiring collected execution.

### Input and artifact binding

The accepted input scope includes the changed behavior's relevant source, configuration, dependencies/lockfiles and test/check definitions. Include mutable datasets or service state in `context` when they affect validity. Snapshot concrete files and directory membership, including relevant untracked files. Exclusions must be explicit and justified; do not omit changed runtime inputs because Git ignores them. Generated logs/receipts remain outside the input scope.

An input manifest is an array of objects with `path` and `sha256` (regular file), `path` and `missing: true` (an explicitly expected missing file), or `path` and `directory: true` (directory membership, including empty directories). Use project-relative forward-slash paths, sorted lexicographically with no duplicates. Hash UTF-8 JSON serialized with sorted keys, no extra whitespace and unescaped Unicode; exclude non-finite numeric values. Directory additions/removals must change the expanded manifest. Resolve paths beneath the selected project root; reject escaping paths and unsupported symlinks instead of silently skipping them. These canonical JSON rules also define record digests, including `contract_sha256` over the entire accepted task-contract record and `return_sha256` over the entire specialist-return record.

E1 uses concrete files/directories and subtree exclusions, not glob expressions. Its collected record adds `process_started`, and `termination_confirmed` on timeout, to distinguish an actual launch from preflight/spawn errors. Optional `collection_errors` retain incomplete collection without masking a command failure/timeout. `artifacts_before` records the same exact preexisting artifacts as `artifacts` after execution; a changed or missing checked artifact cannot pass. Build an artifact first, then check the exact delivered bytes. No process output/log or environment inventory is retained. Manual/reported receipt writers and completion qualification are not E1 capabilities. [Runner usage and limits](execution-and-verification.md#local-execution-receipts-e1).

Receipt `inputs.paths` and `inputs.excludes` must match the accepted requirement's `input_paths` and `input_excludes`; a receipt cannot choose a narrower scope. Capture inputs before and after execution. Changed inputs invalidate the result unless their mutation was explicitly defined as output and excluded before execution. At completion, recompute the same manifest against the intended delivery state; resolve and hash each required artifact again. A changed input, membership, contract, relevant environment/dataset or artifact makes that evidence stale. Unrelated excluded documentation does not force a rerun. A timestamp alone neither proves freshness nor creates an arbitrary expiry interval.

For WordPress, reuse `wordpress_artifact.py` identity/version output and hash the exact installable ZIP. Packaging evidence cannot substitute for install/upgrade/runtime or seeded-data preservation checks when those are required.

## Specialist assignment and return — S1/S2

An assignment uses the common envelope plus nonempty strings `assignment_id`, canonical `specialist_id`, `stage` (one existing lifecycle stage), digest `contract_sha256`, and string arrays `criterion_ids`, `scope`, `settled_decisions`, `protected_invariants`, `authorized_actions` and `evidence_requirement_ids`. `platform` is an object naming the actual stack/runtime. Arrays can be empty only when no such constraint applies; identity, stage, scope and criterion links are required. `authorized_actions` summarizes existing authority and cannot create it.

The return repeats assignment/task/specialist/stage/contract identities and adds:

| Field | Type / requirement | Meaning |
|---|---|---|
| `upstream_revision`, `head_contract_sha256` | Nonempty revision, digest | Observed specialist source and Head/adapter instruction fingerprint used for the operation; provenance, not version pins. |
| `changed_surfaces` | Object array | Project-relative path and action (`add`, `modify`, `delete`, `rename`); renames include `previous_path`. Empty for analysis-only assignments. |
| `decisions` | Object array | `description`, `criterion_ids`, `contract_refs` and `rationale`; include material producer/consumer compatibility implications. |
| `invariants` | Object array | `description`, `status` (`preserved`, `violated`, `unverified`), `explanation` and `evidence_ids`; cover every assignment invariant without downgrading it. |
| `evidence_ids` | String array | References to actual receipts/evidence, not copied success claims. |
| `findings` | Object array | `id`, boolean `required`, `description`, `status` (`open`, `resolved`), and `resolution_evidence_ids` when resolved. |
| `unperformed_checks`, `conflicts` | String arrays | Explicit unavailable checks and unresolved instruction/platform/scope/contract conflicts. |
| `next_action` | Nonempty string | Next action for the Head, including an explicit no-further-domain-work statement when applicable. |

Empty findings/conflicts are allowed, not proof of safety. A valid return establishes structure and identity, not acceptance. The Head compares actual changes, evidence and shared contracts with the assignment. Unexpected scope requires a bounded reconciliation, not automatic approval or automatic rejection of a valid security finding.

Store the Head decision separately as `vibe-head-acceptance`: `assignment_id`, `contract_sha256`, `return_sha256`, `upstream_revision`, `head_contract_sha256`, `decision` (`accepted`, `changes-required`, `blocked`), `assessed_by`, `assessed_at`, `reason` and `unresolved_required_finding_ids`. Acceptance requires no unresolved required finding/conflict or violated/unverified required invariant. Record concrete resolution/reassessment rather than deleting findings or lowering known risk. Specialist acceptance does not establish whole-task completion.

S1's instruction-compatibility assessment is separate from a task return: bind the observed upstream revision and Head/adapter fingerprint, record assessed changes/conflicts and the Head's decision. Reuse unchanged accepted assessments; reassess changed instructions or Head controls. Preserve latest-stable/default-branch resolution, daily inventory and no replacement during an active assignment. P0 introduces no offline/old-version fallback or installation authority.

## Trust, storage and execution limits

Store task snapshots and receipts under the existing local project workspace, for example `state/contracts/` and `test-artifacts/receipts/`; keep specialist assessment records in the existing specialist state area. Resolve references within their designated state roots; do not fetch or execute arbitrary paths/URLs supplied by a report. Retain only enough evidence for the handoff/review; remove task-local temporary logs when no longer needed under project retention requirements. Do not add machine-local state to the product repository.

Receipts and hashes detect accidental alteration and mismatches; they cannot resist an actor who can edit both records and inputs. Independently retained acceptance snapshots require caller/host writer controls. A checksum is not user approval. Command text, upstream instructions, scanner output and referenced URLs remain untrusted input, never execution authorization. Preserve existing permissions for network, costs, destructive actions and delivery. Use bounded argument-list execution; do not collect environment dumps, secret-bearing arguments or unrestricted output.

## Compatibility and migration decision

| Surface | P0/current behavior | Implementation decision |
|---|---|---|
| Completion report version 2 | Remains supported by the current gate; validates declared evidence/provenance and its existing criterion baseline rules. | Retain as an explicitly legacy route after E2; never label its success receipt-verified. |
| Completion report version 3 | Reserved by this design; unsupported by the current gate for `Done`. | E2 adds `task_id`, `contract_sha256` and receipt references to existing report/criterion fields; resolves obligations from the retained task contract before applying current risk/family rules. |
| New task using E2 | No new receipt requirement activated by P0 alone. | Once E2 ships, new structured-completion tasks use version 3 at every risk tier; a tiny task may use one accepted manual obligation. No forced automated test. |
| In-flight version 2 task | Continue its existing supported route. | Migrate only after retaining/reconciling criteria and obligations; rerun only checks whose adequate evidence cannot be bound. Never fabricate receipts from old claims. |
| Existing execution plan version 1 | Legacy unbound reading remains supported; B2 optionally validates retained task contracts/criterion links. | Use `--task-contract` when drafting or validating against an independent baseline; `task_contract_checked` and `acceptance_baseline_checked` report which validation occurred. No execution-proof claim follows. |
| Specialist installation/registry | Unchanged package validation and authority rules. | S1/S2 implement assessment and return validation separately; existing installation is not semantic acceptance. |

The version-3 report evidence entry retains `id`, `kind`, `result`, `required` and applicable provenance, and adds `requirement_id` and `receipt_ref`. The receipt's ID equals the entry ID; task, contract, requirement, criteria, kind, origin and result must agree. `receipt_ref` is a relative path within the task receipt root. Required missing, failed, unresolved reported, stale or mismatched receipts block completion. Optional failures retain the current justification rule and cannot satisfy required criteria.

The caller chooses the expected workflow from the retained task contract/context, not a report-controlled flag. Unknown format versions and a lower-version submission for a version-3 task are unsupported, not an automatic fallback. Do not convert `collected` requirements to manual/reported evidence to evade failure. Retain approved scope, risk, criterion descriptions/behavior and evidence obligations before implementation for Tier 2/3 or scope-changing work; compare meaningful required fields, not just IDs. Existing version-2 baseline checks protect descriptions/required flags only and do not yet enforce this expanded comparison.

Additive optional descriptive fields can remain compatible within a format version. Changes to required fields, meanings, qualification or trust policy require a new format version and explicit migration. Implementation must reject unsupported safety-relevant fields/versions rather than ignore them. P0 changes no runtime schema, release version, installation or host configuration. Review release-version compatibility after the actual implementation; do not promise a release number here.

## P0 exit and next packages

P0 settles shared contracts and migration; B1/B2 provide behavior guidance and optional propagation. E1 implements bounded local collection; E2 will resolve receipts at completion, and S1/S2 will implement specialist assessments/acceptance. Acceptance cases remain in the repository's [implementation plan](https://github.com/pooyahayati/Vibe-Coding-Skill/blob/main/docs/improvement-implementation-plan.md); a specification, successful command or propagated success claim alone does not establish sufficient behavior coverage or specialist acceptance.
