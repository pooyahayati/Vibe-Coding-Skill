#!/usr/bin/env python3
"""Resolve and invoke an exact managed toolchain version for a runtime session."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

try:
    from . import toolchain_resolution
except ImportError:  # direct script execution from the portable package
    import toolchain_resolution

ROOT = Path(__file__).resolve().parents[1]


def resolve(tool: str) -> dict[str, Any]:
    session_key = f"VIBE_TOOLCHAIN_{tool.upper()}_SESSION_VERSION"
    session_version = os.environ.get(session_key, "").strip()
    if session_version:
        return {
            "tool": tool,
            "selected_version": session_version,
            "source": "session-pin",
            "fallback_used": False,
        }
    return toolchain_resolution.resolve(tool, toolchain_resolution.load_config())


def version_from_output(output: str) -> str | None:
    import re
    match = re.search(r"\b(\d+\.\d+(?:\.\d+)?)\b", output)
    return match.group(1) if match else None


def graphify_command(version: str, args: list[str]) -> list[str]:
    executable = shutil.which("graphify")
    if executable:
        rc = subprocess.run([executable, "--version"], cwd=ROOT, text=True, capture_output=True, timeout=60)
        detected = version_from_output((rc.stdout or "") + "\n" + (rc.stderr or ""))
        if rc.returncode == 0 and detected == version:
            return [executable, *args]
    if not shutil.which("uvx"):
        raise RuntimeError(
            f"Graphify {version} is required but no matching graphify executable or uvx runtime is available"
        )
    return ["uvx", "--from", f"graphifyy=={version}", "graphify", *args]


def trivy_command(version: str, args: list[str]) -> list[str]:
    executable = shutil.which("trivy")
    if executable:
        rc = subprocess.run([executable, "--version"], cwd=ROOT, text=True, capture_output=True, timeout=60)
        detected = version_from_output((rc.stdout or "") + "\n" + (rc.stderr or ""))
        if rc.returncode == 0 and detected == version:
            return [executable, *args]
    if not shutil.which("docker"):
        raise RuntimeError(
            f"Trivy {version} is required but no matching trivy executable or Docker runtime is available"
        )
    return ["docker", "run", "--rm", f"aquasec/trivy:{version}", *args]


def command(tool: str, version: str, args: list[str]) -> list[str]:
    if tool == "graphify":
        return graphify_command(version, args)
    if tool == "trivy":
        return trivy_command(version, args)
    raise ValueError(f"unsupported managed tool: {tool}")


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("tool", choices=("graphify", "trivy"))
    ap.add_argument("--version")
    ap.add_argument("--json", action="store_true")
    ns, args = ap.parse_known_args()
    try:
        resolved = resolve(ns.tool) if not ns.version else {"selected_version": ns.version, "source": "explicit"}
        cmd = command(ns.tool, str(resolved["selected_version"]), args)
    except (OSError, RuntimeError, ValueError) as exc:
        result = {"ok": False, "tool": ns.tool, "error": str(exc)}
        print(json.dumps(result, indent=2) if ns.json else f"ERROR: {exc}")
        return 2
    result = {
        "ok": True,
        "tool": ns.tool,
        "selected_version": resolved["selected_version"],
        "source": resolved.get("source"),
        "command": cmd,
    }
    print(json.dumps(result, indent=2) if ns.json else " ".join(cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
