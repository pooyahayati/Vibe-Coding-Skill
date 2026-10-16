#!/usr/bin/env python3
"""Maintainer CI selection; unknown changes expand checks, never imply release proof."""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
OVERVIEWS = {"README.md", "ROADMAP.md", "CHANGELOG.md", "UPDATES.md", "CONTRIBUTING.md", "HOW_TO_INSTALL.md", "LICENSE"}
OVERVIEW_DOCS = {"docs/improvement-implementation-plan.md", "docs/i1-integration-verification.md"}
FULL_INPUTS = {"VERSION", "scripts/ci_scope.py", "scripts/collect_release_checks.py", "scripts/release_readiness.py",
               "scripts/build_release.py", "scripts/sync_package.py", "scripts/validate_skill.py"}
PLATFORM_TESTS = ["tests.test_cross_platform", "tests.test_review_regressions", "tests.test_portable_integration",
                  "tests.test_scripts.GraphProviderContractTests", "tests.test_scripts.GitHubTraceabilityTests"]
INSTRUCTION_TESTS = ["tests.test_context_routing", "tests.test_scripts.RiskClassifierTests", "tests.test_scripts.CompletionGateTests"]
MIRROR = "skills/vibe-coding-skill/"


def dependencies(node: ast.AST) -> set[str]:
    result = set()
    for item in ast.walk(node):
        if isinstance(item, ast.Import):
            result.update(alias.name.rsplit(".", 1)[-1] for alias in item.names)
        elif isinstance(item, ast.ImportFrom):
            result.add((item.module or "").rsplit(".", 1)[-1])
            result.update(alias.name for alias in item.names)
        elif isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id == "load":
            # Repository loader convention: load("module") or load("module.py").
            # A computed target makes focused coverage unknowable, not empty.
            if (len(item.args) != 1 or item.keywords or not isinstance(item.args[0], ast.Constant)
                    or not isinstance(item.args[0].value, str)
                    or not re.fullmatch(r"[A-Za-z_]\w*(?:\.py)?", item.args[0].value)):
                raise ValueError("unresolved dynamic module dependency")
            result.add(item.args[0].value.removesuffix(".py"))
        elif isinstance(item, ast.Constant) and isinstance(item.value, str):
            result.update(re.findall(r"\b([A-Za-z_]\w*)\.py\b", item.value))
    return result


def affected_tests(root: Path, paths: list[str]) -> list[str]:
    files = [*sorted((root / "scripts").glob("*.py")), *sorted((root / "tests").glob("test_*.py"))]
    trees = {file.stem: ast.parse(file.read_text(encoding="utf-8")) for file in files}
    script_names = {file.stem for file in (root / "scripts").glob("*.py")}
    # Only module-level test helpers propagate whole-module impact. A dependency
    # inside one test class must not select unrelated classes in that file.
    graph = {name: dependencies(tree if name in script_names else ast.Module(
        body=[node for node in tree.body if not isinstance(node, ast.ClassDef)], type_ignores=[]))
        for name, tree in trees.items()}
    affected = {Path(path).stem for path in paths if path.endswith(".py")}
    while True:
        expanded = affected | {name for name, deps in graph.items() if deps & affected}
        if expanded == affected:
            break
        affected = expanded
    selected = []
    for name, tree in trees.items():
        if not name.startswith("test_"):
            continue
        global_nodes = [node for node in tree.body if not isinstance(node, ast.ClassDef)]
        globals_used = dependencies(ast.Module(body=global_nodes, type_ignores=[]))
        for node in tree.body:
            is_test = isinstance(node, ast.ClassDef) and any(
                isinstance(base, ast.Attribute) and base.attr == "TestCase" or isinstance(base, ast.Name) and base.id == "TestCase"
                for base in node.bases)
            if is_test and (name in affected or (globals_used | dependencies(node)) & affected):
                selected.append(f"tests.{name}.{node.name}")
    return sorted(set(selected))


def select(paths: list[str] | None, event: str, root: Path = ROOT) -> dict:
    canonical = sorted({path.removeprefix(MIRROR) for path in paths or []})
    reasons = []
    full = event not in {"push", "pull_request", "merge_group"} or paths is None or not canonical
    if full:
        reasons.append("explicit full run or change evidence unavailable")
    code, instructions = [], False
    for path in canonical:
        if path in FULL_INPUTS or path.startswith(".github/"):
            full = True
            reasons.append("delivery or CI control changed")
        elif Path(path).name in {"AGENTS.md", "SKILL.md"}:
            instructions = True
        elif path in OVERVIEWS or path in OVERVIEW_DOCS or (path.startswith("docs/archive/") and path.endswith(".md")) or path == "docs/images/vibe-coding-roadmap-by-pooya-hayati.png":
            continue
        elif path.startswith(("scripts/", "tests/")) and path.endswith(".py"):
            code.append(path)
        elif path == "SKILL.md" or path.startswith(("references/", "packs/", "assets/templates/")):
            instructions = True
        else:
            full = True
            reasons.append("unmapped resource changed")
    tests = []
    if code and not full:
        try:
            tests = affected_tests(root, code)
        except (OSError, SyntaxError, UnicodeError, ValueError):
            full = True
            reasons.append("dependency inspection incomplete")
        if not tests:
            full = True
            reasons.append("no reliable focused test selection")
    if instructions:
        tests = sorted(set(tests) | set(INSTRUCTION_TESTS))
    mode = "full" if full else "affected" if code or instructions else "overview"
    platform = full or bool(code)
    platform_tests = PLATFORM_TESTS if full else [target for target in tests if any(target == p or target.startswith(p + ".") for p in PLATFORM_TESTS)]
    if platform and not platform_tests:
        platform_tests = tests
    return {"schema_version": 1, "mode": mode, "full": full, "runtime": mode != "overview",
            "cross_platform": platform, "policy": full or instructions, "tests": tests,
            "platform_tests": platform_tests, "paths": paths or [], "reasons": sorted(set(reasons))}


