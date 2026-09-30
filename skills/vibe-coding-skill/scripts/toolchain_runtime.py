#!/usr/bin/env python3
"""Resolve and invoke exact managed toolchain versions for an execution session."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from . import toolchain_resolution
except ImportError:  # direct script execution from the portable package
    import toolchain_resolution

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class ToolchainSession:
    """Explicit execution-scoped owner of resolved managed-tool versions."""

    pins: dict[str, dict[str, Any]] = field(default_factory=dict)

    def resolve(self, tool: str) -> dict[str, Any]:
        if tool in self.pins:
            return dict(self.pins[tool])

        session_key = f"VIBE_TOOLCHAIN_{tool.upper()}_SESSION_VERSION"
        session_version = os.environ.get(session_key, "").strip()
        if session_version:
            resolved = {
                "tool": tool,
                "selected_version": session_version,
                "source": "environment-session-pin",
                "fallback_used": False,
                "contract_verified": False,
            }
        else:
            resolved = toolchain_resolution.resolve(
                tool,
                toolchain_resolution.load_config(),
            )
            resolved = dict(resolved)
            resolved["contract_verified"] = True

        self.pins[tool] = resolved
        return dict(resolved)

    def selected_version(self, tool: str) -> str | None:
        row = self.pins.get(tool)
        return str(row["selected_version"]) if row else None


def new_session() -> ToolchainSession:
    return ToolchainSession()


def resolve(
    tool: str,
    session: ToolchainSession | None = None,
) -> dict[str, Any]:
    """Resolve a tool.

    Without an explicit session this is intentionally a one-shot resolution.
    Compound operations must create one ToolchainSession and pass it through.
    """
    if session is not None:
        return session.resolve(tool)

    session_key = f"VIBE_TOOLCHAIN_{tool.upper()}_SESSION_VERSION"
    session_version = os.environ.get(session_key, "").strip()
    if session_version:
        return {
            "tool": tool,
            "selected_version": session_version,
            "source": "environment-session-pin",
            "fallback_used": False,
            "contract_verified": False,
        }
    resolved = dict(
        toolchain_resolution.resolve(tool, toolchain_resolution.load_config())
    )
    resolved["contract_verified"] = True
    return resolved


def version_from_output(output: str) -> str | None:
    import re

    match = re.search(r"\b(\d+\.\d+(?:\.\d+)?)\b", output)
    return match.group(1) if match else None


def matching_native(tool: str, version: str) -> str | None:
    executable = shutil.which(tool)
    if not executable:
        return None
    rc = subprocess.run(
        [executable, "--version"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
    )
    detected = version_from_output((rc.stdout or "") + "\n" + (rc.stderr or ""))
    return executable if rc.returncode == 0 and detected == version else None


def graphify_command(version: str, args: list[str]) -> list[str]:
    executable = matching_native("graphify", version)
    if executable:
        return [executable, *args]
    if not shutil.which("uvx"):
        raise RuntimeError(
            f"Graphify {version} is required but no matching graphify executable "
            "or uvx runtime is available"
        )
    return ["uvx", "--from", f"graphifyy=={version}", "graphify", *args]


def trivy_command(version: str, args: list[str]) -> list[str]:
    """Build a generic Trivy command for non-host-filesystem targets."""
    if args and args[0] == "fs":
        raise ValueError(
            "host filesystem scans must use trivy_fs_command() so the target "
            "is explicitly mapped into the container runtime"
        )
    executable = matching_native("trivy", version)
    if executable:
        return [executable, *args]
    if not shutil.which("docker"):
        raise RuntimeError(
            f"Trivy {version} is required but no matching trivy executable "
            "or Docker runtime is available"
        )
    return ["docker", "run", "--rm", f"aquasec/trivy:{version}", *args]


def docker_bind_mount(
    host_path: str | Path,
    container_path: str = "/workspace",
) -> str:
    """Return one Docker --mount argv value without shell quoting."""
    host_text = str(host_path)
    return (
        f"type=bind,src={host_text},dst={container_path},readonly"
    )


def trivy_fs_command(
    version: str,
    target: str | Path,
    args: list[str] | None = None,
) -> list[str]:
    """Build an exact-version filesystem scan with a real host-path mapping."""
    executable = matching_native("trivy", version)
    host = Path(target).expanduser().resolve()
    scan_args = list(args or [])

    if executable:
        return [executable, "fs", *scan_args, str(host)]

    if not shutil.which("docker"):
        raise RuntimeError(
            f"Trivy {version} filesystem scan requires a matching native Trivy "
            "or Docker runtime"
        )

    # --mount is one argv entry, so spaces stay intact. Docker Desktop accepts
    # native absolute Windows paths in src= on Windows.
    mount = docker_bind_mount(host)
    return [
        "docker",
        "run",
        "--rm",
        "--mount",
        mount,
        f"aquasec/trivy:{version}",
        "fs",
        *scan_args,
        "/workspace",
    ]


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
    session = new_session()
    try:
        resolved = (
            session.resolve(ns.tool)
            if not ns.version
            else {
                "selected_version": ns.version,
                "source": "explicit",
                "contract_verified": False,
            }
        )
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
        "contract_verified": resolved.get("contract_verified"),
        "command": cmd,
    }
    print(json.dumps(result, indent=2) if ns.json else " ".join(cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
