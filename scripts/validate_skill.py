#!/usr/bin/env python3
"""Lightweight repository validation without third-party Python dependencies."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
REQUIRED_REFS = [
    "references/operating-model.md",
    "references/risk-and-autonomy.md",
    "references/project-intelligence.md",
    "references/security-and-dependencies.md",
    "references/project-state-and-traceability.md",
    "references/execution-and-verification.md",
    "references/bootstrap-and-evals.md",
]
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def main() -> int:
    if not SKILL.exists():
        fail("SKILL.md is missing")
    text = SKILL.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail("SKILL.md must start with YAML frontmatter")

    parts = text.split("---", 2)
    if len(parts) != 3:
        fail("invalid frontmatter boundaries")
    _, fm, body = parts

    fields: dict[str, str] = {}
    for line in fm.splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip().strip('"')

    name = fields.get("name", "")
    description = fields.get("description", "")
    if not NAME_RE.fullmatch(name):
        fail(f"invalid skill name: {name!r}")
    if len(name) > 64:
        fail("skill name exceeds 64 chars")
    if not description or len(description) > 1024:
        fail("description must be 1..1024 chars")
    if len(body.splitlines()) > 500:
        fail("SKILL.md exceeds recommended 500 lines")

    for rel in REQUIRED_REFS:
        if not (ROOT / rel).exists():
            fail(f"missing reference: {rel}")
        if rel not in text:
            fail(f"SKILL.md does not reference {rel}")

    for script in ("doctor.py", "change_budget.py", "graphify_compat.py", "bootstrap_project.py", "dependency_guard.py", "validate_evals.py", "sync_package.py"):
        path = ROOT / "scripts" / script
        if not path.exists():
            fail(f"missing script: scripts/{script}")
        compile(path.read_text(encoding="utf-8"), str(path), "exec")

    print("Vibe Coding Skill validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
