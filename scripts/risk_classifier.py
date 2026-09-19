#!/usr/bin/env python3
"""Deterministic baseline risk classifier for Vibe Coding Skill.

This is a guardrail, not a substitute for engineering judgment. It uses explicit
signals first and lightweight text/path heuristics second. When uncertain, it
returns the higher justified tier rather than pretending precision.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

TIER_NAMES = {0: "tiny", 1: "standard", 2: "significant", 3: "critical"}

TIER3_PATTERNS = {
    "destructive_data": re.compile(
        r"\b(drop\s+.{0,60}\b(table|database|column)\b|truncate|destructive\s+migration|delete\s+production\s+data|irreversible\s+(migration|operation)|data\s+loss)",
        re.I,
    ),
    "production_deploy": re.compile(
        r"\b(deploy|release|rollout|switch\s+traffic|cut\s*over|promote)\b.{0,40}\bproduction\b|\bproduction\b.{0,40}\b(deploy|release|rollout|switch\s+traffic|cut\s*over|promote)\b",
        re.I,
    ),
    "control_plane": re.compile(
        r"\b(iam|root\s+credential|production\s+secret|control\s*plane|cluster\s+admin|organization\s+owner)\b.{0,50}\b(change|rotate|replace|delete|grant|revoke)\b",
        re.I,
    ),
}

TIER2_PATTERNS = {
    "authentication": re.compile(r"\b(auth(?:entication|orization)?|oauth|oidc|jwt|session\s+cookie|permission|rbac|acl)\b", re.I),
    "schema": re.compile(r"\b(schema|migration|migrate|database\s+structure|column\s+type|foreign\s+key)\b", re.I),
    "integration": re.compile(r"\b(third[- ]party|external\s+integration|sdk|webhook|payment\s+provider|payment\s+sdk|message\s+queue|background\s+job)\b", re.I),
    "architecture": re.compile(r"\b(change|replace|migrate|switch)\b.{0,40}\b(framework|database|architecture|runtime|language|auth(?:entication)?\s+model)\b", re.I),
    "public_contract": re.compile(r"\b(public\s+api|breaking\s+api|shared\s+contract|protocol\s+change)\b", re.I),
    "prompt_injection": re.compile(r"\b(prompt\s+injection|ignore\s+project\s+rules|print\s+secrets|exfiltrat|send\s+\.env)\b", re.I),
    "graph_stale_refactor": re.compile(r"\b(stale|older\s+than\s+head)\b.{0,80}\b(graph|graph-state)\b|\brefactor\b.{0,80}\b(payment|cross[- ]module|multiple\s+modules)\b", re.I),
}

TINY_PATTERNS = [
    re.compile(r"\b(typo|copy\s+edit|text\s+only|footer\s+text|spelling|one[- ]line\s+fix|localized\s+styling|small\s+css\s+fix)\b", re.I),
]

APPROVAL_PATTERNS = {
    "security_architecture": re.compile(r"\b(change|replace|switch|migrate)\b.{0,60}\b(auth(?:entication)?|authorization|jwt|oauth|oidc|security\s+model)\b", re.I),
    "data_model": re.compile(r"\b(schema\s+migration|database\s+migration|change\s+schema|migrate\s+.*schema|drop\s+(table|column|database))\b", re.I),
    "new_sensitive_integration": re.compile(r"\b(integrate|add|introduce)\b.{0,60}\b(payment\s+(sdk|provider)|third[- ]party\s+payment|identity\s+provider|external\s+auth)\b", re.I),
    "architecture": re.compile(r"\b(change|replace|switch|migrate)\b.{0,50}\b(framework|database|architecture|runtime|language)\b", re.I),
}

PATH_TIER2 = [
    re.compile(r"(^|/)(auth|authentication|authorization|security|permissions?|iam)(/|\.|$)", re.I),
    re.compile(r"(^|/)(migrations?|schema)(/|\.|$)", re.I),
    re.compile(r"(^|/)(webhooks?|payments?|billing)(/|\.|$)", re.I),
]
PATH_TIER3 = [
    re.compile(r"(^|/)(prod|production)(/|\.|$).*(terraform|\.tf$|k8s|kubernetes|helm|deployment)", re.I),
    re.compile(r"(^|/)(iam|secrets?|credentials?)(/|\.|$).*(prod|production)", re.I),
]

EXPLICIT_FLAGS = {
    "tiny": 0,
    "auth": 2,
    "schema": 2,
    "integration": 2,
    "architecture": 2,
    "external-dependency": 1,
    "prompt-injection": 2,
    "sensitive-data": 3,
    "destructive": 3,
    "production": 3,
    "irreversible": 3,
}

@dataclass
class RiskResult:
    tier: int
    tier_name: str
    approval_required: bool
    signals: list[str]
    required_controls: list[str]
    confidence: str

def _controls_for(tier: int, signals: Iterable[str]) -> list[str]:
    s = set(signals)
    controls: list[str] = []
    if tier == 0:
        return ["focused-check"]
    controls.extend(["acceptance-criteria", "impact-check", "tests", "review"])
    if tier >= 2:
        controls.extend(["explicit-spec", "project-graph-or-equivalent-impact-analysis", "independent-review", "regression-check"])
    if any(x.startswith("authentication") or x.startswith("prompt_injection") for x in s):
        controls.append("security-review")
    if any(x.startswith("schema") or x.startswith("destructive_data") for x in s):
        controls.extend(["migration-validation", "data-integrity-check"])
    if tier >= 3:
        controls.extend(["explicit-approval", "rollback-or-recovery-plan", "strong-post-change-verification"])
    return list(dict.fromkeys(controls))

def classify(text: str, changed_files: Iterable[str] | None = None, flags: Iterable[str] | None = None) -> RiskResult:
    text = text or ""
    changed_files = list(changed_files or [])
    flags = [f.strip().lower() for f in (flags or []) if f.strip()]
    tier = 1
    signals: list[str] = []
    approval = False
    explicit_tiny = False

    for flag in flags:
        if flag not in EXPLICIT_FLAGS:
            signals.append(f"unknown_flag:{flag}")
            continue
        flag_tier = EXPLICIT_FLAGS[flag]
        if flag == "tiny":
            explicit_tiny = True
        else:
            tier = max(tier, flag_tier)
        signals.append(f"flag:{flag}")

    for label, rx in TIER3_PATTERNS.items():
        if rx.search(text):
            tier = 3
            approval = True
            signals.append(label)

    if tier < 3:
        for label, rx in TIER2_PATTERNS.items():
            if rx.search(text):
                tier = max(tier, 2)
                signals.append(label)

    for label, rx in APPROVAL_PATTERNS.items():
        if rx.search(text):
            approval = True
            signals.append(f"approval:{label}")

    for path in changed_files:
        normalized = path.replace("\\", "/")
        if any(rx.search(normalized) for rx in PATH_TIER3):
            tier = 3
            approval = True
            signals.append(f"critical_path:{normalized}")
        elif any(rx.search(normalized) for rx in PATH_TIER2):
            tier = max(tier, 2)
            signals.append(f"significant_path:{normalized}")

    tiny_match = explicit_tiny or any(rx.search(text) for rx in TINY_PATTERNS)
    if tiny_match and tier == 1 and not approval:
        tier = 0
        signals.append("tiny_scope")

    if tier == 3:
        approval = True

    if signals and all(s in {"prompt_injection"} or s.startswith("unknown_flag:") for s in signals):
        approval = False

    confidence = "high" if signals else "medium"
    return RiskResult(
        tier=tier,
        tier_name=TIER_NAMES[tier],
        approval_required=approval,
        signals=list(dict.fromkeys(signals)),
        required_controls=_controls_for(tier, signals),
        confidence=confidence,
    )

def main() -> int:
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--text")
    group.add_argument("--text-file")
    ap.add_argument("--changed-file", action="append", default=[])
    ap.add_argument("--flag", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    text = ns.text if ns.text is not None else Path(ns.text_file).read_text(encoding="utf-8")
    result = classify(text, ns.changed_file, ns.flag)
    payload = asdict(result)
    if ns.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"Risk Tier: {result.tier} ({result.tier_name})")
        print(f"Approval required: {'yes' if result.approval_required else 'no'}")
        print("Signals: " + (", ".join(result.signals) if result.signals else "none"))
        print("Controls: " + ", ".join(result.required_controls))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
