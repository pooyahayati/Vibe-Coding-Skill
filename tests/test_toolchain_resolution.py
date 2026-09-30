import json
from pathlib import Path

import scripts.toolchain_resolution as resolution


ROOT = Path(__file__).resolve().parents[1]


def test_toolchain_config_uses_latest_compatible_policy():
    cfg = json.loads((ROOT / "config" / "toolchain.json").read_text(encoding="utf-8"))
    for tool in ("graphify", "trivy"):
        entry = cfg[tool]
        assert entry["channel"] == "stable"
        assert entry["resolution"] == "latest-compatible-stable"
        assert entry["last_known_good"]
        assert "approved" not in entry
        assert "latest_seen" not in entry


def test_resolver_selects_latest_candidate(monkeypatch):
    cfg = {
        "graphify": {
            "channel": "stable",
            "resolution": "latest-compatible-stable",
            "last_known_good": "old",
        }
    }
    monkeypatch.setattr(
        resolution,
        "contract",
        lambda tool, version=None: {"version": "new", "ok": True}
        if version is None
        else {"version": version, "ok": True},
    )
    result = resolution.resolve("graphify", cfg)
    assert result["selected_version"] == "new"
    assert result["fallback_used"] is False


def test_resolver_falls_back_when_latest_fails(monkeypatch):
    cfg = {
        "graphify": {
            "channel": "stable",
            "resolution": "latest-compatible-stable",
            "last_known_good": "old",
        }
    }

    def fake_contract(tool, version=None):
        return {"version": "new", "ok": False} if version is None else {"version": version, "ok": True}

    monkeypatch.setattr(resolution, "contract", fake_contract)
    result = resolution.resolve("graphify", cfg)
    assert result["selected_version"] == "old"
    assert result["fallback_used"] is True
    assert result["source"] == "last-known-good"


def test_resolver_rejects_broken_fallback(monkeypatch):
    cfg = {
        "graphify": {
            "channel": "stable",
            "resolution": "latest-compatible-stable",
            "last_known_good": "old",
        }
    }
    monkeypatch.setattr(resolution, "contract", lambda tool, version=None: {"version": version or "new", "ok": False})
    try:
        resolution.resolve("graphify", cfg)
    except RuntimeError as exc:
        assert "last-known-good" in str(exc)
    else:
        raise AssertionError("resolver must fail when both candidate and fallback are incompatible")


def test_runtime_command_uses_exact_graphify_version(monkeypatch):
    import scripts.toolchain_runtime as runtime

    monkeypatch.setattr(runtime.shutil, "which", lambda name: None if name == "graphify" else "/usr/bin/uvx")
    cmd = runtime.graphify_command("1.2.3", ["--version"])
    assert cmd[:4] == ["uvx", "--from", "graphifyy==1.2.3", "graphify"]


def test_runtime_command_rejects_unverified_installed_graphify(monkeypatch):
    import scripts.toolchain_runtime as runtime

    monkeypatch.setattr(runtime.shutil, "which", lambda name: "/usr/bin/graphify" if name == "graphify" else None)

    class Result:
        returncode = 0
        stdout = "Graphify 9.9.9"
        stderr = ""

    monkeypatch.setattr(runtime.subprocess, "run", lambda *args, **kwargs: Result())
    try:
        runtime.graphify_command("1.2.3", ["--version"])
    except RuntimeError as exc:
        assert "uvx runtime" in str(exc)
    else:
        raise AssertionError("runtime must not silently use a mismatched installed Graphify")
