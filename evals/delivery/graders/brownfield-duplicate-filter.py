import argparse
import ast
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("fixture_filters", path)
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
        module = load_module(root / "app" / "filters.py")
        store = module.FilterStore()
        store.save("open-orders")
        store.save("open-orders")
        behavior_ok = store.all() == ["open-orders"]
        detail = repr(store.all())
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"

    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=root,
        text=True,
        capture_output=True,
    )

    test_path = root / "tests" / "test_filters.py"
    regression_test_ok = False
    try:
        source = test_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        methods = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        ]
        regression_test_ok = len(methods) >= 2 and source.count(".save(") >= 3
    except Exception:
        pass

    result = {
        "schema_version": 1,
        "checks": [
            {
                "id": "duplicate-is-idempotent",
                "category": "functional",
                "required": True,
                "passed": behavior_ok,
                "details": detail,
            },
            {
                "id": "existing-and-new-tests-pass",
                "category": "regression",
                "required": True,
                "passed": tests.returncode == 0,
                "details": tests.stdout + tests.stderr,
            },
            {
                "id": "focused-regression-test-added",
                "category": "regression",
                "required": True,
                "passed": regression_test_ok,
                "details": "requires at least two test methods and duplicate-save exercise",
            },
        ],
        "metrics": {},
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
