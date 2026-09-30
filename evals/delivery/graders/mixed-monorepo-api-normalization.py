import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

EXPECTED_STORE_SHA256 = "1c5addd2ff0642999b30551add48c9bcc869fdbbf61657fba1af52e8c72bdb17"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("fixture_api_service", path)
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
        module = load_module(root / "apps" / "api" / "service.py")
        module.CUSTOMERS.clear()
        customer = module.create_customer(" User@Example.COM ")
        behavior_ok = (
            customer["email"] == "user@example.com"
            and module.CUSTOMERS == [{"email": "user@example.com"}]
        )
        detail = repr(module.CUSTOMERS)
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"

    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "apps/api/tests"],
        cwd=root,
        text=True,
        capture_output=True,
    )

    store_path = root / "apps" / "store" / "service.py"
    store_hash = hashlib.sha256(store_path.read_bytes()).hexdigest() if store_path.exists() else ""
    store_ok = store_hash == EXPECTED_STORE_SHA256

    result = {
        "schema_version": 1,
        "checks": [
            {
                "id": "api-email-normalized",
                "category": "functional",
                "required": True,
                "passed": behavior_ok,
                "details": detail,
            },
            {
                "id": "api-regression-tests",
                "category": "regression",
                "required": True,
                "passed": tests.returncode == 0,
                "details": tests.stdout + tests.stderr,
            },
            {
                "id": "store-sibling-unchanged",
                "category": "forbidden-mutation",
                "required": True,
                "passed": store_ok,
                "details": store_hash,
            },
        ],
        "metrics": {},
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
