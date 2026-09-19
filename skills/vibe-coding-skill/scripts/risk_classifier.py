#!/usr/bin/env python3
"""Deterministic, explainable risk classification for Vibe Coding Skill."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Rule:
    name: str
    tier: int
    pattern: re.Pattern[str]
    reason: str
    approval: bool = False

RULES = [
    Rule("destructive-data", 3, re.compile(r"\b(drop|truncate|delete all|wipe|destroy|purge)\b", re.I), "destructive data operation", True),
    Rule("production", 3, re.compile(r"\b(production|prod deploy|switch traffic|cutover|iam|control[- ]?plane)\b", re.I), "production/control-plane impact", True),
    Rule("sensitive-data", 3, re.compile(r"\b(financial|payment data|health data|medical|private key|secret rotation|credentials?)\b", re.I), "sensitive/security-critical data", True),
    Rule("auth", 2, re.compile(r"\b(auth|authentication|authorization|jwt|oauth|session cookie|permissions?|rbac)\b", re.I), "authentication/authorization change", True),
    Rule("migration", 2, re.compile(r"\b(schema|migration|migrate|database table|index change)\b", re.I), "schema/data migration impact"),
    Rule("external-integration", 2, re.compile(r"\b(webhook|third[- ]party|external integration|payment sdk|public api)\b", re.I), "external/public contract impact", True),
    Rule("security", 2, re.compile(r"\b(prompt injection|exfiltrat|vulnerabilit|security|secrets?|privilege)\b", re.I), "security-sensitive behavior"),
    Rule("graph-cross-module", 2, re.compile(r"\b(refactor .*flow|across the application|multi[- ]module|stale.*graph)\b", re.I), "cross-module/project-intelligence impact"),
    Rule("dependency", 1, re.compile(r"\b(install|dependency|package|library|sdk)\b", re.I), "dependency change"),
    Rule("feature", 1, re.compile(r"\b(add|feature|button|export|saved[- ]?filter|endpoint)\b", re.I), "standard product change"),
]

TINY = re.compile(r"\b(typo|copy edit|text only|one[- ]line|localized styling|css correction)\b", re.I)


def classify(text: str, paths: list[str] | None = None) -> dict[str, object]:
    normalized = " ".join([text, *(paths or [])])
    matches = [r for r in RULES if r.pattern.search(normalized)]
    if matches:
        tier = max(r.tier for r in matches)
    elif TINY.search(normalized):
        tier = 0
    else:
        tier = 1

    # Tiny wording must never downgrade explicit higher-risk indicators.
    if tier <= 1 and TINY.search(normalized) and not matches:
        tier = 0

    reasons = [r.reason for r in matches if r.tier == tier]
    if not reasons:
        reasons = ["localized/reversible change" if tier == 0 else "standard change with no higher-risk signal detected"]

    approval = tier == 3 or any(r.approval and r.tier == tier for r in matches)

    controls = {
        0: ["focused check"],
        1: ["acceptance criteria", "impact check", "tests", "review"],
        2: ["explicit spec", "graph/impact analysis", "implementation plan", "independent review", "security/regression checks"],
        3: ["explicit approval", "rollback/recovery plan", "strong verification", "post-change validation"],
    }[tier]

    return {
        "tier": tier,
        "label": ["tiny", "standard", "significant", "critical"][tier],
        "approval_required": approval,
        "reasons": reasons,
        "matched_rules": [r.name for r in matches],
        "required_controls": controls,
        "note": "This classifier supplies a conservative workflow floor; engineering context may raise the tier.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?", default="")
    ap.add_argument("--path", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    if not ns.text and not ns.path:
        raise SystemExit("provide task text and/or --path")
    result = classify(ns.text, ns.path)
    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Tier {result['tier']} — {result['label']}")
        print(f"Approval required: {result['approval_required']}")
        for reason in result["reasons"]:
            print(f"- {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
