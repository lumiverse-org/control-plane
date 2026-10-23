"""Unit tests for L2-T533: lint_workflow."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "lint"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.lint_workflow", *args]
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_good_fixture_passes():
    res = run_tool("--path", str(FIXTURES_DIR / "good.yml"), "--summary")
    assert res.returncode == 0
    assert "OK lint_workflow checked=1 failed=0" in res.stdout


def test_fixture_directory_reports_five_failures():
    res = run_tool("--path", str(FIXTURES_DIR), "--summary")
    assert res.returncode == 2
    assert "FAIL lint_workflow checked=6 failed=5" in res.stdout


def test_missing_path_errors():
    res = run_tool("--path", str(FIXTURES_DIR / "nope.yml"), "--summary")
    assert res.returncode == 3
    assert "ERROR lint_workflow checked=0 failed=0" in res.stdout
    assert "ERROR: path does not exist" in res.stderr


def test_bad_lw01_unpinned_action():
    res = run_tool("--path", str(FIXTURES_DIR / "bad_lw01.yml"), "--summary")
    assert res.returncode == 2
    assert "FAIL lint_workflow checked=1 failed=1" in res.stdout
    assert "LW-01" in res.stderr


def test_bad_lw02_if_on_required_job():
    res = run_tool("--path", str(FIXTURES_DIR / "bad_lw02.yml"), "--summary")
    assert res.returncode == 2
    assert "FAIL lint_workflow checked=1 failed=1" in res.stdout
    assert "LW-02" in res.stderr


def test_bad_lw03_path_filter():
    res = run_tool("--path", str(FIXTURES_DIR / "bad_lw03.yml"), "--summary")
    assert res.returncode == 2
    assert "FAIL lint_workflow checked=1 failed=1" in res.stdout
    assert "LW-03" in res.stderr


def test_bad_lw04_permissions_absent():
    res = run_tool("--path", str(FIXTURES_DIR / "bad_lw04.yml"), "--summary")
    assert res.returncode == 2
    assert "FAIL lint_workflow checked=1 failed=1" in res.stdout
    assert "LW-04" in res.stderr


def test_bad_lw05_continue_on_error():
    res = run_tool("--path", str(FIXTURES_DIR / "bad_lw05.yml"), "--summary")
    assert res.returncode == 2
    assert "FAIL lint_workflow checked=1 failed=1" in res.stdout
    assert "LW-05" in res.stderr


def test_empty_directory_is_ok(tmp_path):
    res = run_tool("--path", str(tmp_path), "--summary")
    assert res.returncode == 0
    assert "OK lint_workflow checked=0 failed=0" in res.stdout


def test_stdout_carries_only_summary_line():
    res = run_tool("--path", str(FIXTURES_DIR), "--summary")
    # exactly one line of stdout: the summary line itself
    assert res.stdout.strip().splitlines() == ["FAIL lint_workflow checked=6 failed=5"]


def test_non_workflow_files_are_skipped(tmp_path):
    # A config/metadata file without on: and jobs: must not be flagged for missing permissions
    meta = tmp_path / "MANIFEST.yaml"
    meta.write_text("templates:\n  - template: ci.yml\n    destination: .github/workflows/ci.yml\n")
    res = run_tool("--path", str(meta), "--summary")
    assert res.returncode == 0
    assert "OK lint_workflow checked=1 failed=0" in res.stdout


def test_templated_workflow_with_placeholders_passes(tmp_path):
    wf = tmp_path / "build.yml"
    wf.write_text(
        "name: Build\n"
        "on:\n"
        "  push:\n"
        "permissions:\n"
        "  contents: read\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    uses: {{CONTROL_PLANE_REPO}}/.github/workflows/build.yml@{{WORKFLOWS_TAG}}\n"
    )
    res = run_tool("--path", str(wf), "--summary")
    assert res.returncode == 0
    assert "OK lint_workflow checked=1 failed=0" in res.stdout
