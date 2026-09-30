#!/usr/bin/env python3
"""Build and verify installable WordPress plugin artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

HEADER_FIELDS = {
    "plugin_name": "Plugin Name",
    "version": "Version",
    "requires_at_least": "Requires at least",
    "requires_php": "Requires PHP",
    "text_domain": "Text Domain",
    "wc_requires_at_least": "WC requires at least",
    "wc_tested_up_to": "WC tested up to",
}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
VCS_PARTS = {".git", ".hg", ".svn", "__pycache__"}


def header_value(text: str, label: str) -> str:
    pattern = re.compile(
        rf"(?mi)^[ \t/*#@-]*{re.escape(label)}\s*:\s*(.+?)\s*$"
    )
    match = pattern.search(text)
    if not match:
        return ""
    return match.group(1).strip().rstrip("*/").strip()


def parse_headers(text: str) -> dict[str, str]:
    return {
        key: header_value(text, label)
        for key, label in HEADER_FIELDS.items()
    }


def read_headers(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="ignore")[:8192]
    return parse_headers(text)


def contained(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def discover_main_file(
    root: Path,
    explicit: str | None = None,
) -> tuple[Path, dict[str, str]]:
    root = root.resolve()
    if explicit:
        candidate = (root / explicit).resolve()
        if not contained(root, candidate):
            raise ValueError("main plugin file must stay inside source root")
        if not candidate.is_file():
            raise ValueError(f"main plugin file does not exist: {explicit}")
        headers = read_headers(candidate)
        if not headers["plugin_name"]:
            raise ValueError(
                f"main plugin file has no Plugin Name header: {explicit}"
            )
        return candidate, headers

    candidates: list[tuple[Path, dict[str, str]]] = []
    for candidate in sorted(root.glob("*.php")):
        headers = read_headers(candidate)
        if headers["plugin_name"]:
            candidates.append((candidate, headers))
    if len(candidates) != 1:
        raise ValueError(
            "source root must contain exactly one root-level PHP file with "
            "a Plugin Name header, or pass --main-file"
        )
    return candidates[0]


def inspect_source(
    root: Path,
    main_file: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"source root is not a directory: {root}")
    main, headers = discover_main_file(root, main_file)
    if not headers["version"]:
        raise ValueError("plugin Version header is required for delivery")
    return {
        "source_root": str(root),
        "main_file": main.relative_to(root).as_posix(),
        **headers,
    }


def normalized_slug(value: str) -> str:
    slug = value.strip().lower()
    if not SLUG_RE.fullmatch(slug):
        raise ValueError(
            "plugin slug must use lowercase letters, digits, dot, dash, or underscore"
        )
    return slug


def source_files(root: Path, output: Path | None = None) -> list[Path]:
    files: list[Path] = []
    output_resolved = output.resolve() if output else None
    for path in sorted(root.rglob("*")):
        if not path.is_file() and not path.is_symlink():
            continue
        rel = path.relative_to(root)
        if any(part in VCS_PARTS for part in rel.parts):
            continue
        if output_resolved and path.resolve() == output_resolved:
            continue
        if path.is_symlink():
            raise ValueError(
                f"refusing to package symlink from delivery source: {rel.as_posix()}"
            )
        files.append(path)
    if not files:
        raise ValueError("delivery source contains no packageable files")
    return files


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (0o100644 & 0xFFFF) << 16
    return info


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_artifact(
    source_root: Path,
    output: Path,
    slug: str | None = None,
    main_file: str | None = None,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    source = inspect_source(source_root, main_file)
    archive_slug = normalized_slug(slug or source_root.name)
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    files = source_files(source_root, output)
    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in files:
            rel = path.relative_to(source_root).as_posix()
            archive.writestr(
                zip_info(f"{archive_slug}/{rel}"),
                path.read_bytes(),
            )

    result = inspect_artifact(output)
    if result["slug"] != archive_slug:
        raise RuntimeError("artifact slug changed during packaging")
    if result["version"] != source["version"]:
        raise RuntimeError("artifact Version header changed during packaging")
    result.update(
        {
            "source_root": str(source_root),
            "artifact": str(output),
            "artifact_sha256": sha256(output),
            "file_count": len(files),
        }
    )
    return result


def safe_member_parts(name: str) -> tuple[str, ...]:
    if "\\" in name:
        raise ValueError(f"artifact contains non-portable zip path: {name}")
    value = PurePosixPath(name)
    if value.is_absolute() or any(part in {"", ".", ".."} for part in value.parts):
        raise ValueError(f"artifact contains unsafe zip path: {name}")
    return value.parts


def is_zip_symlink(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0o170000
    return mode == stat.S_IFLNK


def inspect_artifact(artifact: Path) -> dict[str, Any]:
    artifact = artifact.resolve()
    if not artifact.is_file():
        raise ValueError(f"artifact does not exist: {artifact}")
    if not zipfile.is_zipfile(artifact):
        raise ValueError("artifact is not a valid ZIP file")

    with zipfile.ZipFile(artifact) as archive:
        infos = [info for info in archive.infolist() if not info.is_dir()]
        if not infos:
            raise ValueError("artifact ZIP is empty")

        roots: set[str] = set()
        main_candidates: list[tuple[str, dict[str, str]]] = []
        for info in infos:
            parts = safe_member_parts(info.filename)
            roots.add(parts[0])
            if is_zip_symlink(info):
                raise ValueError(
                    f"artifact contains symlink entry: {info.filename}"
                )
            if (
                len(parts) == 2
                and parts[1].lower().endswith(".php")
            ):
                text = archive.read(info).decode("utf-8", "ignore")[:8192]
                headers = parse_headers(text)
                if headers["plugin_name"]:
                    main_candidates.append((info.filename, headers))

        if len(roots) != 1:
            raise ValueError(
                "installable plugin ZIP must contain exactly one top-level directory"
            )
        if len(main_candidates) != 1:
            raise ValueError(
                "artifact must contain exactly one root-level PHP file with "
                "a Plugin Name header"
            )

        main_name, headers = main_candidates[0]
        if not headers["version"]:
            raise ValueError("artifact plugin Version header is missing")

        return {
            "artifact": str(artifact),
            "slug": next(iter(roots)),
            "main_file": main_name,
            **headers,
            "entries": len(infos),
        }


def verify_artifact(
    artifact: Path,
    expected_slug: str | None = None,
    expected_version: str | None = None,
) -> dict[str, Any]:
    result = inspect_artifact(artifact)
    failures: list[str] = []
    if expected_slug and result["slug"] != normalized_slug(expected_slug):
        failures.append(
            f"slug mismatch: expected {expected_slug}, got {result['slug']}"
        )
    if expected_version and result["version"] != expected_version:
        failures.append(
            "version mismatch: expected "
            f"{expected_version}, got {result['version']}"
        )
    result.update(
        {
            "artifact_sha256": sha256(artifact.resolve()),
            "verified": not failures,
            "failures": failures,
        }
    )
    return result


def install_smoke(artifact: Path) -> dict[str, Any]:
    verified = verify_artifact(artifact)
    if not verified["verified"]:
        raise ValueError("; ".join(verified["failures"]))

    with tempfile.TemporaryDirectory(prefix="vibe-wp-install-") as td:
        plugins = Path(td) / "wp-content" / "plugins"
        plugins.mkdir(parents=True)
        with zipfile.ZipFile(artifact.resolve()) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                parts = safe_member_parts(info.filename)
                if is_zip_symlink(info):
                    raise ValueError(
                        f"artifact contains symlink entry: {info.filename}"
                    )
                destination = plugins.joinpath(*parts)
                if not contained(plugins, destination):
                    raise ValueError(
                        f"artifact extraction escaped plugin directory: {info.filename}"
                    )
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.read(info))

        installed_root = plugins / str(verified["slug"])
        if not installed_root.is_dir():
            raise RuntimeError("artifact did not install into one plugin directory")
        main_rel = PurePosixPath(str(verified["main_file"])).parts[1:]
        installed_main = installed_root.joinpath(*main_rel)
        headers = read_headers(installed_main)
        if headers["version"] != verified["version"]:
            raise RuntimeError("installed plugin version differs from ZIP header")

    return {
        **verified,
        "install_smoke": "pass",
        "installed_version": verified["version"],
    }


def run_wp(
    wp_bin: str,
    wordpress_root: Path,
    args: list[str],
    timeout: int = 180,
) -> dict[str, Any]:
    executable = shutil.which(wp_bin) if not Path(wp_bin).is_file() else wp_bin
    if not executable:
        raise RuntimeError(f"WP-CLI executable not found: {wp_bin}")
    command = [
        str(executable),
        f"--path={wordpress_root.resolve()}",
        *args,
    ]
    result = subprocess.run(
        command,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
    return {
        "command": command,
        "returncode": result.returncode,
        "output": output[-4000:],
    }


def require_wp_step(step: dict[str, Any], label: str) -> None:
    if int(step["returncode"]) != 0:
        raise RuntimeError(f"{label} failed: {step['output']}")


def plugin_version(
    wp_bin: str,
    wordpress_root: Path,
    slug: str,
) -> tuple[str, dict[str, Any]]:
    step = run_wp(
        wp_bin,
        wordpress_root,
        ["plugin", "get", slug, "--field=version"],
    )
    require_wp_step(step, "plugin version check")
    value = str(step["output"]).splitlines()[0].strip()
    return value, step


def runtime_check(
    artifact: Path,
    wordpress_root: Path,
    wp_bin: str = "wp",
    previous_artifact: Path | None = None,
    exercise_uninstall: bool = False,
    disposable_environment: bool = False,
) -> dict[str, Any]:
    current = verify_artifact(artifact)
    if not current["verified"]:
        raise ValueError("; ".join(current["failures"]))
    current_path = artifact.resolve()
    wordpress_root = wordpress_root.resolve()
    if not wordpress_root.is_dir():
        raise ValueError(
            f"WordPress root does not exist: {wordpress_root}"
        )

    previous: dict[str, Any] | None = None
    if previous_artifact:
        previous = verify_artifact(previous_artifact)
        if not previous["verified"]:
            raise ValueError("; ".join(previous["failures"]))
        if previous["slug"] != current["slug"]:
            raise ValueError("previous and current artifacts have different slugs")

    if exercise_uninstall and not disposable_environment:
        raise ValueError(
            "--exercise-uninstall requires --disposable-environment because "
            "uninstall may delete plugin-owned data"
        )

    steps: list[dict[str, Any]] = []
    slug = str(current["slug"])
    initial = run_wp(wp_bin, wordpress_root, ["plugin", "list", "--format=json"])
    require_wp_step(initial, "initial plugin state")
    try:
        installed_plugins = json.loads(str(initial["output"]))
    except (ValueError, TypeError) as exc:
        raise RuntimeError("initial plugin state is not valid JSON") from exc
    if not isinstance(installed_plugins, list) or not all(isinstance(item, dict) for item in installed_plugins):
        raise RuntimeError("initial plugin state must be a plugin array")
    plugin_present_before = any(item.get("name") == slug for item in installed_plugins)
    steps.append(initial)

    if previous_artifact and previous:
        step = run_wp(
            wp_bin,
            wordpress_root,
            [
                "plugin",
                "install",
                str(previous_artifact.resolve()),
                "--force",
                "--activate",
            ],
        )
        require_wp_step(step, "previous artifact install")
        steps.append(step)
        installed, version_step = plugin_version(
            wp_bin, wordpress_root, slug
        )
        steps.append(version_step)
        if installed != previous["version"]:
            raise RuntimeError(
                "previous artifact installed unexpected version: "
                f"{installed} != {previous['version']}"
            )

    step = run_wp(
        wp_bin,
        wordpress_root,
        [
            "plugin",
            "install",
            str(current_path),
            "--force",
            "--activate",
        ],
    )
    require_wp_step(step, "current artifact install")
    steps.append(step)

    installed, version_step = plugin_version(
        wp_bin, wordpress_root, slug
    )
    steps.append(version_step)
    if installed != current["version"]:
        raise RuntimeError(
            "installed artifact version differs from ZIP: "
            f"{installed} != {current['version']}"
        )

    for action in ("deactivate", "activate"):
        step = run_wp(
            wp_bin,
            wordpress_root,
            ["plugin", action, slug],
        )
        require_wp_step(step, f"plugin {action}")
        steps.append(step)

    uninstalled = False
    if exercise_uninstall:
        step = run_wp(
            wp_bin,
            wordpress_root,
            ["plugin", "deactivate", slug],
        )
        require_wp_step(step, "plugin deactivate before uninstall")
        steps.append(step)
        step = run_wp(
            wp_bin,
            wordpress_root,
            ["plugin", "uninstall", slug],
        )
        require_wp_step(step, "plugin uninstall")
        steps.append(step)
        uninstalled = True

    return {
        "ok": True,
        "slug": slug,
        "artifact": str(current_path),
        "artifact_sha256": current["artifact_sha256"],
        "embedded_version": current["version"],
        "previous_artifact": (
            str(previous_artifact.resolve())
            if previous_artifact
            else None
        ),
        "previous_artifact_sha256": (
            previous["artifact_sha256"] if previous else None
        ),
        "previous_version": previous["version"] if previous else None,
        "installed_version": installed,
        "fresh_install_checked": False,
        "fresh_plugin_install_checked": previous is None and not plugin_present_before,
        "plugin_present_before": plugin_present_before,
        "data_freshness_verified": False,
        "fresh_install_limitation": (
            "Plugin absence is checked. A generic helper cannot verify absence of "
            "plugin-owned data; full fresh-install evidence requires a known-clean "
            "fixture and project-specific data assertions."
        ),
        "upgrade_checked": previous is not None,
        "deactivate_reactivate_checked": True,
        "uninstall_checked": uninstalled,
        "steps": steps,
    }


def print_result(result: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for key, value in result.items():
            if key == "steps":
                continue
            print(f"{key}: {value}")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("inspect")
    p.add_argument("--source-root", default=".")
    p.add_argument("--main-file")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("package")
    p.add_argument("--source-root", default=".")
    p.add_argument("--output", required=True)
    p.add_argument("--slug")
    p.add_argument("--main-file")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("verify")
    p.add_argument("--artifact", required=True)
    p.add_argument("--expected-slug")
    p.add_argument("--expected-version")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("install-smoke")
    p.add_argument("--artifact", required=True)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("runtime-check")
    p.add_argument("--artifact", required=True)
    p.add_argument("--previous-artifact")
    p.add_argument("--wordpress-root", required=True)
    p.add_argument("--wp-bin", default="wp")
    p.add_argument("--exercise-uninstall", action="store_true")
    p.add_argument("--disposable-environment", action="store_true")
    p.add_argument("--json", action="store_true")

    ns = ap.parse_args()
    try:
        if ns.command == "inspect":
            result = inspect_source(
                Path(ns.source_root),
                ns.main_file,
            )
        elif ns.command == "package":
            result = package_artifact(
                Path(ns.source_root),
                Path(ns.output),
                ns.slug,
                ns.main_file,
            )
        elif ns.command == "verify":
            result = verify_artifact(
                Path(ns.artifact),
                ns.expected_slug,
                ns.expected_version,
            )
            if not result["verified"]:
                print_result(result, ns.json)
                return 2
        elif ns.command == "install-smoke":
            result = install_smoke(Path(ns.artifact))
        else:
            result = runtime_check(
                Path(ns.artifact),
                Path(ns.wordpress_root),
                ns.wp_bin,
                Path(ns.previous_artifact)
                if ns.previous_artifact
                else None,
                ns.exercise_uninstall,
                ns.disposable_environment,
            )
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        result = {"ok": False, "error": str(exc)}
        print_result(result, getattr(ns, "json", False))
        return 2

    print_result(result, ns.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
