"""Unit tests for L2-T534: check_required_contexts."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "contexts"
REGISTRY = str(FIXTURES_DIR / "registry.yaml")


def run_tool(*args: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "tools.evidence.check_required_contexts", *args]
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def test_ok_fixture_passes():
    res = run_tool("--templates", str(FIXTURES_DIR / "ok"), "--registry", REGISTRY, "--summary")
    assert res.returncode == 0
    assert "OK check_required_contexts checked=3 failed=0" in res.stdout


def test_missing_fixture_fails():
    res = run_tool("--templates", str(FIXTURES_DIR / "missing"), "--registry", REGISTRY, "--summary")
    assert res.returncode == 2
    assert "FAIL check_required_contexts checked=3 failed=1" in res.stdout
    assert "not emitted by any job" in res.stderr


def test_extra_fixture_fails_on_if():
    res = run_tool("--templates", str(FIXTURES_DIR / "extra"), "--registry", REGISTRY, "--summary")
    assert res.returncode == 2
    assert "FAIL check_required_contexts checked=3 failed=1" in res.stdout
    assert "PATH_FILTER_ON_REQUIRED_CONTEXT" in res.stderr


def test_real_registry_parses_to_fifteen_contexts():
    """Regression guard for the nested `contexts:` schema (lanes/L2-00-charter.md
    §A5-C/A6-C): checked= must reflect all 15 published contexts regardless of
    how many are currently emitted elsewhere in the tree."""
    real_registry = str(REPO_ROOT / "templates" / "workflows" / "required-checks.yaml")
    res = run_tool("--templates", str(REPO_ROOT / "templates" / "workflows"),
                   "--registry", real_registry, "--summary")
    assert "checked=15" in res.stdout


def test_missing_registry_errors():
    res = run_tool("--templates", str(FIXTURES_DIR / "ok"),
                    "--registry", str(FIXTURES_DIR / "nonexistent.yaml"), "--summary")
    assert res.returncode == 3
    assert "ERROR check_required_contexts checked=0 failed=0" in res.stdout
