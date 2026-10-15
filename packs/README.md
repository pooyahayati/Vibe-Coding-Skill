# Capability Pack Contract

Capability packs are small constraint bundles selected by `scripts/context_router.py`.

A pack is not a tutorial and not a mini-architecture. Keep it short and decision-relevant.

Each pack should contain:

- **Activation** — evidence that makes the pack relevant.
- **Constraints** — platform/runtime rules that affect implementation.
- **Risks** — failure modes the task must consider.
- **Integration points** — boundaries that deserve explicit verification.
- **Required checks** — applicable evidence for changed outcomes/risks, selected through the Head's [verification policy](../references/execution-and-verification.md#testing-policy). Activation alone does not require the entire list or repeated checks at each stage.
- **Avoid** — patterns that commonly create compatibility, security, or performance problems.
- **Deeper references** — optional official/specialist material; baseline correctness must not depend on an external skill.

Project-wide invariants and Vibe Core safety/evidence rules always outrank pack convenience.
