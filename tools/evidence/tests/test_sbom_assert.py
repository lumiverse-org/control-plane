"""Unit tests for L2-T538: sbom_assert."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "sbom"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.sbom_assert", *args]
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_good_manifest_passes():
    manifest = str(FIXTURES_DIR / "good.json")
    res = run_tool("--manifest", manifest, "--summary")
    assert res.returncode == 0
    assert "OK sbom_assert checked=2 failed=0" in res.stdout


def test_missing_sbom_fails():
    manifest = str(FIXTURES_DIR / "missing.json")
    res = run_tool("--manifest", manifest, "--summary")
    assert res.returncode == 2
    assert "FAIL sbom_assert checked=2 failed=1" in res.stdout
    assert "has no sbom entry" in res.stderr


def test_sbom_in_later_step_fails():
    manifest = str(FIXTURES_DIR / "later-step.json")
    res = run_tool("--manifest", manifest, "--summary")
    assert res.returncode == 2
    assert "FAIL sbom_assert checked=2 failed=1" in res.stdout
    assert "sbom emitted in different step" in res.stderr


def test_empty_manifest_errors():
    manifest = str(FIXTURES_DIR / "empty.json")
    res = run_tool("--manifest", manifest, "--summary")
    assert res.returncode == 3
    assert "ERROR sbom_assert checked=0 failed=0" in res.stdout
    assert "not a clean build" in res.stderr


def test_missing_manifest_file_errors():
    manifest = str(FIXTURES_DIR / "nonexistent.json")
    res = run_tool("--manifest", manifest, "--summary")
    assert res.returncode == 3
    assert "ERROR reading" in res.stderr
