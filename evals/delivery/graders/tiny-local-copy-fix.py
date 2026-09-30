import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("fixture_app", path)
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

    try:
        value = load_module(root / "app.py").render_footer()
        exact = value == "Welcome to Acme."
        detail = repr(value)
    except Exception as exc:
        exact = False
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
                "id": "footer-exact",
                "category": "functional",
                "required": True,
                "passed": exact,
                "details": detail,
            },
            {
                "id": "focused-tests",
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
