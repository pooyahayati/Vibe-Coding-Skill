import argparse
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    root = Path(ns.workspace)

    admin_path = root / "sample-plugin" / "includes" / "admin.php"
    source = admin_path.read_text(encoding="utf-8") if admin_path.exists() else ""
    registration_ok = (
        "register_setting" in source
        and "sample_label" in source
        and "sanitize_text_field" in source
    )
    escaped_input_ok = (
        "sample_label" in source
        and "get_option" in source
        and "esc_attr" in source
        and "<input" in source
    )

    build = subprocess.run(
        [sys.executable, "build_plugin.py"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    zip_path = root / "dist" / "sample-plugin.zip"
    artifact_ok = False
    detail = build.stdout + build.stderr
    if build.returncode == 0 and zip_path.is_file():
        try:
            with ZipFile(zip_path) as archive:
                names = [name for name in archive.namelist() if name and not name.endswith("/")]
            tops = {name.split("/", 1)[0] for name in names}
            artifact_ok = (
                tops == {"sample-plugin"}
                and "sample-plugin/sample-plugin.php" in names
                and "sample-plugin/includes/admin.php" in names
                and all(name.startswith("sample-plugin/") for name in names)
            )
            detail = repr(names)
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"

    main_path = root / "sample-plugin" / "sample-plugin.php"
    header_ok = False
    if main_path.exists():
        main_source = main_path.read_text(encoding="utf-8")
        header_ok = (
            "Plugin Name: Sample Plugin" in main_source
            and "Version: 1.0.0" in main_source
        )

    result = {
        "schema_version": 1,
        "checks": [
            {
                "id": "setting-registered-and-sanitized",
                "category": "functional",
                "required": True,
                "passed": registration_ok,
                "details": "register_setting + sample_label + sanitize_text_field",
            },
            {
                "id": "setting-input-escaped",
                "category": "security",
                "required": True,
                "passed": escaped_input_ok,
                "details": "get_option + esc_attr + input",
            },
            {
                "id": "plugin-header-preserved",
                "category": "regression",
                "required": True,
                "passed": header_ok,
                "details": "plugin name/version header",
            },
            {
                "id": "installable-zip-shape",
                "category": "artifact",
                "required": True,
                "passed": artifact_ok,
                "details": detail,
            },
        ],
        "metrics": {},
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
