#!/usr/bin/env python3
"""Contract-test a Graphify release and optionally update the approved version."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "toolchain.json"


def latest_pypi_version() -> str:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    req = urllib.request.Request(
        "https://pypi.org/pypi/graphifyy/json",
        headers={"User-Agent": f"Vibe-Coding-Skill/{version}"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)["info"]["version"]


def run(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=180)
    out = ((p.stdout or "") + "\n" + (p.stderr or "")).strip()
    return p.returncode == 0, out[-4000:]


def contract_test(version: str) -> dict[str, object]:
    if not shutil.which("uvx"):
        raise RuntimeError("uvx is required for Graphify compatibility testing")

    package = f"graphifyy=={version}"
    checks: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="vibe-graphify-") as td:
        root = Path(td)
        (root / "sample.py").write_text(
            "def alpha():\n    return beta()\n\ndef beta():\n    return 42\n",
            encoding="utf-8",
        )

        commands = [
            ["uvx", "--from", package, "graphify", "--version"],
            ["uvx", "--from", package, "graphify", "extract", ".", "--code-only", "--no-viz"],
        ]
        for cmd in commands:
            ok, out = run(cmd, root)
            checks.append({"command": " ".join(cmd), "ok": ok, "output": out})
            if not ok:
                return {"version": version, "ok": False, "checks": checks}

        candidates = [root / "graphify-out" / "graph.json", root / "graph.json"]
        graph_path = next((p for p in candidates if p.exists()), None)
        if graph_path is None:
            checks.append({"command": "graph output", "ok": False, "output": "graph.json not found"})
            return {"version": version, "ok": False, "checks": checks}

        data = json.loads(graph_path.read_text(encoding="utf-8"))
        schema_ok = isinstance(data, (dict, list))
        checks.append({"command": "graph schema smoke check", "ok": schema_ok, "output": str(graph_path)})
        if not schema_ok:
            return {"version": version, "ok": False, "checks": checks}

        nodes = data.get("nodes", []) if isinstance(data, dict) else []
        labels = [
            str(node.get("label") or node.get("id"))
            for node in nodes
            if isinstance(node, dict) and (node.get("label") or node.get("id"))
        ]
        if len(labels) < 2:
            checks.append({"command": "graph node contract", "ok": False, "output": "expected at least two labeled nodes"})
            return {"version": version, "ok": False, "checks": checks}

        graph_arg = str(graph_path.resolve())
        adapter_commands = [
            ["uvx", "--from", package, "graphify", "query", "alpha", "--graph", graph_arg],
            ["uvx", "--from", package, "graphify", "explain", labels[0], "--graph", graph_arg],
            ["uvx", "--from", package, "graphify", "path", labels[0], labels[1], "--graph", graph_arg],
        ]
        for cmd in adapter_commands:
            ok, out = run(cmd, root)
            checks.append({"command": " ".join(cmd), "ok": ok, "output": out})
            if not ok:
                return {"version": version, "ok": False, "checks": checks}

        (root / "sample.py").write_text(
            "def alpha():\n    return beta()\n\ndef beta():\n    return 43\n",
            encoding="utf-8",
        )
        update_cmd = ["uvx", "--from", package, "graphify", "update", "."]
        ok, out = run(update_cmd, root)
        checks.append({"command": " ".join(update_cmd), "ok": ok, "output": out})
        return {"version": version, "ok": bool(ok), "checks": checks}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version")
    ap.add_argument("--latest", action="store_true")
    ap.add_argument("--update-approved", action="store_true")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    current = cfg["graphify"]["approved"]
    version = latest_pypi_version() if ns.latest else (ns.version or current)

    result = contract_test(version)
    result["previous_approved"] = current

    if result["ok"] and ns.update_approved and version != current:
        cfg["graphify"]["approved"] = version
        cfg["graphify"]["last_known_good"] = version
        cfg["graphify"]["latest_seen"] = version
        CONFIG.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        result["config_updated"] = True
    else:
        result["config_updated"] = False

    if ns.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Graphify {version}: {'PASS' if result['ok'] else 'FAIL'}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
