"""Unit tests for L2-T542: identity_gate."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "identity"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.identity_gate", *args]
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_self_approval_fails():
    approval = str(FIXTURES_DIR / "self.yaml")
    res = run_tool("--approval", approval, "--deployer", "dev-1", "--summary")
    assert res.returncode == 2
    assert "FAIL identity_gate checked=1 failed=1" in res.stdout
    assert "APPROVER_EQUALS_DEPLOYER" in res.stderr


def test_differing_identity_passes():
    approval = str(FIXTURES_DIR / "other.yaml")
    res = run_tool("--approval", approval, "--deployer", "dev-1", "--summary")
    assert res.returncode == 0
    assert "OK identity_gate checked=1 failed=0" in res.stdout


def test_empty_approver_errors():
    approval = str(FIXTURES_DIR / "empty.yaml")
    res = run_tool("--approval", approval, "--deployer", "dev-1", "--summary")
    assert res.returncode == 3
    assert "ERROR identity_gate checked=0 failed=0" in res.stdout
    assert "no resolvable approver field" in res.stderr


def test_missing_approval_file_errors():
    approval = str(FIXTURES_DIR / "missing.yaml")
    res = run_tool("--approval", approval, "--deployer", "dev-1", "--summary")
    assert res.returncode == 3
    assert "ERROR identity_gate checked=0 failed=0" in res.stdout
    assert "approval record not found" in res.stderr
