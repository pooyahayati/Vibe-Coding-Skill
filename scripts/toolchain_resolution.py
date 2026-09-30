#!/usr/bin/env python3
"""Resolve managed external tools to the latest compatible stable release."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "toolchain.json"
SUPPORTED = {"graphify": "scripts/graphify_compat.py", "trivy": "scripts/trivy_compat.py"}


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def validate_config(config: dict[str, Any], tool: str) -> dict[str, Any]:
    entry = config.get(tool)
    if not isinstance(entry, dict):
        raise ValueError(f"missing toolchain entry: {tool}")
    if entry.get("channel") != "stable":
        raise ValueError(f"{tool}: channel must be stable")
    if entry.get("resolution") != "latest-compatible-stable":
        raise ValueError(f"{tool}: unsupported resolution policy")
    if not entry.get("last_known_good"):
        raise ValueError(f"{tool}: last_known_good is required as compatibility fallback")
    return entry


def contract(tool: str, version: str | None = None) -> dict[str, Any]:
    script = ROOT / SUPPORTED[tool]
    cmd = ["python", str(script)]
    if version:
        cmd += ["--version", version]
    else:
        cmd += ["--latest"]
    cmd += ["--json"]
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=900)
    output = (p.stdout or "").strip()
    if not output:
        raise RuntimeError(f"{tool} compatibility command returned no JSON")
    try:
        result = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{tool} compatibility command returned invalid JSON: {exc}") from exc
    result["command_ok"] = p.returncode == 0
    return result


def resolve(tool: str, config: dict[str, Any]) -> dict[str, Any]:
    entry = validate_config(config, tool)
    candidate = contract(tool)
    if candidate.get("ok"):
        return {
            "tool": tool,
            "resolution": entry["resolution"],
            "channel": entry["channel"],
            "selected_version": candidate["version"],
            "source": "latest-compatible-stable",
            "fallback_used": False,
            "candidate": candidate,
        }

    fallback_version = str(entry["last_known_good"])
    fallback = contract(tool, fallback_version)
    if not fallback.get("ok"):
        raise RuntimeError(
            f"{tool}: latest stable candidate failed compatibility and last-known-good "
            f"{fallback_version} also failed compatibility"
        )
    return {
        "tool": tool,
        "resolution": entry["resolution"],
        "channel": entry["channel"],
        "selected_version": fallback_version,
        "source": "last-known-good",
        "fallback_used": True,
        "candidate": candidate,
        "fallback": fallback,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tool", choices=sorted(SUPPORTED))
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    try:
        result = resolve(ns.tool, load_config())
    except (OSError, ValueError, RuntimeError) as exc:
        result = {"ok": False, "tool": ns.tool, "error": str(exc)}
        if ns.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"ERROR: {exc}")
        return 2
    result["ok"] = True
    if ns.json:
        print(json.dumps(result, indent=2))
    else:
        suffix = " (fallback)" if result["fallback_used"] else ""
        print(f"{ns.tool}: {result['selected_version']}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
