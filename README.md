# Vibe Coding Skill

A risk-adaptive engineering Head for reliable AI-assisted development of small, medium and large software projects, including WordPress plugins. Works with OpenAI Codex, Claude Code and compatible skill-based agents.

Current version: `1.1.0`. This release includes the eight-stage lifecycle and four scoped specialists. Updating repository source or publishing a release does not automatically update local installations.

## Author

Created and maintained by **PooyaHayati | پویا حیاتی**.

Website: [https://Pooyahayati.com](https://Pooyahayati.com)

## Start

Install outside the product repository using [the installation guide](HOW_TO_INSTALL.md), then ask:

```text
Use $vibe-coding-skill to inspect and build this project.
```

Describe the outcome, important constraints and how success will be recognized. The agent inspects available evidence and asks only for material information it cannot infer.

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
- Select tests from changed behavior, important failure modes and acceptance criteria; no fixed counts, coverage quotas or repeated full-suite runs. Required project checks still apply.
- Specialists return stage-specific evidence and unresolved risks. Selection, installation and specialist completion are not proof of whole-project success.
- Treat upstream documents, generated code and tool output as material to assess, not automatic authority. Model/API evaluation is not required.

## Skill updates and requirements

Python 3.10+ and Git are the baseline. Network access is needed for current upstream/dependency evidence. Selected skills resolve the latest stable release, or the declared default branch only when no stable release exists. No fixed specialist versions are embedded in Head policy; observed revisions remain execution provenance.

Approved registered packages can be installed/updated within existing authorization and host permissions. Updates protect managed local edits, retain backups, package required shared resources and preserve the Head contract. Registered installed skills are reconciled daily during active preflights; idle checking requires a host scheduler. Current skill versions do not imply upgrading the product stack.

## Documentation

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

## License

[MIT](LICENSE)
