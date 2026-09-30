"""Grade the behavior from the exact ZIP with an instrumented PHP runtime."""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

PHP_HARNESS = r'''<?php
error_reporting(E_ALL);
define('ABSPATH', __DIR__ . '/');
$actions = []; $settings = []; $options = [];
function add_action($hook, $callback, ...$rest) { global $actions; $actions[$hook][] = $callback; }
function register_setting($group, $name, $args = []) { global $settings; $settings[$name] = $args; }
function sanitize_text_field($value) { return trim(preg_replace('/\s+/', ' ', strip_tags((string)$value))); }
function get_option($name, $default = false) { global $options; return $options[$name] ?? $default; }
function esc_attr($value) { return htmlspecialchars((string)$value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
require $argv[1];
foreach ($actions['admin_init'] ?? [] as $callback) { call_user_func($callback); }
$args = $settings['sample_label'] ?? null;
$sanitize = is_array($args) ? ($args['sanitize_callback'] ?? null) : $args;
$registered = $args !== null && is_callable($sanitize);
$sanitized = $registered ? call_user_func($sanitize, ' <b>Hello</b> ') : null;
$options['sample_label'] = '" onfocus="alert(1)" ><script>alert(1)</script>&';
ob_start();
if (is_callable('sample_plugin_render_label_field')) { sample_plugin_render_label_field(); }
$html = ob_get_clean();
echo json_encode(['registered' => $registered, 'sanitized' => $sanitized,
                  'html' => $html, 'stored_value' => $options['sample_label']]);
'''


class InputProbe(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.inputs = []
        self.unsafe = False

    def handle_starttag(self, tag, attrs):
        if tag != "input" or any(name.lower().startswith("on") for name, _ in attrs):
            self.unsafe = True
        if tag == "input":
            self.inputs.append(dict(attrs))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def inspect_zip(zip_path: Path):
    with ZipFile(zip_path) as archive:
        names = [name for name in archive.namelist() if name and not name.endswith("/")]
        valid = bool(names) and len(names) == len(set(names)) and all(
            "\\" not in name and not PurePosixPath(name).is_absolute()
            and ".." not in PurePosixPath(name).parts
            and name.startswith("sample-plugin/")
            for name in names
        ) and {name.split("/", 1)[0] for name in names} == {"sample-plugin"}
        valid = valid and all(name in names for name in (
            "sample-plugin/sample-plugin.php", "sample-plugin/includes/admin.php"
        )) and not any(((item.external_attr >> 16) & 0o170000) == 0o120000 for item in archive.infolist())
        if not valid:
            return False, False, {}, "invalid ZIP paths or plugin layout"
        main = archive.read("sample-plugin/sample-plugin.php").decode("utf-8")
        header_ok = "Plugin Name: Sample Plugin" in main and "Version: 1.0.0" in main
        php = shutil.which("php")
        if not php:
            return True, header_ok, {}, "PHP CLI unavailable; functional/security verification is not established"
        with tempfile.TemporaryDirectory(prefix="vibe-wp-grade-") as td:
            base = Path(td)
            archive.extractall(base)
            harness = base / "trusted-harness.php"
            harness.write_text(PHP_HARNESS, encoding="utf-8")
            result = subprocess.run([php, str(harness), str(base / "sample-plugin/sample-plugin.php")],
                                    text=True, capture_output=True, timeout=15)
            if result.returncode != 0:
                return True, header_ok, {}, "PHP execution failed: " + result.stderr[-1500:]
            behavior = json.loads(result.stdout)
            return True, header_ok, behavior, "Executed instrumented WordPress API behavior from ZIP"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--json", action="store_true")
    root = Path(ap.parse_args().workspace)
    artifact_ok = header_ok = registration_ok = escaped_input_ok = False
    detail = "Artifact build did not complete"
    try:
        build = subprocess.run([sys.executable, "build_plugin.py"], cwd=root,
                               text=True, capture_output=True, timeout=15)
        if build.returncode == 0:
            artifact_ok, header_ok, behavior, detail = inspect_zip(root / "dist/sample-plugin.zip")
            registration_ok = behavior.get("registered") is True and behavior.get("sanitized") == "Hello"
            parser = InputProbe()
            parser.feed(behavior.get("html", ""))
            escaped_input_ok = not parser.unsafe and len(parser.inputs) == 1 and all(
                parser.inputs[0].get(key) == value for key, value in {
                    "type": "text", "name": "sample_label", "value": behavior.get("stored_value")
                }.items()
            )
        else:
            detail = "Artifact build failed: " + build.stderr[-1500:]
    except Exception as exc:
        detail = type(exc).__name__ + ": " + str(exc)
    checks = [
        ("setting-registered-and-sanitized", "functional", registration_ok),
        ("setting-input-escaped", "security", escaped_input_ok),
        ("plugin-header-preserved", "regression", header_ok),
        ("installable-zip-shape", "artifact", artifact_ok),
    ]
    print(json.dumps({"schema_version": 1, "checks": [
        {"id": cid, "category": category, "required": True, "passed": passed, "details": detail}
        for cid, category, passed in checks
    ], "metrics": {}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
