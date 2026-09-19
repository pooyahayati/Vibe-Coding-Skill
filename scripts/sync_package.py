#!/usr/bin/env python3
"""Generate/check the portable Agent Plugin skill mirror from canonical root files."""

from __future__ import annotations

import argparse
import filecmp
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "skills" / "vibe-coding-skill"

RUNTIME_FILES = [
    Path("SKILL.md"),
    Path("config/toolchain.json"),
    Path("agents/openai.yaml"),
    Path("scripts/doctor.py"),
    Path("scripts/change_budget.py"),
    Path("scripts/bootstrap_project.py"),
    Path("scripts/dependency_guard.py"),
]

RUNTIME_DIRS = [
    Path("references"),
    Path("assets/templates"),
]


def expected_files() -> list[Path]:
    paths = list(RUNTIME_FILES)
    for directory in RUNTIME_DIRS:
        paths.extend(
            p.relative_to(ROOT)
            for p in sorted((ROOT / directory).rglob("*"))
            if p.is_file()
        )
    return paths


def check() -> int:
    problems: list[str] = []
    for rel in expected_files():
        src = ROOT / rel
        dst = TARGET / rel
        if not dst.exists():
            problems.append(f"missing: {dst.relative_to(ROOT)}")
        elif not filecmp.cmp(src, dst, shallow=False):
            problems.append(f"drift: {dst.relative_to(ROOT)}")
    if problems:
        print("Portable package is out of sync:")
        for problem in problems:
            print(f"- {problem}")
        print("Run: python scripts/sync_package.py --write")
        return 1
    print("Portable package is synchronized.")
    return 0


def write() -> int:
    for rel in expected_files():
        src = ROOT / rel
        dst = TARGET / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    print(f"Synchronized {len(expected_files())} files into {TARGET.relative_to(ROOT)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    ns = ap.parse_args()
    return check() if ns.check else write()


if __name__ == "__main__":
    raise SystemExit(main())
