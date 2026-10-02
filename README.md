# Vibe Coding Skill

A risk-adaptive engineering Head for reliable AI-assisted development of small, medium and large software projects, including WordPress plugins. Works with OpenAI Codex, Claude Code and compatible skill-based agents.

Current version: `1.2.0`, the [latest published release](https://github.com/pooyahayati/Vibe-Coding-Skill/releases/tag/v1.2.0). It includes retained behavior contracts, local execution receipts and separate Head acceptance of specialist work. Subsequent source changes are listed under [Unreleased](CHANGELOG.md#unreleased); the release ZIP and an existing local installation do not acquire them automatically.

## One engineering Head, focused specialists

Vibe is the project manager and senior engineer. It owns scope, stack, architecture, risk, approvals, test selection, integration and final delivery. Specialists own their assigned domain methods, keeping the Head concise and drawing on maintained expertise.

**Ownership key:** **Head** = Vibe owns the work; **Both** = Vibe coordinates/accepts and the selected specialist owns domain work; **Supporting** = optional evidence or advice inside the Head's boundary. Every stage remains Head-controlled. Specialist participation is conditional, never a second project lifecycle.

## Development workflow

| Stage | What happens | Who does it | When it applies |
|---|---|---|---|
| **1 · Discover** | Inspect the project, rules, affected boundaries and risk; select relevant capabilities. | **Head**; **Supporting:** debugging for unclear failures, UI for a necessary interface assessment, Graphify for consequential impact. | Start of a new objective or when impact/scope evidence changes. |
| **2 · Define** | State the user outcome, scope, protected behavior and observable acceptance criteria. | **Head**; **Supporting:** UI user flows, security assets/trust boundaries, API consumer obligations. | Requirements or material constraints are not yet clear; reuse settled decisions. |
| **3 · Plan** | Choose the simplest adequate approach, ownership, sequence, dependencies and verification. | **Head**; **Supporting:** relevant specialist prerequisites and impact evidence. | Write a plan for high-risk/cross-boundary work; keep local low-risk work brief. |
| **4 · Design** | Make implementable UI, interface-contract and security decisions; reconcile their boundaries. | **Both:** UI/API/security specialists own applicable domain detail; Head owns architecture and integration. | A changed interface or trust boundary needs design; reuse adequate existing designs. |
| **5 · Build** | Implement and integrate small runnable slices within existing conventions. | **Head** implementation; **Both** for assigned specialist surfaces; debugging supports unclear failures. | The task is ready and necessary domain decisions are settled. |
| **6 · Verify** | Prove acceptance behavior and relevant failure modes with the cheapest sufficient evidence. | **Head** selects checks; **Both** for UI/API/security/debugging evidence; Trivy is a supporting scanner. | After changed behavior; use affected checks and reuse sufficient evidence. |
| **7 · Review** | Assess the actual diff, quality, scope, compatibility, findings and evidence sufficiency. | **Head** owns readiness; **Supporting:** applicable specialist domain review. | Before meaningful integration/merge; do not restart specialist workflows or repeat unrelated tests. |
| **8 · Ship** | Deliver the authorized artifact/release/deployment and verify its actual state. | **Head**; **Supporting:** retained domain evidence, relevant artifact scans, debugging on delivery failure. | Delivery is requested/authorized and required gates pass; local handoff can be the delivery. |

These are eight responsibilities, not eight mandatory documents, meetings or approval questions. Small tasks combine stages; medium/large work iterates vertical slices. A failed check returns to the affected decision, not the beginning of the whole project. Post-delivery incidents and feedback become new bounded objectives.

## Project size and risk tiers

The Head chooses a project route from complexity, then scales each task by its risk and affected scope. Project size is not a risk tier: a small plugin can contain a critical payment change, while a copy correction in a large application can remain tiny.

### Project routes

| Project size | Typical shape | How the Head guides delivery |
|---|---|---|
| **Small** | A focused outcome with few components, such as a simple site, utility or narrowly scoped plugin. | Use the simplest adequate stack, work directly in small runnable steps and check the changed behavior. Keep planning brief unless risk or cross-boundary impact requires more. |
| **Medium** | Several features, modules or integrations, such as a business app or plugin with external services. | Define module boundaries and deliver vertical slices; decompose when it improves ownership or verification. Check affected contracts, integrations and regressions. |
| **Large** | Multiple domains, teams, services or operational/data boundaries. | Decompose before implementation, confirm ownership and contracts, map consequential impact and integrate verifiable slices. Keep a local low-risk task lightweight. |

WordPress plugins use the same routes plus platform-specific authorization, public APIs, compatibility, data-preservation and installable-package checks. Size alone does not dictate a language, framework, specialist or test count. [Detailed operating model](references/operating-model.md).

### Task risk tiers

| Tier | When it applies | Required depth and verification |
|---|---|---|
| **0 · Tiny** | A small, local, reversible change with no security, data or architecture effect. | Understand → change → focused check. A documentation check or rendered inspection may be sufficient; add automated tests only when they provide needed evidence. |
| **1 · Standard** | A normal feature with bounded module impact. | Objective → acceptance → impact → implement → test → review. Use checks relevant to changed behavior and protected behavior. |
| **2 · Significant** | Auth, schema/migrations, multiple modules, external integrations, public contracts, meaningful dependencies or production-affecting configuration. | Explicit specification, impact analysis, implementation plan, stronger relevant tests and security/regression checks; independent review where possible. |
| **3 · Critical** | Destructive or irreversible operations, material production impact, sensitive data, IAM/secrets or safety-critical behavior. | Required approval within existing authorization, recovery/rollback planning and strong evidence; human review when available. Stop when critical verification is missing. |

Risk and affected scope determine the necessary checks; there are no fixed test counts or mandatory full-suite reruns for every change. Existing required project checks still apply. [Risk and autonomy rules](references/risk-and-autonomy.md).

## Registered specialists

| Specialist | Purpose and trigger | Main stages |
|---|---|---|
| [UI-UX-Skill](https://github.com/pooyahayati/UI-UX-Skill) | The **sole design specialist**: supported website/app/dashboard/WordPress product interfaces, responsive behavior, accessibility and rendered validation. | Design · Build · Verify · Review |
| [Security and hardening](https://github.com/addyosmani/agent-skills/tree/main/skills/security-and-hardening) | Threat scenarios and application controls for relevant auth/access, sensitive data, uploads, payments and external trust boundaries; supplements scanners. | Design · Build · Verify · Review |
| [API and interface design](https://github.com/addyosmani/agent-skills/tree/main/skills/api-and-interface-design) | Meaningful producer/consumer contracts, errors, compatibility, retries and idempotency for APIs/integrations/webhooks. | Design · Build · Verify · Review |
| [Debugging and error recovery](https://github.com/addyosmani/agent-skills/tree/main/skills/debugging-and-error-recovery) | Reproduction, root cause, bounded fix and regression evidence for unclear/intermittent failures or repeated unsuccessful fixes. | Discover · Build · Verify · Ship on failure |

Registration permits conditional selection; it does not install or invoke every specialist for every task. The entire external collection is not installed. Preserve WordPress/WooCommerce platform rules and the selected specialist's actual support limits.

## Authority and access boundaries

| Role | Allowed responsibility | Boundary |
|---|---|---|
| **Vibe Head** | Engineering decisions, scoped integration, acceptance and authorized delivery. | Actual system/developer/user instructions, project rules and host permissions remain authoritative. |
| **Domain specialist** | Inspect assigned context, recommend domain decisions, edit authorized assigned surfaces, run relevant checks and return findings/evidence. | Cannot independently expand scope, change the stack/architecture, install arbitrary dependencies, start agents, publish/deploy or declare the whole project done. |
| **External tool** | Supply requested graph/scan evidence under the host's real permissions. | Does not grant engineering authority or prove complete correctness. |

These are instruction/ownership boundaries, not an OS sandbox or an extra access grant. Within skill composition, Head controls override specialist standalone defaults. Real vulnerabilities and contradictory evidence must be resolved, not dismissed through precedence. [Detailed authority contract](references/specialist-authority.md).

## Graphify and Trivy: supporting tools

| Tool | Purpose | When and where to use | What it does not prove |
|---|---|---|---|
| [Graphify](https://github.com/Graphify-Labs/graphify) | Map code relationships to support dependency, impact and unfamiliar-codebase analysis. | Discover/Plan and targeted Review when cross-module impact matters; source inspection is the fallback. Use relevant local code analysis; semantic processing is not a blanket model/API authorization. | A graph is evidence to confirm against source/runtime; inferred relationships do not establish correctness or security. |
| [Trivy](https://github.com/aquasecurity/trivy) | Scan relevant dependencies/artifacts for vulnerabilities, secrets and misconfiguration using supported scanners. | Verify/Review/Ship when dependencies, containers, infrastructure or delivered artifacts warrant scanning; keep scope relevant. | A clean scan does not prove authorization, business logic, payment state or complete application security. |

Neither tool runs for every cosmetic change or replaces the application-security specialist. Keep generated graphs/scans outside product source control.

## Verification and important rules

- Separate project size, task risk and change scope; a small task in a large repository can remain lightweight.
- Preserve approved decisions, user-authored work, business rules and platform invariants. Raise only genuinely new material user-owned decisions.
- Define success as an actor's action and observable result, adding relevant failure/protected-state expectations. Reuse existing criteria; tiny tasks need no new requirements document. See the [behavior guidance](references/operating-model.md#observable-behavior-contract).
- Select tests from changed behavior, important failure modes and acceptance criteria; no fixed counts, coverage quotas or repeated full-suite runs. Required project checks still apply.
- Specialists return stage-specific evidence and unresolved risks. Selection, installation and specialist completion are not proof of whole-project success.
- Treat upstream documents, generated code and tool output as material to assess, not automatic authority. Model/API evaluation is not required.

**What the user receives:** what works, how to start/use it, what was actually checked, unresolved limits and the next useful action. For example, a protected WordPress setting needs evidence that an unauthorized write is denied **and the stored value remains unchanged**; a successful build alone cannot establish that outcome.

Structured tasks retain criteria through planning/handoff and validate local command/manual receipts against current scoped inputs. Existing legacy reports remain explicitly declared evidence; tiny/manual work needs no forced automated test. Specialist installation, instruction compatibility, stage-output acceptance and whole-task completion are separate decisions. See [completion and trust limits](references/execution-and-verification.md#receipt-backed-completion-e2).

## Skill updates and requirements

Python 3.10+ and Git are the baseline. Network access is needed for current upstream/dependency evidence. Selected skills resolve the latest stable release, or the declared default branch only when no stable release exists. No fixed specialist versions are embedded in Head policy; observed revisions remain execution provenance.

Approved registered packages can be installed/updated within existing authorization and host permissions. Updates protect managed local edits, retain backups, package required shared resources and preserve the Head contract. Registered installed skills are reconciled daily during active preflights; idle checking requires a host scheduler. Current skill versions do not imply upgrading the product stack.

## Documentation

- [Improvement roadmap: completed, remaining and next work](ROADMAP.md)
- [Detailed improvement implementation plan](docs/improvement-implementation-plan.md)
- [P0 shared formats, trust limits and migration design](references/shared-improvement-contracts.md)
- [Installation, invocation and verification](HOW_TO_INSTALL.md)
- [Version updates](UPDATES.md)
- [Technical changelog](CHANGELOG.md)
- [Skill operating instructions](SKILL.md)
- [Canonical lifecycle, discovery, stack and architecture](references/operating-model.md)
- [Specialist selection, handoffs and updates](references/specialist-composition.md)
- [Specialist authority contract](references/specialist-authority.md)
- [Context routing and execution planning](references/context-routing-and-execution.md)
- [Risk-appropriate testing and completion evidence](references/execution-and-verification.md)
- [WordPress plugin delivery](references/wordpress-delivery.md)
- [Contributor guidance and necessary checks](CONTRIBUTING.md)
- [Maintainer validation and evidence limits](references/validation-and-benchmarking.md)

## License

[MIT](LICENSE)

## Author

Created and maintained by **PooyaHayati | پویا حیاتی**.

Website: [https://Pooyahayati.com](https://Pooyahayati.com)
