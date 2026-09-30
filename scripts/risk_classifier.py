#!/usr/bin/env python3
"""Deterministic, explainable risk classification for Vibe Coding Skill."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Rule:
    name: str
    tier: int
    pattern: re.Pattern[str]
    reason: str
    approval: bool = False


LABELS = ["tiny", "standard", "significant", "critical"]

TIER_CONTROLS = {
    0: ["focused check"],
    1: ["acceptance criteria", "impact check", "tests", "review"],
    2: [
        "explicit spec",
        "graph/impact analysis",
        "implementation plan",
        "independent review",
        "security/regression checks",
    ],
    3: [
        "explicit approval",
        "rollback/recovery plan",
        "strong verification",
        "post-change validation",
    ],
}

# These are supplemental language signals. Risk decisions are made from the
# structured facts produced below, not directly from an isolated keyword.
RULES = [
    Rule(
        "destructive-data",
        3,
        re.compile(
            r"(?:\b(?:drop\s+(?:table|database|schema)|truncate|wipe|purge)\b"
            r"|\b(?:delete|remove)\b.{0,50}\b(?:all|every)\b.{0,50}"
            r"\b(?:data|records?|customers?|users?|table|database)\b"
            r"|(?:حذف|پاک(?:\s*کردن|\s*کن)?).{0,40}(?:همه|تمام).{0,40}"
            r"(?:داده|اطلاعات|رکورد|مشتری|کاربر|دیتابیس|پایگاه\s*داده))",
            re.I,
        ),
        "destructive data operation",
        True,
    ),
    Rule(
        "production",
        3,
        re.compile(
            r"(?:\b(?:production|prod\s+deploy|switch\s+traffic|cutover|iam|control[- ]?plane)\b"
            r"|(?:پروداکشن|محیط\s+(?:تولید|عملیاتی)))",
            re.I,
        ),
        "production/control-plane impact",
        True,
    ),
    Rule(
        "sensitive-data",
        3,
        re.compile(
            r"(?:\b(?:financial|payment\s+data|health\s+data|medical|private\s+key|"
            r"secret\s+rotation|credentials?)\b"
            r"|(?:داده(?:‌|\s)*مالی|اطلاعات(?:‌|\s)*مالی|داده(?:‌|\s)*پزشکی|"
            r"اطلاعات(?:‌|\s)*سلامت|اطلاعات(?:‌|\s)*پرداخت|داده(?:‌|\s)*پرداخت|"
            r"شماره(?:‌|\s)*کارت|کلید(?:‌|\s)*خصوصی|اعتبارنامه))",
            re.I,
        ),
        "sensitive/security-critical data",
        True,
    ),
    Rule(
        "auth",
        2,
        re.compile(
            r"(?:\b(?:auth|authentication|authorization|jwt|oauth|session\s+cookie|"
            r"permissions?|rbac)\b|(?:احراز(?:‌|\s)*هویت|مجوز|سطح(?:‌|\s)*دسترسی))",
            re.I,
        ),
        "authentication/authorization change",
        True,
    ),
    Rule(
        "migration",
        2,
        re.compile(
            r"(?:\b(?:schema|migration|migrate|database\s+table|index\s+change)\b"
            r"|(?:مهاجرت(?:‌|\s)*داده|تغییر(?:‌|\s)*اسکیما|تغییر(?:‌|\s)*ساختار(?:‌|\s)*دیتابیس))",
            re.I,
        ),
        "schema/data migration impact",
    ),
    Rule(
        "external-integration",
        2,
        re.compile(
            r"\b(?:webhook|third[- ]party|external\s+integration|payment\s+sdk|public\s+api)\b",
            re.I,
        ),
        "external/public contract impact",
        True,
    ),
    Rule(
        "security",
        2,
        re.compile(
            r"\b(?:prompt\s+injection|exfiltrat|vulnerabilit|security|secrets?|privilege)\b",
            re.I,
        ),
        "security-sensitive behavior",
    ),
    Rule(
        "graph-cross-module",
        2,
        re.compile(
            r"\b(?:refactor .*flow|across\s+the\s+application|multi[- ]module|stale.*graph)\b",
            re.I,
        ),
        "cross-module/project-intelligence impact",
    ),
    Rule(
        "dependency",
        1,
        re.compile(r"\b(?:install|dependency|package|library|sdk)\b", re.I),
        "dependency change",
    ),
    Rule(
        "feature",
        1,
        re.compile(r"\b(?:add|feature|button|export|saved[- ]?filter|endpoint)\b", re.I),
        "standard product change",
    ),
]

TINY = re.compile(
    r"\b(?:typo|copy\s+edit|text\s+only|one[- ]line|localized\s+styling|css\s+correction)\b",
    re.I,
)


def policy_for_tier(tier: int) -> dict[str, Any]:
    if tier not in {0, 1, 2, 3}:
        raise ValueError(f"invalid risk tier: {tier}")
    if tier == 0:
        controls = list(TIER_CONTROLS[0])
    else:
        controls = []
        for level in range(1, tier + 1):
            controls.extend(TIER_CONTROLS[level])
    return {
        "tier": tier,
        "label": LABELS[tier],
        "required_controls": controls,
    }


def infer_facts(text: str, paths: list[str] | None = None) -> dict[str, Any]:
    normalized = " ".join([text, *(paths or [])])
    matches = [rule for rule in RULES if rule.pattern.search(normalized)]
    facts: dict[str, Any] = {
        "operation": "standard",
        "environment": "unspecified",
        "data_sensitivity": "unspecified",
        "change_boundary": "local",
        "signals": [rule.name for rule in matches],
        "uncertainty": [],
    }

    names = {rule.name for rule in matches}
    if "destructive-data" in names:
        facts["operation"] = "destructive-data"
    elif "auth" in names:
        facts["operation"] = "authorization"
    elif "migration" in names:
        facts["operation"] = "migration"
    elif "external-integration" in names:
        facts["operation"] = "external-integration"
    elif "dependency" in names:
        facts["operation"] = "dependency"

    if "production" in names:
        facts["environment"] = "production"
    if "sensitive-data" in names:
        facts["data_sensitivity"] = "sensitive"
    if "graph-cross-module" in names:
        facts["change_boundary"] = "cross-module"

    # Non-English or mixed-language text with no recognized risk fact is
    # explicitly uncertain rather than being treated as evidence of low risk.
    if any(ord(ch) > 127 and ch.isalpha() for ch in text) and not matches:
        facts["uncertainty"].append(
            "non-English or mixed-language request has no recognized risk facts"
        )
    return facts


def merge_facts(inferred: dict[str, Any], supplied: dict[str, Any] | None) -> dict[str, Any]:
    if not supplied:
        return inferred
    result = dict(inferred)
    for key in ("operation", "environment", "data_sensitivity", "change_boundary"):
        value = supplied.get(key)
        if isinstance(value, str) and value.strip():
            result[key] = value.strip().lower()
    return result


def tier_from_facts(facts: dict[str, Any], matches: list[Rule]) -> tuple[int, list[str], bool]:
    tier = max((rule.tier for rule in matches), default=1)
    reasons = [rule.reason for rule in matches if rule.tier == tier]
    approval = any(rule.approval and rule.tier == tier for rule in matches)

    if facts.get("operation") == "destructive-data":
        tier = max(tier, 3)
        reasons = ["destructive data operation"]
        approval = True
    if facts.get("environment") == "production":
        tier = max(tier, 3)
        if tier == 3 and "production/control-plane impact" not in reasons:
            reasons.append("production/control-plane impact")
        approval = True
    if facts.get("data_sensitivity") in {
        "sensitive", "financial", "health", "credentials", "secret",
    }:
        tier = max(tier, 3)
        if "sensitive/security-critical data" not in reasons:
            reasons.append("sensitive/security-critical data")
        approval = True
    if facts.get("operation") in {"authorization", "migration", "external-integration", "security"}:
        tier = max(tier, 2)
    if facts.get("change_boundary") in {"cross-module", "public-contract"}:
        tier = max(tier, 2)

    return tier, list(dict.fromkeys(reasons)), approval


def classify(
    text: str,
    paths: list[str] | None = None,
    facts: dict[str, Any] | None = None,
) -> dict[str, object]:
    normalized = " ".join([text, *(paths or [])])
    matches = [rule for rule in RULES if rule.pattern.search(normalized)]
    inferred = infer_facts(text, paths)
    effective_facts = merge_facts(inferred, facts)
    tier, reasons, approval = tier_from_facts(effective_facts, matches)

    if not matches and not facts and TINY.search(normalized):
        tier = 0
        reasons = ["localized/reversible change"]
        approval = False
    elif not reasons:
        reasons = [
            "standard change with no higher-risk fact detected"
        ]

    policy = policy_for_tier(tier)
    return {
        **policy,
        "approval_required": tier == 3 or approval,
        "reasons": reasons,
        "matched_rules": [rule.name for rule in matches],
        "risk_facts": effective_facts,
        "uncertainty": list(effective_facts.get("uncertainty") or []),
        "note": (
            "This classifier supplies a conservative workflow floor; engineering "
            "context or verified structured facts may raise the tier."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?", default="")
    ap.add_argument("--path", action="append", default=[])
    ap.add_argument(
        "--facts-json",
        help=(
            "Optional JSON object with operation, environment, data_sensitivity, "
            "and change_boundary facts."
        ),
    )
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    if not ns.text and not ns.path and not ns.facts_json:
        raise SystemExit("provide task text, --path, and/or --facts-json")

    supplied = json.loads(ns.facts_json) if ns.facts_json else None
    if supplied is not None and not isinstance(supplied, dict):
        raise SystemExit("--facts-json must be a JSON object")
    result = classify(ns.text, ns.path, supplied)
    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Tier {result['tier']} — {result['label']}")
        print(f"Approval required: {result['approval_required']}")
        for reason in result["reasons"]:
            print(f"- {reason}")
        for warning in result["uncertainty"]:
            print(f"WARN: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
