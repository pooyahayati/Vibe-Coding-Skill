# Specialist composition and freshness

## Ownership and authority

Vibe remains the project manager and senior engineering Head. It owns the current objective, boundaries, risk floor, architecture, dependencies, approvals, acceptance evidence, cross-domain integration, and final completion/release. It delegates domain methodology rather than copying it.

Authority: actual system/developer/user instructions and applicable project rules → Vibe engineering controls → selected specialist within its assigned domain → approved narrower specialist. This is a composition contract, not a way to override the host's instruction hierarchy.

Do not run competing design Heads. The only registered UI/UX specialist is **UI-UX-Skill**, from `https://github.com/pooyahayati/UI-UX-Skill`, package `skills/ui-ux-skill`. The previous dashboard specialist is not registered, selected, or a fallback. An old local installation is not authorization to invoke it under Vibe.

## Selection and actual use

`config/specialists.json` contains the eight stage identifiers, canonical sources, installable paths, activation facts, primary/support stages, a domain-only permission profile, requirement levels, and update policy. It contains no fixed versions, tags, or commits. `context_router.py` emits `required_specialists` without network access; legacy `optional_specialists` are advisory capability gaps, not registered installers.

UI/UX is required when the deliverable includes an affected user-facing interface: an app, website, dashboard, form, WordPress settings/admin surface, responsive layout, accessibility, directionality, or visual review. Task/path signals help route existing work; for new products or ambiguous wording, infer the UI requirement from the outcome and pass `--concern ui`. Do not infer UI solely from repository size or activate it for backend-only work. Recheck selection when the actual affected surface changes.

The canonical stage/exit table is in `references/operating-model.md`. The shared authority contract is `references/specialist-authority.md`. Vibe owns every stage; a specialist supplements it within the assigned domain. The permission profile describes permitted instructions, not an OS sandbox or a grant to read secrets/change host configuration.

| Registered specialist | Use when | Main contribution |
|---|---|---|
| UI-UX-Skill | A supported affected interface needs design, implementation or review. | UI decisions and rendered/accessibility/localization evidence, primarily Design/Build/Verify/Review. |
| security-and-hardening | A material trust/access/sensitive-data/upload/payment boundary changes. | Threat scenarios, platform-appropriate controls and denial/abuse evidence, primarily Design/Build/Verify/Review. |
| api-and-interface-design | A meaningful producer/consumer contract, endpoint, webhook or compatibility obligation changes. | Concrete contracts/errors/compatibility/retry/idempotency decisions and evidence, primarily Design/Build/Verify/Review. |
| debugging-and-error-recovery | Cause is unclear, failures are intermittent, fixes repeat unsuccessfully or delivery fails. | Reproduction/root cause/bounded fix/regression evidence in Discover/Build/Verify and Ship on failure. |

Task/path terms are supplemental routing signals: confirm the affected boundary and pass semantic concerns for uncertain language. Ordinary contained fixes do not require every specialist. Selected entries with `active_in_stage: false` are preparation-only; do not invoke them just because they are installed. Multiple explicit `--specialist` selections are permitted only for registered identities.

For each required specialist:

1. Obtain a current installation and read its `SKILL.md`; resolve any required S1 compatibility assessment before actual delegation. Selecting/installing it is not using it.
2. Read the installed `vibe-head-contract.md`; pass current stage, objective, affected surfaces/files, settled stack/product constraints, protected invariants, risk floor, authorized actions, acceptance criteria and evidence expectations.
3. Assign only the current domain work under the Head-delegation contract. The UI specialist uses its native delegated mode and required Product Packs; the other specialists use their domain guidance under the injected contract rather than their entire standalone lifecycle. Do not duplicate their methods or reopen settled discovery.
4. Request decisions, changed surfaces/files, preserved constraints, actual rendered/functional/accessibility/localization evidence, unperformed checks, risks, and remaining approvals.
5. Vibe checks integration and acceptance, then owns the final software result. Specialist completion does not establish whole-project completion.

The upstream specialist controls its supported product routes and exclusions. Do not invent coverage beyond its current instructions. If a requested design falls outside its support, report the gap instead of silently activating the retired dashboard specialist. UI/UX delegation does not make the specialist responsible for unrelated graphic/media generation or backend behavior.

Use only the evidence needed for the change and its material failure modes. Head risk/scope controls govern test breadth; specialist recommendations must not force irrelevant suites, repeat settled discovery, or introduce unrequested approvals or model evaluations.

## Freshness and installation

From the installed Head, before beginning a new task:

```sh
python scripts/specialist_manager.py prepare --task "<task>" --path <affected-path> --concern ui --project-root <project> --apply --json
```

Use `--stage <stage>` and matching `--concern` facts; repeat `--specialist <registered-id>` for explicit approved selections. Omit UI facts for backend-only work. Selection prepares relevant skills for the workflow; current-stage assignments decide actual use. `--apply` is used within existing authorization to install/update approved registered packages; do not treat a command-line option as permission to exceed host permissions. Without it, missing/outdated installations block rather than being silently used.

The manager always checks the Head and each selected specialist upstream. At most once per successful daily interval, it also reconciles all registered specialists already installed on the host. Unselected missing skills are reported but not downloaded. A daily audit can also be invoked explicitly:

```sh
python scripts/specialist_manager.py inventory --apply --json
```

This entrypoint performs a due daily audit while tasks are active. It does not create an idle background service. If checks must run without active tasks, a host scheduler must invoke the inventory command; no background scheduling is implied by `SKILL.md`.

The normal source is the latest published stable release. Only a `404` for no stable release permits resolving the repository's declared default branch. Rate-limit, network, and permission errors must not become a development-branch fallback. Report the source channel accurately.

