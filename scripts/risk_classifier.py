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


RULES = [
    Rule(
        "destructive-data",
        3,
        re.compile(
            r"\b(truncate|delete all|wipe|destroy|purge)\b"
            r"|\bdrop\s+(?:the\s+)?(?:[\w-]+\s+){0,2}(table|database|schema|collection|index)\b"
            r"|حذف\s+(همه|تمام|کامل)|پاک\s*کردن\s+(همه|تمام|کامل)|پاکسازی\s+کامل|از\s+بین\s+بردن",
            re.I,
        ),
        "destructive data operation",
        True,
    ),
    Rule(
        "production",
        3,
        re.compile(
            r"\b(production|prod deploy|switch traffic|cutover|iam|control[- ]?plane)\b"
            r"|محیط\s+تولید|پروداکشن|انتقال\s+ترافیک",
            re.I,
        ),
        "production/control-plane impact",
        True,
    ),
    Rule(
        "sensitive-data",
        3,
        re.compile(
            r"\b(financial|payment data|health data|medical|private key|secret rotation|credentials?)\b"
            r"|داده(?:‌|\s)*های?\s+(مالی|پرداخت|سلامت|پزشکی)|کلید\s+خصوصی|اعتبارنامه",
            re.I,
        ),
        "sensitive/security-critical data",
        True,
    ),
    Rule(
        "auth",
        2,
        re.compile(
            r"\b(auth|authentication|authorization|jwt|oauth|session cookie|permissions?|rbac)\b"
            r"|احراز\s+هویت|مجوز|سطح\s+دسترسی",
            re.I,
        ),
        "authentication/authorization change",
        True,
    ),
    Rule(
        "migration",
        2,
        re.compile(
            r"\b(schema|migration|migrate|database table|index change)\b"
            r"|مهاجرت\s+داده|تغییر\s+اسکیما|طرح\s+پایگاه\s+داده",
            re.I,
        ),
        "schema/data migration impact",
    ),
    Rule(
        "external-integration",
        2,
        re.compile(
            r"\b(webhook|third[- ]party|external integration|payment sdk|public api)\b"
            r"|وبهوک|سرویس\s+خارجی|یکپارچه(?:‌|\s)*سازی\s+خارجی",
            re.I,
        ),
        "external/public contract impact",
        True,
    ),
    Rule(
        "security",
        2,
        re.compile(
            r"\b(prompt injection|exfiltrat|vulnerabilit|security|secrets?|privilege)\b"
            r"|تزریق\s+پرامپت|آسیب(?:‌|\s)*پذیری|امنیت|افشای\s+راز",
            re.I,
        ),
        "security-sensitive behavior",
    ),
    Rule(
        "graph-cross-module",
        2,
        re.compile(
            r"\b(refactor .*flow|across the application|multi[- ]module|stale.*graph)\b"
            r"|چند\s*ماژول|سراسر\s+برنامه",
            re.I,
        ),
        "cross-module/project-intelligence impact",
    ),
    Rule(
        "dependency",
        1,
        re.compile(r"\b(install|dependency|package|library|sdk)\b|وابستگی|پکیج|کتابخانه", re.I),
        "dependency change",
    ),
    Rule(
        "feature",
        1,
        re.compile(r"\b(add|feature|button|export|saved[- ]?filter|endpoint)\b|افزودن|ویژگی|دکمه", re.I),
        "standard product change",
    ),
]

TINY = re.compile(
    r"\b(typo|copy edit|text only|one[- ]line|localized styling|css correction)\b"
    r"|غلط\s+املایی|فقط\s+متن|اصلاح\s+متن|استایل\s+موضعی",
    re.I,
)

TIER_LABELS = ["tiny", "standard", "significant", "critical"]

CONTROLS_BY_TIER = {
    0: ["focused check"],
    1: ["acceptance criteria", "impact check", "tests", "review"],
    2: [
        "acceptance criteria",
        "impact check",
        "explicit spec",
        "graph/impact analysis",
        "implementation plan",
        "tests",
        "review",
        "security/regression checks",
    ],
    3: [
        "acceptance criteria",
        "impact check",
        "explicit spec",
        "graph/impact analysis",
        "implementation plan",
        "tests",
        "review",
        "security/regression checks",
        "explicit approval",
        "rollback/recovery plan",
        "strong verification",
        "post-change validation",
    ],
}

