#!/usr/bin/env python3
"""Contract-test Trivy via its official container image."""

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


def latest_release() -> str:
    req = urllib.request.Request(
        "https://api.github.com/repos/aquasecurity/trivy/releases/latest",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "Vibe-Coding-Skill/0.3.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)["tag_name"].lstrip("v")


def run(cmd: list[str], cwd: Path, timeout: int = 300) -> tuple[bool, str]:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    out = ((p.stdout or "") + "\n" + (p.stderr or "")).strip()
    return p.returncode == 0, out[-4000:]


def contract_test(version: str) -> dict[str, object]:
    if not shutil.which("docker"):
        raise RuntimeError("Docker is required for Trivy compatibility testing")

    image = f"aquasec/trivy:{version}"
    checks = []
    ok, out = run(["docker", "run", "--rm", image, "--version"], ROOT)
    checks.append({"command": f"{image} --version", "ok": ok, "output": out})
    if not ok:
        return {"version": version, "ok": False, "checks": checks}

    with tempfile.TemporaryDirectory(prefix="vibe-trivy-") as td:
        fixture = Path(td)
        (fixture / "app.txt").write_text("ordinary test fixture\n", encoding="utf-8")
        mount = f"{fixture.resolve()}:/workspace:ro"
        ok, out = run([
            "docker", "run", "--rm", "-v", mount, image,
            "fs", "--scanners", "secret", "--format", "json", "/workspace",
        ], ROOT)
        checks.append({"command": "secret scanner smoke test", "ok": ok, "output": out})
    return {"version": version, "ok": ok, "checks": checks}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version")
    ap.add_argument("--latest", action="store_true")
    ap.add_argument("--update-approved", action="store_true")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    current = cfg["trivy"].get("approved")
    version = latest_release() if ns.latest else (ns.version or current)
    if not version:
        raise SystemExit("no Trivy version specified or approved")

    result = contract_test(version)
    result["previous_approved"] = current
    if result["ok"] and ns.update_approved and version != current:
        cfg["trivy"]["approved"] = version
        cfg["trivy"]["last_known_good"] = version
        cfg["trivy"]["latest_seen"] = version
        CONFIG.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        result["config_updated"] = True
    else:
        result["config_updated"] = False

    print(json.dumps(result, indent=2) if ns.json else f"Trivy {version}: {'PASS' if result['ok'] else 'FAIL'}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
