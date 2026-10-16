#!/usr/bin/env python3
"""Maintainer publication/recovery after exact-revision CI and final-artifact Trivy."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


class GitHub:
    def __init__(self, repository):
        self.repository = repository
        self.prefix = "repos/" + repository

    def command(self, *args, missing=False):
        result = subprocess.run(["gh", *args], capture_output=True, timeout=120)
        if result.returncode:
            if missing and b"HTTP 404" in result.stderr:
                return None
            raise RuntimeError("GitHub operation failed; inspect/retry the retained release state: "
                               + result.stderr.decode("utf-8", errors="replace")[:1000])
        return result.stdout

    def read(self, path, missing=False):
        raw = self.command("api", self.prefix + path, missing=missing)
        return json.loads(raw) if raw is not None else None

    def release(self, tag):
        # Listing includes authenticated drafts, unlike published-only discovery.
        pages = json.loads(self.command("api", "--paginate", "--slurp", self.prefix + "/releases?per_page=100"))
        matches = [row for page in pages for row in page if row["tag_name"] == tag]
        require(len(matches) <= 1, "ambiguous release identity; inspect duplicate tag releases")
        return matches[0] if matches else None

    def tag_commit(self, tag):
        ref = self.read("/git/ref/tags/" + tag, missing=True)
        if ref is None:
            return None
        obj = ref["object"]
        for _ in range(8):
            require(re.fullmatch(r"[0-9a-f]{40}", str(obj.get("sha"))), "invalid tag object identity")
            if obj.get("type") == "commit":
                return obj["sha"]
            require(obj.get("type") == "tag", "release tag does not resolve to a commit")
            obj = self.read("/git/tags/" + obj["sha"])["object"]
        raise ValueError("annotated tag chain exceeds inspection limit")

    def asset(self, asset_id):
        require(type(asset_id) is int and asset_id > 0, "invalid release asset identity")
        return self.command("api", self.prefix + f"/releases/assets/{asset_id}", "-H", "Accept: application/octet-stream")

    def create_tag(self, tag, sha):
        self.command("api", self.prefix + "/git/refs", "-X", "POST", "-f", "ref=refs/tags/" + tag, "-f", "sha=" + sha)

    def create_draft(self, tag, sha, channel, notes):
        args = ["release", "create", tag, "--repo", self.repository, "--target", sha, "--verify-tag", "--draft",
                "--title", "Vibe Coding Skill " + tag, "--notes-file", str(notes)]
        if channel != "stable":
            args.append("--prerelease")
        self.command(*args)

    def upload(self, tag, files):
        self.command("release", "upload", tag, *map(str, files), "--repo", self.repository)

    def publish(self, tag, channel):
        self.command("release", "edit", tag, "--repo", self.repository, "--draft=false",
                     "--prerelease=" + str(channel != "stable").lower(), "--latest=" + str(channel == "stable").lower())


def local_assets(output, version):
    archive = output / f"Vibe-Coding-Skill-{version}.zip"
    checksums = output / f"Vibe-Coding-Skill-{version}-SHA256SUMS.txt"
    expected = {path.name: path.read_bytes() for path in (archive, checksums)}
    digest = hashlib.sha256(expected[archive.name]).hexdigest()
    require(expected[checksums.name] == f"{digest}  {archive.name}\n".encode(), "local checksum does not match the final artifact")
    require((output / "release-notes.md").is_file(), "release notes missing")
    return expected, digest


def inspect(github, release, tag, sha, channel, expected):
    require(release is not None and release.get("tag_name") == tag, "release identity missing/mismatched")
    require(type(release.get("draft")) is bool and release.get("prerelease") is (channel != "stable"), "release channel/state mismatch")
    target = github.tag_commit(tag)
    require(target == sha or (target is None and release["draft"] and release.get("target_commitish") == sha),
            "release tag target mismatch; do not move an existing tag; inspect or choose a new version")
    assets = release.get("assets")
    require(isinstance(assets, list), "release asset inventory unavailable")
    missing = []
    for name, content in expected.items():
        matches = [row for row in assets if row.get("name") == name]
        require(len(matches) <= 1, "duplicate release asset: " + name)
        if not matches:
            missing.append(name)
            continue
        asset = matches[0]
        require(asset.get("state") == "uploaded" and asset.get("size") == len(content),
                "incomplete/conflicting asset; inspect it explicitly before retry: " + name)
        actual = github.asset(asset["id"])
        require(hashlib.sha256(actual).digest() == hashlib.sha256(content).digest(),
                "release asset content mismatch; no automatic replacement: " + name)
    return missing


def publish(github, sha, version, channel, output, recover_draft=False):
    require(re.fullmatch(r"[0-9a-f]{40}", sha), "invalid target commit")
    require(re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version), "invalid release version")
    require(channel in ("stable", "rc", "beta"), "invalid channel")
    output = output.resolve()
    expected, digest = local_assets(output, version)
    tag = "v" + version
    release = github.release(tag)
    created = release is None
    if release is not None:
        missing = inspect(github, release, tag, sha, channel, expected)
        if not release["draft"]:
            require(not missing, "published release is incomplete; inspect missing assets; never silently rewrite it")
            return {"status": "reused", "tag": tag, "commit": sha, "sha256": digest}
        require(recover_draft, "matching draft needs explicit --recover-draft under publication authorization")
    else:
        target = github.tag_commit(tag)
        require(target in (None, sha), "existing tag points elsewhere; choose a new version instead of moving it")
    if github.tag_commit(tag) is None:
        github.create_tag(tag, sha)
    require(github.tag_commit(tag) == sha, "tag target changed before publication")
    if created:
        github.create_draft(tag, sha, channel, output / "release-notes.md")
    # Re-read before mutation: an interrupted upload/retry never overwrites assets.
    release = github.release(tag)
    missing = inspect(github, release, tag, sha, channel, expected)
    require(release["draft"], "release was published concurrently; inspect before retry")
    if missing:
        github.upload(tag, [output / name for name in missing])
    release = github.release(tag)
    require(release["draft"] and not inspect(github, release, tag, sha, channel, expected), "draft remains incomplete after upload")
    github.publish(tag, channel)
    release = github.release(tag)
    require(release is not None and not release["draft"] and not inspect(github, release, tag, sha, channel, expected),
            "publication not confirmed; inspect/retry retained release state")
    return {"status": "published" if created else "recovered", "tag": tag, "commit": sha, "sha256": digest}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--channel", choices=("stable", "rc", "beta"), required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--recover-draft", action="store_true")
    args = parser.parse_args()
    try:
        require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository), "invalid repository")
        result = publish(GitHub(args.repository), args.sha, args.version, args.channel, args.output_dir, args.recover_draft)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "BLOCK", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
