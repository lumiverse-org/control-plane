"""Unit tests for L2-T539: render_template."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "render"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.render_template", *args]
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def test_ok_fixture_passes():
    res = run_tool("--lint", str(FIXTURES_DIR / "ok"), "--summary")
    assert res.returncode == 0
    assert "OK render_template checked=2 failed=0" in res.stdout


def test_undeclared_token_fails():
    res = run_tool("--lint", str(FIXTURES_DIR / "undeclared"), "--summary")
    assert res.returncode == 2
    assert "FAIL render_template checked=1 failed=1" in res.stdout
    assert "token {{NOPE}} is not declared" in res.stderr


def test_nested_gha_expression_fails():
    res = run_tool("--lint", str(FIXTURES_DIR / "nested"), "--summary")
    assert res.returncode == 2
    assert "FAIL render_template checked=1 failed=1" in res.stdout
    assert "inside GHA" in res.stderr


def test_missing_placeholders_file_errors(tmp_path):
    empty_dir = tmp_path / "no-placeholders"
    empty_dir.mkdir()
    res = run_tool("--lint", str(empty_dir), "--summary")
    assert res.returncode == 3
    assert "ERROR render_template checked=0 failed=0" in res.stdout
    assert "PLACEHOLDERS.yaml not found" in res.stderr


def test_lint_nonexistent_directory_errors():
    res = run_tool("--lint", str(FIXTURES_DIR / "does-not-exist"), "--summary")
    assert res.returncode == 3
    assert "ERROR render_template checked=0 failed=0" in res.stdout


def test_render_writes_stdout_only_no_file(tmp_path):
    template = tmp_path / "sample.yml"
    template.write_text("name: ci-{{PRODUCT_NAME}}\n")
    values = tmp_path / "values.yaml"
    values.write_text('"{{PRODUCT_NAME}}": demo-product\n')

    before = set(tmp_path.iterdir())
    res = run_tool("--render", str(template), "--values", str(values), "--summary")
    after = set(tmp_path.iterdir())

    assert res.returncode == 0
    assert "name: ci-demo-product" in res.stdout
    assert "OK render_template checked=1 failed=0" in res.stdout
    assert before == after  # no file was created, removed, or renamed by --render


def test_render_without_values_leaves_unknown_tokens_untouched(tmp_path):
    template = tmp_path / "sample.yml"
    template.write_text("name: ci-{{PRODUCT_NAME}}\n")

    res = run_tool("--render", str(template), "--summary")

    assert res.returncode == 0
    assert "name: ci-{{PRODUCT_NAME}}" in res.stdout  # no --values given: token passes through literally


def test_manifest_all_entries_present(tmp_path):
    (tmp_path / "ci.yml").write_text("name: ci\n")
    manifest = tmp_path / "MANIFEST.yaml"
    manifest.write_text("templates:\n  - file: ci.yml\n")

    res = run_tool("--manifest", str(manifest), "--summary")

    assert res.returncode == 0
    assert "OK render_template checked=1 failed=0" in res.stdout


def test_manifest_missing_entry_fails(tmp_path):
    manifest = tmp_path / "MANIFEST.yaml"
    manifest.write_text("templates:\n  - file: missing.yml\n")

    res = run_tool("--manifest", str(manifest), "--summary")

    assert res.returncode == 2
    assert "FAIL render_template checked=1 failed=1" in res.stdout
    assert "manifest entry missing.yml does not exist" in res.stderr


def test_empty_directory_with_declared_tokens_is_ok(tmp_path):
    """Recommended hardening beyond the task doc's 3 named fixtures: L2-T300's own README text
    (quoted in lanes/L2-05-tasks.md ~line 4399) says an empty template directory lints OK, not
    as N 'unused token' failures. See correction #2 in this spec's (c)."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    (empty_dir / "PLACEHOLDERS.yaml").write_text('tokens:\n  - "{{PRODUCT_NAME}}"\n')

    res = run_tool("--lint", str(empty_dir), "--summary")

    assert res.returncode == 0
    assert "OK render_template checked=0 failed=0" in res.stdout
