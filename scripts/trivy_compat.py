#!/usr/bin/env python3
"""Check Trivy compatibility or gate a release with the installed native scanner."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "toolchain.json"


def local_readiness() -> dict[str, object]:
    """Planning preflight only; presence is not release security evidence."""
    try:
        executable = shutil.which("trivy")
        version = detected_version(executable) if executable else None
        if not version:
            raise RuntimeError("install a verified native Trivy executable on PATH before publication")
        return {"gate": "PASS", "runtime": "native", "version": version,
                "release_scan_verified": False}
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return {"gate": "BLOCK", "release_scan_verified": False,
                "failures": [str(exc) if isinstance(exc, RuntimeError) else "native Trivy cannot execute"]}


def release_findings(report: dict, target: str, target_type: str) -> dict[str, int]:
    """Inspect actual JSON findings; an exit-zero scan is not a clean scan."""
    if (not isinstance(report, dict) or type(report.get("SchemaVersion")) is not int
            or report["SchemaVersion"] != 2 or report.get("ArtifactName") != target
            or report.get("ArtifactType") != {"fs": "filesystem", "image": "container_image"}[target_type]):
        raise ValueError("invalid Trivy report or target binding")
    results = report.get("Results", [])  # Trivy omits an empty Results collection.
    if not isinstance(results, list):
        raise ValueError("invalid Trivy results")
    counts = {"blocking": 0, "other": 0}
    for result in results:
        if not isinstance(result, dict):
            raise ValueError("invalid Trivy result")
        for key in ("Vulnerabilities", "Secrets", "Misconfigurations"):
            findings = result.get(key, [])
            if not isinstance(findings, list):
                raise ValueError("invalid Trivy findings")
            for finding in findings:
                if not isinstance(finding, dict) or finding.get("Severity") not in {
                        "UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"}:
                    raise ValueError("invalid Trivy finding severity")
                if key == "Misconfigurations" and finding.get("Status") == "PASS":
                    continue
                blocked = key == "Secrets" or finding["Severity"] in {"HIGH", "CRITICAL"}
                counts["blocking" if blocked else "other"] += 1
    return counts


def release_scan(target: str, output: Path, *, target_type: str = "fs",
                 scanners: str = "vuln,secret", version: str | None = None,
                 timeout: int = 300) -> dict[str, object]:
    """Run a native, local release check; never replace it with Docker or stale JSON."""
    result: dict[str, object] = {"gate": "BLOCK", "runtime": "native",
                               "release_scan_verified": False, "failures": []}
    try:
        ready = local_readiness()
        if ready["gate"] != "PASS":
            return dict(result, failures=ready["failures"])
        selected = version or latest_release()
        if ready["version"] != selected:
            raise ValueError("installed Trivy must match the resolved stable version; update before publication")
        selected_scanners = scanners.split(",")
        if (target_type not in {"fs", "image"} or not selected_scanners
                or len(set(selected_scanners)) != len(selected_scanners)
                or set(selected_scanners) - {"vuln", "secret", "misconfig"}
                or "secret" not in selected_scanners or timeout <= 0):
            raise ValueError("release scans require secret scanning and supported, relevant scanners")
        output = output.expanduser().resolve()
        if output.is_relative_to(ROOT):
            raise ValueError("security report/cache must stay outside the Skill repository")
        if target_type == "fs":
            scan_root = Path(target).expanduser().resolve()
            if not scan_root.is_dir():
                raise ValueError("filesystem release target must be a prepared directory, not a ZIP")
            if output.is_relative_to(scan_root):
                raise ValueError("security report/cache must stay outside the scanned source")
            target = str(scan_root)
        elif not re.fullmatch(r"(?:[^\s]+@)?sha256:[0-9a-f]{64}", target):
            raise ValueError("release image must be bound to an immutable sha256 identity")
        output.parent.mkdir(parents=True, exist_ok=True)
        # Fresh output and a clean working directory prevent stale reports and
        # implicit project ignore/config files from manufacturing a clean scan.
        with tempfile.TemporaryDirectory(prefix="trivy-release-", dir=output.parent) as td:
            work = Path(td)
            report_file = work / "scan.json"
            (work / "empty.yaml").write_text("{}\n", encoding="utf-8")
            (work / "empty.ignore").write_text("", encoding="utf-8")
            cmd = [shutil.which("trivy"), target_type, "--scanners", scanners,
                   "--format", "json", "--output", str(report_file),
                   "--exit-code", "0", "--severity", "UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL",
                   "--config", str(work / "empty.yaml"), "--ignorefile", str(work / "empty.ignore"),
                   "--cache-dir", str(output.parent / "trivy-cache"),
                   "--skip-db-update=false", "--skip-java-db-update=false", "--skip-check-update=false",
                   target]
            env = {k: v for k, v in os.environ.items() if not k.upper().startswith("TRIVY_")}
            process = subprocess.run(cmd, cwd=work, env=env, text=True, capture_output=True, timeout=timeout)
            if process.returncode != 0:
                raise ValueError("Trivy scan/data update failed; no release success claimed")
            report = json.loads(report_file.read_text(encoding="utf-8"))
            counts = release_findings(report, target, target_type)
            digest = hashlib.sha256(report_file.read_bytes()).hexdigest()
            report_file.chmod(0o600)
            report_file.replace(output)
        warnings = []
        if counts["other"] or "WARN" in (process.stderr or ""):
            warnings.append("Head must assess lower-severity findings and scanner coverage warnings")
        result.update({"gate": "BLOCK" if counts["blocking"] else ("WARN" if warnings else "PASS"),
                       "release_scan_verified": True, "version": selected, "target": target,
                       "scanners": selected_scanners, "report": str(output), "report_sha256": digest,
                       "findings": counts, "warnings": warnings,
                       "failures": ["resolve blocking vulnerabilities, misconfigurations or detected secrets"]
                       if counts["blocking"] else []})
    except ValueError as exc:
        result["failures"] = [str(exc) if type(exc) is ValueError else "Trivy returned invalid JSON; no release success claimed"]
    except (OSError, RuntimeError, KeyError, TypeError, subprocess.TimeoutExpired):
        result["failures"] = ["native release scan unavailable, incomplete or invalid; inspect local setup/target/data access"]
    return result


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


def trivy_runtime(version: str) -> tuple[str, str]:
    native = shutil.which("trivy")
    if native and detected_version(native) == version:
        return "native", native
    if shutil.which("docker"):
        return "docker", "docker"
    raise RuntimeError(
        f"Trivy {version} compatibility testing requires either a matching "
        "native trivy executable or Docker"
    )


def contract_test(version: str) -> dict[str, object]:
    runtime, executable = trivy_runtime(version)
    use_native = runtime == "native"
    native = executable if use_native else None
    image = f"aquasec/trivy:{version}"

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
    ap.add_argument("--check-local", action="store_true", help="planning preflight; not scan evidence")
    ap.add_argument("--release-target", help="actual prepared release directory or image reference")
    ap.add_argument("--target-type", choices=("fs", "image"), default="fs")
    ap.add_argument("--scanners", default="vuln,secret")
    ap.add_argument("--output", type=Path, help="private local report outside product source")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()

    if ns.check_local or ns.release_target:
        if ns.check_local and ns.release_target or ns.release_target and not ns.output:
            ap.error("choose preflight or release scan; release scan requires --output")
        result = local_readiness() if ns.check_local else release_scan(
            ns.release_target, ns.output, target_type=ns.target_type,
            scanners=ns.scanners, version=ns.version, timeout=ns.timeout)
        print(json.dumps(result, indent=2) if ns.json else f"Trivy release gate: {result['gate']}")
        return 2 if result["gate"] == "BLOCK" else 0

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
