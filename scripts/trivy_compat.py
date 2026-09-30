#!/usr/bin/env python3
"""Contract-test Trivy via its official container image."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "toolchain.json"


def skill_version() -> str:
    version_file = ROOT / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    skill_file = ROOT / "SKILL.md"
    if skill_file.exists():
        match = re.search(
            r'(?m)^  version:\s*"([^"]+)"\s*$',
            skill_file.read_text(encoding="utf-8"),
        )
        if match:
            return match.group(1)
    return "portable"


def latest_release() -> str:
    req = urllib.request.Request(
        "https://api.github.com/repos/aquasecurity/trivy/releases/latest",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"Vibe-Coding-Skill/{skill_version()}",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)["tag_name"].lstrip("v")


def run(cmd: list[str], cwd: Path, timeout: int = 300) -> tuple[bool, str]:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    out = ((p.stdout or "") + "\n" + (p.stderr or "")).strip()
    return p.returncode == 0, out[-4000:]


def detected_version(executable: str) -> str | None:
    ok, out = run([executable, "--version"], ROOT, timeout=60)
    if not ok:
        return None
    match = re.search(r"\b(\d+\.\d+(?:\.\d+)?)\b", out)
    return match.group(1) if match else None


def contract_test(version: str) -> dict[str, object]:
    native = shutil.which("trivy")
    use_native = bool(native and detected_version(native) == version)
    image = f"aquasec/trivy:{version}"
    if not use_native and not shutil.which("docker"):
        raise RuntimeError(
            f"Trivy {version} compatibility testing requires either a matching "
            "native trivy executable or Docker"
        )

    checks = []
    if use_native:
        assert native is not None
        ok, out = run([native, "--version"], ROOT)
        checks.append({"command": f"{native} --version", "ok": ok, "output": out})
    else:
        ok, out = run(["docker", "run", "--rm", image, "--version"], ROOT)
        checks.append({"command": f"{image} --version", "ok": ok, "output": out})
    if not ok:
        return {"version": version, "ok": False, "checks": checks}

    with tempfile.TemporaryDirectory(prefix="vibe-trivy-") as td:
        fixture = Path(td)
        (fixture / "app.txt").write_text("ordinary test fixture\n", encoding="utf-8")
        if use_native:
            assert native is not None
            cmd = [
                native,
                "fs",
                "--scanners",
                "secret",
                "--format",
                "json",
                str(fixture.resolve()),
            ]
        else:
            mount = (
                f"type=bind,src={fixture.resolve()},dst=/workspace,readonly"
            )
            cmd = [
                "docker",
                "run",
                "--rm",
                "--mount",
                mount,
                image,
                "fs",
                "--scanners",
                "secret",
                "--format",
                "json",
                "/workspace",
            ]
        ok, out = run(cmd, ROOT)
        checks.append({"command": "secret scanner smoke test", "ok": ok, "output": out})
    return {
        "version": version,
        "ok": ok,
        "runtime": "native" if use_native else "docker",
        "checks": checks,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version")
    ap.add_argument("--latest", action="store_true")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    current = cfg["trivy"].get("last_known_good")
    if not ns.latest and not ns.version and not current:
        raise SystemExit("no Trivy version specified or last-known-good fallback")
    version = latest_release() if ns.latest else (ns.version or current)

    result = contract_test(version)
    result["last_known_good"] = current
    result["resolution"] = "latest-compatible-stable"
    if ns.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Trivy {version}: {'PASS' if result['ok'] else 'FAIL'}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