FACT_FIELDS = ("operation", "environment", "data_sensitivity", "change_boundary")
INPUT_FIELDS = (*FACT_FIELDS, "change_effect", "scope_evidence")
FACT_VALUES = {
    "operation": {"tiny", "feature", "read-only", "refactor", "destructive", "auth",
                  "migration", "external-integration", "dependency", "security", "payment"},
    "environment": {"local", "development", "test", "staging", "production", "control-plane"},
    "data_sensitivity": {"none", "public", "internal", "personal", "sensitive", "financial",
                         "payment", "health", "credentials", "private-key", "secret"},
    "change_boundary": {"local", "module", "cross-module", "system", "application-wide"},
}
FACT_ALIASES = {
    "operation": {"delete": "destructive", "delete-all": "destructive", "wipe": "destructive",
                  "purge": "destructive", "drop-data": "destructive", "authentication": "auth",
                  "authorization": "auth", "schema-migration": "migration", "data-migration": "migration",
                  "webhook": "external-integration", "public-api": "external-integration",
                  "package-change": "dependency"},
    "environment": {"prod": "production", "live": "production", "dev": "development"},
    "data_sensitivity": {"pii": "personal", "medical": "health"},
    "change_boundary": {"single-module": "module", "multi-module": "cross-module"},
}


def policy_for_tier(tier: int, approval_required: bool = False) -> dict[str, object]:
    if tier not in {0, 1, 2, 3}:
        raise ValueError(f"unsupported risk tier: {tier}")
    return {
        "tier": tier,
        "label": TIER_LABELS[tier],
        "approval_required": bool(approval_required or tier == 3),
        "required_controls": list(CONTROLS_BY_TIER[tier]),
    }


def normalize_fact(value: Any) -> str:
    return re.sub(r"[\s_]+", "-", str(value or "").strip().lower())


def normalized_facts(facts: dict[str, Any] | None) -> dict[str, str]:
    return {
        field: FACT_ALIASES[field].get(normalize_fact((facts or {}).get(field)),
                                       normalize_fact((facts or {}).get(field)))
        for field in FACT_FIELDS
    }


def structured_fact_signals(facts: dict[str, Any] | None) -> list[dict[str, object]]:
    if not facts:
        return []

    signals: list[dict[str, object]] = []
    normalized = normalized_facts(facts)

    operation = normalized["operation"]
    if operation in {"destructive", "delete-all", "wipe", "purge", "drop-data"}:
        signals.append({"name": "fact:destructive-data", "tier": 3, "reason": "structured fact: destructive data operation", "approval": True})
    elif operation in {"authentication", "authorization", "auth"}:
        signals.append({"name": "fact:auth", "tier": 2, "reason": "structured fact: authentication/authorization change", "approval": True})
    elif operation in {"migration", "schema-migration", "data-migration"}:
        signals.append({"name": "fact:migration", "tier": 2, "reason": "structured fact: schema/data migration", "approval": False})
    elif operation in {"external-integration", "webhook", "public-api"}:
        signals.append({"name": "fact:external-integration", "tier": 2, "reason": "structured fact: external/public contract impact", "approval": True})
    elif operation in {"dependency", "package-change"}:
        signals.append({"name": "fact:dependency", "tier": 1, "reason": "structured fact: dependency change", "approval": False})
    elif operation in {"security", "payment"}:
        signals.append({"name": "fact:security", "tier": 2, "reason": "structured fact: security/payment behavior", "approval": False})
    elif operation in {"feature", "refactor"}:
        signals.append({"name": "fact:" + operation, "tier": 1, "reason": "structured fact: bounded behavioral change", "approval": False})

    environment = normalized["environment"]
    if environment in {"production", "prod", "control-plane"}:
        signals.append({"name": "fact:production", "tier": 3, "reason": "structured fact: production/control-plane impact", "approval": True})

    sensitivity = normalized["data_sensitivity"]
    if sensitivity in {"sensitive", "financial", "payment", "health", "medical", "credentials", "private-key", "secret"}:
        signals.append({"name": "fact:sensitive-data", "tier": 3, "reason": "structured fact: sensitive/security-critical data", "approval": True})
    elif sensitivity in {"personal", "pii"}:
        signals.append({"name": "fact:personal-data", "tier": 2, "reason": "structured fact: personal-data impact", "approval": False})

    boundary = normalized["change_boundary"]
    if boundary in {"cross-module", "multi-module", "system", "application-wide"}:
        signals.append({"name": "fact:cross-module", "tier": 2, "reason": "structured fact: cross-module/system impact", "approval": False})

    return signals