def changed_paths(root: Path, event: str, payload: dict) -> list[str] | None:
    try:
        head = os.environ.get("GITHUB_SHA") or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        if event == "pull_request":
            base = payload["pull_request"]["base"]["sha"]
        elif event == "merge_group":
            base = payload["merge_group"]["base_sha"]
        elif event == "push":
            base = payload["before"]
        else:
            return None
        if not all(isinstance(ref, str) and re.fullmatch(r"[0-9a-f]{40}", ref) and ref != "0" * 40 for ref in (base, head)):
            return None
        # HEAD is the checked-out PR merge result, not the unmerged head branch.
        actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        if actual != head:
            return None
        data = subprocess.check_output(["git", "diff", "--name-only", "--no-renames", "-z", base, head, "--"], cwd=root, stderr=subprocess.DEVNULL)
        return [item.decode("utf-8") for item in data.split(b"\0") if item]
    except (KeyError, OSError, subprocess.SubprocessError, UnicodeError):
        return None


def link_errors(root: Path, paths: list[str]) -> list[str]:
    errors = []
    for relative in paths:
        source = root / relative
        if source.suffix.lower() != ".md" or not source.is_file():
            continue
        text = re.sub(r"(?ms)^```.*?^```[^\n]*", "", source.read_text(encoding="utf-8"))
        for match in re.finditer(r"!?\[[^\]\n]*\]\((<[^>]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\)", text):
            href = urlsplit(match.group(1).strip("<>"))
            if href.scheme or href.netloc:
                continue  # Local links only; no network request or URL execution.
            target = (source.parent / unquote(href.path)).resolve() if href.path else source.resolve()
            if not target.is_relative_to(root.resolve()) or not target.exists():
                errors.append(f"{relative}: missing/outside local target {match.group(1)}")
                continue
            if href.fragment and target.suffix.lower() == ".md":
                body = target.read_text(encoding="utf-8")
                anchors = set(re.findall(r'(?:id|name)=[\"\']([^\"\']+)', body))
                counts = {}
                for heading in re.findall(r"(?m)^#{1,6}\s+(.+?)\s*#*\s*$", body):
                    slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
                    number = counts.get(slug, 0)
                    anchors.add(slug + (f"-{number}" if number else ""))
                    counts[slug] = number + 1
                if unquote(href.fragment) not in anchors:
                    errors.append(f"{relative}: missing anchor {match.group(1)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["plan", "test"])
    parser.add_argument("--plan", required=True)
    parser.add_argument("--platform", action="store_true")
    args = parser.parse_args()
    if args.mode == "test":
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        targets = plan["platform_tests"] if args.platform else plan["tests"]
        if plan["full"] and not args.platform:
            targets = ["discover", "-s", "tests", "-p", "test_*.py"]
        elif not all(re.fullmatch(r"tests\.test_\w+(?:\.\w+)?", target) for target in targets):
            raise ValueError("invalid selected test target")
        if not targets:
            raise ValueError("no test execution selected; do not claim a test pass")
        return subprocess.run([sys.executable, "-m", "unittest", *targets], cwd=ROOT).returncode
    event = os.environ.get("GITHUB_EVENT_NAME", "workflow_dispatch")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    try:
        payload = json.loads(Path(event_path).read_text(encoding="utf-8")) if event_path else {}
    except (OSError, ValueError):
        payload = {}
    paths = changed_paths(ROOT, event, payload)
    plan = select(paths, event)
    plan["link_errors"] = link_errors(ROOT, paths if paths is not None else [str(p.relative_to(ROOT)) for p in ROOT.glob("*.md")])
    Path(args.plan).write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
            for key in ("full", "runtime", "cross_platform", "policy"):
                stream.write(f"{key}={str(plan[key]).lower()}\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write(f"CI selection: **{plan['mode']}**. Full release evidence: **{plan['full']}**.\n")
            stream.write("Overview checks do not establish runtime or platform validation.\n" if plan["mode"] == "overview" else "Selected tests follow changed inputs; unknown impact uses the full baseline.\n")
    print(json.dumps(plan, indent=2))
    return 1 if plan["link_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
