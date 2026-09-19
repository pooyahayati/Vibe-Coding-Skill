#!/usr/bin/env python3
"""Deterministic baseline risk classifier for proposed software changes."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TIER_NAMES = {0: "tiny", 1: "standard", 2: "significant", 3: "critical"}

RULES = [
    (3, "destructive-data", r"\b(drop|truncate|delete all|destructive|irreversible|data loss)\b"),
    (3, "production", r"\b(production|prod deploy|switch traffic|iam|control plane|rotate secrets?)\b"),
    (3, "sensitive-domain", r"\b(payment settlement|financial transaction|medical record|safety[- ]critical)\b"),
    (2, "authentication", r"\b(auth|authentication|authorization|oauth|jwt|session cookies?|permissions?)\b"),
    (2, "migration", r"\b(schema|migration|migrate database|database migration)\b"),
    (2, "architecture", r"\b(architecture|framework change|database change|microservices?|public api|breaking api)\b"),
    (2, "integration", r"\b(webhook|third[- ]party integration|payment sdk|external integration)\b"),
    (2, "prompt-injection", r"\b(ignore project rules|print secrets|exfiltrate|send \.env|prompt injection)\b"),
    (2, "stale-graph", r"\b(stale graph|graph-state|older than head|code graph.*refactor)\b"),
    (1, "dependency", r"\b(install|dependency|package|library|sdk)\b"),
    (1, "feature", r"\b(add|feature|endpoint|button|export|filter|workflow)\b"),
]

TINY = re.compile(r"\b(typo|copy edit|one-line|one line|text only|localized styling|css tweak)\b", re.I)

SENSITIVE_PATHS = [
    (3, "production-infra-path", re.compile(r"(^|/)(prod|production)(/|$)", re.I)),
    (2, "auth-path", re.compile(r"(^|/)(auth|security|iam|permissions?)(/|\.|$)", re.I)),
    (2, "migration-path", re.compile(r"(^|/)(migrations?|schema)(/|\.|$)", re.I)),
    (2, "infra-path", re.compile(r"(Dockerfile|terraform|\.tf$|k8s|kubernetes|helm|\.github/workflows)", re.I)),
]


def classify(text: str, files: list[str] | None = None) -> dict[str, object]:
    lowered = text.lower()
    tier = 0 if TINY.search(text) else 1
    reasons: list[str] = []

    for rule_tier, reason, pattern in RULES:
        if re.search(pattern, lowered, re.I):
            tier = max(tier, rule_tier)
            reasons.append(reason)

    for path in files or []:
        for path_tier, reason, rx in SENSITIVE_PATHS:
            if rx.search(path):
                tier = max(tier, path_tier)
                reasons.append(f"{reason}:{path}")

    if not reasons and tier == 0:
        reasons.append("tiny-localized-change")
    elif not reasons:
        reasons.append("ordinary-product-change")

    approval_required = tier == 3 or any(
        r in reasons
        for r in ("architecture", "authentication", "migration", "sensitive-domain")
    )
    required_controls = {
        0: ["focused-check"],
        1: ["acceptance-criteria", "impact-check", "tests"],
        2: ["explicit-spec", "impact-analysis", "independent-review", "security-regression"],
        3: ["explicit-approval", "rollback-recovery", "strong-verification", "human-review-when-available"],
    }[tier]

    return {
        "tier": tier,
        "tier_name": TIER_NAMES[tier],
        "approval_required": approval_required,
        "reasons": sorted(set(reasons)),
        "required_controls": required_controls,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?", default="")
    ap.add_argument("--file", action="append", default=[])
    ap.add_argument("--files-from")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    files = list(ns.file)
    if ns.files_from:
        files.extend(
            x.strip()
            for x in Path(ns.files_from).read_text(encoding="utf-8").splitlines()
            if x.strip()
        )
    result = classify(ns.text, files)
    if ns.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Tier {result['tier']} — {result['tier_name']}")
        print(f"Approval required: {result['approval_required']}")
        print("Reasons: " + ", ".join(result["reasons"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