def classify(
    text: str,
    paths: list[str] | None = None,
    facts: dict[str, Any] | None = None,
) -> dict[str, object]:
    if facts is not None and not isinstance(facts, dict):
        raise ValueError("structured risk facts must be an object")
    normalized_text = " ".join([text, *(paths or [])])
    discovered = [rule for rule in RULES if rule.pattern.search(normalized_text)]
    fact_signals = structured_fact_signals(facts)
    supplied_facts = facts or {}
    canonical = normalized_facts(supplied_facts)
    uncertainties: list[str] = []
    if supplied_facts:
        for field in FACT_FIELDS:
            if canonical[field] not in FACT_VALUES[field]:
                uncertainties.append(f"structured fact unresolved: {field}")
        for field in sorted(set(supplied_facts) - set(INPUT_FIELDS)):
            uncertainties.append(f"unsupported structured risk field: {field}")

    effect = normalize_fact(supplied_facts.get("change_effect"))
    evidence = supplied_facts.get("scope_evidence")
    assessment = {"status": "not-provided", "semantics_verified": False}
    if "change_effect" in supplied_facts or "scope_evidence" in supplied_facts:
        assessment.update(effect=effect, evidence=evidence, paths=list(paths or []), status="unresolved")
        if effect not in {"non-runtime", "behavioral"}:
            uncertainties.append("change_effect must be non-runtime or behavioral")
        elif effect == "non-runtime":
            if not isinstance(evidence, str) or not evidence.strip() or not paths:
                uncertainties.append("non-runtime scope needs known affected paths and concrete inspection evidence")
            if fact_signals or canonical["operation"] not in {"tiny", "read-only"}:
                uncertainties.append("non-runtime scope conflicts with operation or material risk facts")
            if not uncertainties:
                assessment["status"] = "accepted"
        else:
            assessment["status"] = "behavioral"

    # A Head-reviewed scope assessment can resolve discovery signals; a bare
    # tiny claim cannot. This validates consistency, not the truth of the review.
    resolved = assessment["status"] == "accepted"
    matches = [] if resolved else discovered

    text_tier = max((rule.tier for rule in matches), default=-1)
    fact_tier = max((int(row["tier"]) for row in fact_signals), default=-1)
    tier = max(text_tier, fact_tier)

    if tier < 0:
        tier = 0 if resolved or TINY.search(normalized_text) else 1

    highest_text = [rule for rule in matches if rule.tier == tier]
    highest_facts = [row for row in fact_signals if int(row["tier"]) == tier]
    reasons = [rule.reason for rule in highest_text] + [str(row["reason"]) for row in highest_facts]
    if not reasons:
        reasons = [
            "reviewed non-runtime scope" if resolved else "localized/reversible change"
            if tier == 0
            else "standard change with no higher-risk signal detected"
        ]

    approval = any(rule.approval and rule.tier == tier for rule in matches)
    approval = approval or any(bool(row["approval"]) and int(row["tier"]) == tier for row in fact_signals)

    policy = policy_for_tier(tier, approval)

    if not resolved and text_tier > max(fact_tier, 0) and canonical["operation"] in {"tiny", "read-only"}:
        uncertainties.append("text/path risk signals remain unresolved; inspect actual effects before treating them as incidental")
    if not supplied_facts and not matches and not fact_signals and not TINY.search(normalized_text):
        uncertainties.append(
            "no explicit risk signal was recognized; provide structured risk facts when operation, environment, data sensitivity, or change boundary may affect risk"
        )

    return {
        **policy,
        "reasons": list(dict.fromkeys(reasons)),
        "matched_rules": [rule.name for rule in matches]
        + [str(row["name"]) for row in fact_signals],
        "structured_facts": {**{key: canonical[key] for key in FACT_FIELDS if key in supplied_facts},
                             **{key: supplied_facts[key] for key in INPUT_FIELDS if key not in FACT_FIELDS and key in supplied_facts}},
        "scope_assessment": assessment,
        "resolved_signals": [rule.name for rule in discovered] if resolved else [],
        "uncertainties": uncertainties,
        "decision_basis": "reviewed-scope+structured-facts" if resolved else "structured-facts+text-signals" if fact_signals else "text-signals",
        "note": (
            "This classifier supplies a conservative workflow floor; engineering context may raise the tier. "
            "Text/path matches are discovery signals, resolved only by a consistent Head scope review. "
            "The caller verifies actual effects; this tool checks input consistency, not source semantics or authorization."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?", default="")
    ap.add_argument("--path", action="append", default=[])
    for field in INPUT_FIELDS:
        ap.add_argument("--" + field.replace("_", "-"))
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    if not ns.text and not ns.path:
        raise SystemExit("provide task text and/or --path")

    facts = {field: getattr(ns, field) for field in INPUT_FIELDS if getattr(ns, field) is not None}
    result = classify(ns.text, ns.path, facts or None)
    if ns.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Tier {result['tier']} — {result['label']}")
        print(f"Approval required: {result['approval_required']}")
        for reason in result["reasons"]:
            print(f"- {reason}")
        for uncertainty in result["uncertainties"]:
            print(f"WARN: {uncertainty}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
