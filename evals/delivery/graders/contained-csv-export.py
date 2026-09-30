import argparse
import csv
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("fixture_reports", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args()
    root = Path(ns.workspace)

    behavior_ok = False
    detail = ""
    try:
        module = load_module(root / "reports.py")
        output = module.export_csv([
            {"id": "1", "name": "Ada, Lovelace"},
            {"id": "2", "name": 'Grace "Amazing" Hopper'},
        ])
        rows = list(csv.reader(io.StringIO(output)))
        behavior_ok = rows == [
            ["id", "name"],
            ["1", "Ada, Lovelace"],
            ["2", 'Grace "Amazing" Hopper'],
        ]
        detail = repr(rows)
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"

    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    result = {
        "schema_version": 1,
        "checks": [
            {
                "id": "csv-roundtrip",
                "category": "functional",
                "required": True,
                "passed": behavior_ok,
                "details": detail,
            },
            {
                "id": "existing-report-tests",
                "category": "regression",
                "required": True,
                "passed": tests.returncode == 0,
                "details": tests.stdout + tests.stderr,
            },
        ],
        "metrics": {},
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
