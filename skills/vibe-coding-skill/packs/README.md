# Capability Pack Contract

Capability packs are small constraint bundles selected by `scripts/context_router.py`.

A pack is not a tutorial and not a mini-architecture. Keep it short and decision-relevant.

Each pack should contain:

- **Activation** — evidence that makes the pack relevant.
- **Constraints** — platform/runtime rules that affect implementation.
- **Risks** — failure modes the task must consider.
- **Integration points** — boundaries that deserve explicit verification.
- **Required checks** — evidence expected before completion when the pack is active.
- **Avoid** — patterns that commonly create compatibility, security, or performance problems.
- **Deeper references** — optional official/specialist material; baseline correctness must not depend on an external skill.

Project-wide invariants and Vibe Core safety/evidence rules always outrank pack convenience.
