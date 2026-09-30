#!/usr/bin/env python3
"""Build a reproducible portable ZIP and check the actual extracted installation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import sync_package

ROOT = Path(__file__).resolve().parents[1]


def build(output_dir: Path) -> dict:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version):
        raise ValueError("VERSION is not a semantic version")
    if sync_package.check():
        raise ValueError("portable package is out of sync")
    output_dir = output_dir.resolve()
    if output_dir.is_relative_to(ROOT):
        raise ValueError("release output must be outside the repository")
    sources = [(sync_package.TARGET / rel, rel) for rel in sync_package.expected_files()]
    sources += [(ROOT / name, Path(name)) for name in ("VERSION", "LICENSE")]
    for source, rel in sources:
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"unsafe or missing release source: {rel}")
        if rel.is_absolute() or ".." in rel.parts or "\\" in rel.as_posix():
            raise ValueError(f"unsafe archive path: {rel}")
        if any(parent.is_symlink() for parent in source.parents if parent != ROOT.parent):
            raise ValueError(f"symlink in release source path: {rel}")
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"Vibe-Coding-Skill-{version}.zip"
    with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=9) as package:
        for source, rel in sorted(sources, key=lambda item: item[1].as_posix()):
            entry = ZipInfo("vibe-coding-skill/" + rel.as_posix(), (1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            entry.compress_type = ZIP_DEFLATED
            # Runtime files are UTF-8 text; canonical LF makes OS checkouts equivalent.
            package.writestr(entry, source.read_bytes().replace(b"\r\n", b"\n"), compresslevel=9)
    with tempfile.TemporaryDirectory(prefix="vibe-release-") as temporary:
        installed = Path(temporary) / "vibe-coding-skill"
        with ZipFile(archive) as package:
            package.extractall(temporary)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        check = subprocess.run(
            [sys.executable, str(installed / "scripts/install_check.py"),
             "--skill-root", str(installed), "--json"],
            capture_output=True, text=True, encoding="utf-8", env=env, timeout=120,
        )
        if check.returncode:
            raise ValueError("extracted installation check failed: " + check.stdout + check.stderr)
        installation = json.loads(check.stdout)
        if installation.get("failures") or installation.get("status") not in ("PASS", "WARN"):
            raise ValueError("extracted installation did not pass its required checks")
        if installation.get("skill", {}).get("version") != version:
            raise ValueError("extracted Skill version does not match VERSION")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksums = output_dir / f"Vibe-Coding-Skill-{version}-SHA256SUMS.txt"
    checksums.write_text(f"{digest}  {archive.name}\n", encoding="utf-8", newline="\n")
    catalog = (ROOT / "UPDATES.md").read_text(encoding="utf-8")
    section = re.search(r"(?ms)^## " + re.escape(version) + r"\b.*?(?=^## |\Z)", catalog)
    if not section:
        raise ValueError("UPDATES.md requires an entry for the release version")
    notes = section.group(0).strip() + "\n\n" + (
        "Download the portable ZIP and extract its `vibe-coding-skill` directory into "
        "your agent's user-level skills directory. Keep it outside product repositories. "
        "Python 3.10+ and Git are required.\n\n"
        "Run `python scripts/install_check.py --skill-root . --json` from the extracted "
        "directory. Optional tool warnings do not mean the installation failed.\n\n"
        "Verify the ZIP using the attached SHA-256 checksum file. GitHub's source "
        "archives contain the full maintainer repository.\n"
    )
    (output_dir / "release-notes.md").write_text(notes, encoding="utf-8", newline="\n")
    return {
        "version": version, "archive": archive.name, "sha256": digest,
        "files": len(sources), "bytes": archive.stat().st_size,
        "installation_status": installation["status"],
        "installation_warnings": installation.get("warnings", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = build(args.output_dir)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"Release package failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2) if args.json else f"Built {result['archive']} ({result['files']} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