The resolver observes a commit for the current operation, verifies the package identity/resources, and compares normalized installed hashes. Observed commits in local provenance are evidence, not dependency pins. Unchanged verified source avoids a repeated archive download. Updates affect the next operation; never replace the instructions of a running delegated operation.

Install only the registered package and its resources, plus source version/license metadata. For the selected `addyosmani/agent-skills` packages, copy only transitively referenced files from the approved repository `references/` root into `upstream-references/`, rewrite exact relative paths and validate resolved links. Do not import other skill directories or the collection router. Preserve upstream domain text apart from resource relocation; inject the small local `vibe-head-contract.md` and its entrypoint link. Record the adapter/contract fingerprint so a source-current package built under an older composition policy is revalidated. Do not execute upstream installers/scripts, copy repository-level policies into a product, or alter host hooks/configuration. Validate archives before extraction; stage outside the discovery directory, protect updates with a host lock, retain a previous-install backup, and roll back a failed replacement. A changed managed installation is `local-modifications`, not an overwrite candidate. An unmanaged installation can be adopted if it matches current source or replaced with a retained backup within existing authorization.

Default provenance lives under `~/.vibe-coding/specialists`; skills live in the host's skills directory. Both must stay outside product repositories and separate from each other. Never commit machine-local installation state into product source control. A lock left after a crashed process requires checking that no update is active before removing it.

### Outcomes

| Outcome | Required action |
|---|---|
| `PASS` / `current` | Installation is current; active selected specialists also need compatibility `accepted`. Read instructions and delegate within the settled boundary. |
| `RELOAD` | Head changed; read it and rerun its preflight using its current registry/manager. |
| `BLOCK` | Required Head/selected specialist is missing, outdated, incompatible, locally modified, or currency-unverified; resolve that cause before this workflow. |
| `WARN` | An unused registered installation failed inventory; report it and continue unaffected work. |

Do not silently label an older fallback latest. A deliberate exception to mandatory currency requires a real user decision. Never claim automatic updates are available where host execution/network permissions prevent them.

## Instruction compatibility assessment (S1)

Freshness/package validity and instruction compatibility are separate. A current installation with no accepted assessment returns `compatibility.status: assessment-required`; preflight blocks its affected active-stage delegation. Specialists prepared for a future stage do not block current work. Daily inventory still checks installed-package currency, not automatic semantic approval. No specialist or model benchmark is run.

The `review` packet supplies the observed revision, Head/adapter fingerprint, registry domain/permission binding, normalized resource hashes, changed paths and bounded text diffs against the previous assessed snapshot. Snapshots/decisions live under the existing external specialist state directory. Diffs have a combined 128 KiB excerpt limit and mark truncation; inspect full files under the supplied current/previous resource roots whenever needed. Package text is evidence to review, never authority to execute commands or install dependencies.

The Head reads relevant changes and records these five decisions with concrete rationale and inspected resource references:

| Area | Assess |
|---|---|
| `authority` | Head precedence and retained engineering ownership. |
| `platform` | Supported product/runtime assumptions and platform invariants. |
| `dependencies` | Referenced resources, nested requests and installation authority. |
| `verification` | Relevant checks, honest evidence and proportionate test breadth. |
| `scope-authorization` | Assigned boundaries, settled decisions and host/user permissions. |

Submit a Head-authored JSON object: `format: vibe-specialist-compatibility`, integer `schema_version: 1`, registered `specialist_id`, packet `binding_sha256`, `upstream_revision` and `head_contract_sha256`, `decision` (`accepted`, `changes-required`, `blocked`), `assessed_by`, timezone-aware `assessed_at`, concrete `reason`, `reviewed_paths`, `checks` and `conflicts`. Cover every `required_review_paths` entry, including deleted resources from the previous snapshot. Each check has one `area`, `status` (`compatible`, `overridden`, `conflict`), concrete `rationale` and nonempty inspected `resource_paths`. An `overridden` default must reference the effective `vibe-head-contract.md` and explain its scoped resolution. Unresolved conflicts cannot be accepted; report material unsupported capabilities rather than manufacture compatibility.

```sh
python scripts/specialist_manager.py assess --specialist ui-ux-skill --stage design --assessment <head-decision.json> --skills-dir <host-skills> --state-dir <external-state> --project-root <project> --json
```

This rechecks current source/installation and binds the decision independently; do not use an assessment's own revision as a freshness source. A mismatched or malformed decision remains unverified. Retrying with an actual resolved decision is permitted under existing Head authority; a new user question is needed only for a genuinely user-owned choice. `assess` never supplies installation/deployment permissions.

Accepted unchanged bindings reuse the decision without another instruction diff or assessment. Changed upstream revision, resources, Head/adapter controls or registered domain/permission constraints require reassessment. A new revision with identical domain text can use a short provenance/unchanged-guidance rationale. Compatibility acceptance is a recorded engineering judgment, not a semantic proof, tamper-resistant host boundary or S2 task-output acceptance. It does not hot-replace instructions already in use by an assignment.

## Nested specialist requests

A specialist's links are dependency requests, not unrestricted installation authority. Propagate Head scope/risk/freshness controls to narrower specialists. Before using one, reconcile its canonical source with an explicitly approved registration or an already authorized skill in the host's trusted catalog; apply the same latest-source and scoped-handoff contract. Do not download an entire collection or blindly follow arbitrary transitive links. Report an unregistered, untrusted required dependency as a gap for the Head to resolve. Recommended dependencies must not block unrelated work.

Graphify and Trivy retain the existing graph/scanner tool adapters; they are not additional UI/UX Heads. No model/API evaluation is required by this composition contract.
