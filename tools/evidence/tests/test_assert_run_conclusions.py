"""Unit tests for L2-T535: assert_run_conclusions."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNS_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "runs"
REGISTRY = REPO_ROOT / "tools" / "evidence" / "fixtures" / "contexts" / "registry.yaml"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.assert_run_conclusions", *args]
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_clean_passes():
    res = run_tool("--checks", str(RUNS_DIR / "clean.json"), "--registry", str(REGISTRY), "--summary")
    assert res.returncode == 0
    assert "OK assert_run_conclusions checked=3 failed=0" in res.stdout


def test_skipped_fails():
    res = run_tool("--checks", str(RUNS_DIR / "skipped.json"), "--registry", str(REGISTRY), "--summary")
    assert res.returncode == 2
    assert "FAIL assert_run_conclusions checked=3 failed=1" in res.stdout
    assert "FAIL: context 'build' has forbidden conclusion 'skipped'" in res.stderr


def test_neutral_fails():
    res = run_tool("--checks", str(RUNS_DIR / "neutral.json"), "--registry", str(REGISTRY), "--summary")
    assert res.returncode == 2
    assert "FAIL assert_run_conclusions checked=3 failed=1" in res.stdout
    assert "FAIL: context 'build' has forbidden conclusion 'neutral'" in res.stderr


def test_absent_fails():
    res = run_tool("--checks", str(RUNS_DIR / "absent.json"), "--registry", str(REGISTRY), "--summary")
    assert res.returncode == 2
    assert "FAIL assert_run_conclusions checked=3 failed=1" in res.stdout
    assert "FAIL: context 'build' is absent from check runs" in res.stderr


def test_unreadable_checks_errors():
    res = run_tool("--checks", str(RUNS_DIR / "does-not-exist.json"), "--registry", str(REGISTRY), "--summary")
    assert res.returncode == 3
    assert "ERROR assert_run_conclusions checked=0 failed=0" in res.stdout
    assert "ERROR reading checks JSON" in res.stderr


def test_malformed_checks_errors():
    res = run_tool("--checks", str(RUNS_DIR / "malformed.json"), "--registry", str(REGISTRY), "--summary")
    assert res.returncode == 3
    assert "ERROR assert_run_conclusions checked=0 failed=0" in res.stdout
    assert "ERROR reading checks JSON" in res.stderr
