#!/usr/bin/env python3
"""Collect exact-revision GitHub run evidence without promoting partial CI to release proof."""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
from pathlib import Path

import release_readiness as readiness


def api(endpoint: str) -> list[dict]:
    completed = subprocess.run(["gh", "api", "--paginate", "--slurp", endpoint],
                               capture_output=True, text=True, encoding="utf-8", timeout=60)
    if completed.returncode:
        raise RuntimeError("GitHub evidence query unavailable; no release success claimed")
    result = json.loads(completed.stdout)
    if not isinstance(result, list):
        raise ValueError("unexpected GitHub evidence response")
    return result


def collect(runs: list[dict], repository: str, sha: str, channel: str, fetch_jobs) -> dict:
    checks = []
    for run in runs:
        if (run.get("head_sha") != sha or run.get("head_branch") != "main"
                or run.get("event") not in {"push", "workflow_dispatch", "schedule"}
                or run.get("head_repository", {}).get("full_name") != repository
                or run.get("name") not in readiness.CHANNEL_CHECKS[channel]):
            continue
        checks.append({"name": run["name"], "commit": sha, "conclusion": run.get("conclusion"),
                       "run_id": run["id"], "run_attempt": run.get("run_attempt", 1)})
    latest = readiness.latest_check_records(checks, sha)
    for name, check in latest.items():
        check["validation_scope"] = "unverified"
        if check["conclusion"] == "success":
            if name not in readiness.FULL_SCOPE_CHECKS:
                check["validation_scope"] = "full"
            elif readiness.full_validation_scope(name, fetch_jobs(check["run_id"], check["run_attempt"])):
                check["validation_scope"] = "full"
            else:
                check["validation_scope"] = "partial"
    return {"schema_version": 2, "version": readiness.current_skill_version(), "commit": sha, "checks": list(latest.values())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--channel", choices=readiness.CHANNEL_CHECKS, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--event", help="workflow_run event snapshot; preserves the completed trigger during API indexing lag")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository) or not re.fullmatch(r"[0-9a-f]{40}", args.sha):
        raise ValueError("invalid repository or target revision")
    prefix = "repos/" + args.repository + "/actions/runs"
    runs = [run for page in api(prefix + f"?head_sha={args.sha}&per_page=100") for run in page.get("workflow_runs", [])]
    if args.event:
        trigger = json.loads(Path(args.event).read_text(encoding="utf-8")).get("workflow_run")
        if isinstance(trigger, dict):
            runs.append(trigger)

    def jobs(run_id, attempt):
        if type(run_id) is not int or type(attempt) is not int or min(run_id, attempt) < 1:
            raise ValueError("invalid run/attempt identity")
        return [job for page in api(prefix + f"/{run_id}/attempts/{attempt}/jobs?per_page=100") for job in page.get("jobs", [])]

    report = collect(runs, args.repository, args.sha, args.channel, jobs)
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    result = readiness.evaluate(report, args.channel)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
            stream.write(f"base_ready={'true' if result['gate'] == 'PASS' else 'false'}\n")
    print(json.dumps(result, indent=2))
    # Other baseline runs may still be executing; unavailable API evidence raises.
    # The publication step runs only when base_ready is true.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
