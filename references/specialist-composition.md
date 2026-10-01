# Specialist composition and freshness

## Ownership and authority

Vibe remains the project manager and senior engineering Head. It owns the current objective, boundaries, risk floor, architecture, dependencies, approvals, acceptance evidence, cross-domain integration, and final completion/release. It delegates domain methodology rather than copying it.

Authority: actual system/developer/user instructions and applicable project rules → Vibe engineering controls → selected specialist within its assigned domain → approved narrower specialist. This is a composition contract, not a way to override the host's instruction hierarchy.

Do not run competing design Heads. The only registered UI/UX specialist is **UI-UX-Skill**, from `https://github.com/pooyahayati/UI-UX-Skill`, package `skills/ui-ux-skill`. The previous dashboard specialist is not registered, selected, or a fallback. An old local installation is not authorization to invoke it under Vibe.

## Selection and actual use

`config/specialists.json` contains canonical sources, installable paths, triggers, requirement levels, and update policy. It contains no fixed versions, tags, or commits. `context_router.py` emits `required_specialists` without network access; legacy `optional_specialists` are advisory capability gaps, not registered installers.

UI/UX is required when the deliverable includes an affected user-facing interface: an app, website, dashboard, form, WordPress settings/admin surface, responsive layout, accessibility, directionality, or visual review. Task/path signals help route existing work; for new products or ambiguous wording, infer the UI requirement from the outcome and pass `--concern ui`. Do not infer UI solely from repository size or activate it for backend-only work. Recheck selection when the actual affected surface changes.

For each required specialist:

1. Obtain a current installation and read its `SKILL.md`; do not describe merely selecting/installing it as using it.
2. Pass objective, affected surfaces, settled stack/product constraints, risk floor, autonomy, approvals, and acceptance conditions.
3. Enter its Head-delegated mode. Let it classify the product and load its own required Product Packs and task-relevant references. Do not replicate product-specific design rules or reopen settled discovery.
4. Request decisions, changed surfaces/files, preserved constraints, actual rendered/functional/accessibility/localization evidence, unperformed checks, risks, and remaining approvals.
5. Vibe checks integration and acceptance, then owns the final software result. Specialist completion does not establish whole-project completion.

The upstream specialist controls its supported product routes and exclusions. Do not invent coverage beyond its current instructions. If a requested design falls outside its support, report the gap instead of silently activating the retired dashboard specialist. UI/UX delegation does not make the specialist responsible for unrelated graphic/media generation or backend behavior.

Use only the evidence needed for the change and its material failure modes. Head risk/scope controls govern test breadth; specialist recommendations must not force irrelevant suites, repeat settled discovery, or introduce unrequested approvals or model evaluations.

## Freshness and installation

From the installed Head, before beginning a new task:

```sh
python scripts/specialist_manager.py prepare --task "<task>" --path <affected-path> --concern ui --project-root <project> --apply --json
```

Omit UI facts for backend-only work. `--apply` is used within existing authorization to install/update approved registered packages; do not treat a command-line option as permission to exceed host permissions. Without it, missing/outdated installations block rather than being silently used.

The manager always checks the Head and each selected specialist upstream. At most once per successful daily interval, it also reconciles all registered specialists already installed on the host. Unselected missing skills are reported but not downloaded. A daily audit can also be invoked explicitly:

```sh
python scripts/specialist_manager.py inventory --apply --json
```

This entrypoint performs a due daily audit while tasks are active. It does not create an idle background service. If checks must run without active tasks, a host scheduler must invoke the inventory command; no background scheduling is implied by `SKILL.md`.

The normal source is the latest published stable release. Only a `404` for no stable release permits resolving the repository's declared default branch. Rate-limit, network, and permission errors must not become a development-branch fallback. Report the source channel accurately.

The resolver observes a commit for the current operation, verifies the package identity/resources, and compares normalized installed hashes. Observed commits in local provenance are evidence, not dependency pins. Unchanged verified source avoids a repeated archive download. Updates affect the next operation; never replace the instructions of a running delegated operation.

Install only the registered package and its resources, plus source version/license metadata. Do not execute upstream installers/scripts, copy repository-level policies into a product, or alter host hooks/configuration. Validate archives before extraction; stage outside the discovery directory, protect updates with a host lock, retain a previous-install backup, and roll back a failed replacement. A changed managed installation is `local-modifications`, not an overwrite candidate. An unmanaged installation can be adopted if it matches current source or replaced with a retained backup within existing authorization.

Default provenance lives under `~/.vibe-coding/specialists`; skills live in the host's skills directory. Both must stay outside product repositories and separate from each other. Never commit machine-local installation state into product source control. A lock left after a crashed process requires checking that no update is active before removing it.

### Outcomes

| Outcome | Required action |
|---|---|
| `PASS` / `current` | Read current instructions, then delegate within the settled boundary. |
| `RELOAD` | Head changed; read it and rerun its preflight using its current registry/manager. |
| `BLOCK` | Required Head/selected specialist is missing, outdated, incompatible, locally modified, or currency-unverified; resolve that cause before this workflow. |
| `WARN` | An unused registered installation failed inventory; report it and continue unaffected work. |

Do not silently label an older fallback latest. A deliberate exception to mandatory currency requires a real user decision. Never claim automatic updates are available where host execution/network permissions prevent them.

## Nested specialist requests

A specialist's links are dependency requests, not unrestricted installation authority. Propagate Head scope/risk/freshness controls to narrower specialists. Before using one, reconcile its canonical source with an explicitly approved registration or an already authorized skill in the host's trusted catalog; apply the same latest-source and scoped-handoff contract. Do not download an entire collection or blindly follow arbitrary transitive links. Report an unregistered, untrusted required dependency as a gap for the Head to resolve. Recommended dependencies must not block unrelated work.

Graphify and Trivy retain the existing graph/scanner tool adapters; they are not additional UI/UX Heads. No model/API evaluation is required by this composition contract.
