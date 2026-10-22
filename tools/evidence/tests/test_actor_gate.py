"""Unit tests for L2-T541: actor_gate."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "actor"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.actor_gate", *args]
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_machine_actor_rejected():
    people_path = str(FIXTURES_DIR / "people.yaml")
    res = run_tool("--actor", "machine-1", "--capability", "devops", "--people", people_path, "--summary")
    assert res.returncode == 2
    assert "FAIL actor_gate checked=3 failed=1" in res.stdout
    assert "MACHINE_ACTOR_REJECTED" in res.stderr


def test_human_without_capability_fails():
    people_path = str(FIXTURES_DIR / "people.yaml")
    res = run_tool("--actor", "dev-2", "--capability", "devops", "--people", people_path, "--summary")
    assert res.returncode == 2
    assert "FAIL actor_gate checked=3 failed=1" in res.stdout


def test_human_with_capability_passes():
    people_path = str(FIXTURES_DIR / "people.yaml")
    res = run_tool("--actor", "dev-1", "--capability", "devops", "--people", people_path, "--summary")
    assert res.returncode == 0
    assert "OK actor_gate checked=3 failed=0" in res.stdout


def test_unreadable_people_yaml_errors():
    people_path = str(FIXTURES_DIR / "nope.yaml")
    res = run_tool("--actor", "dev-1", "--capability", "devops", "--people", people_path, "--summary")
    assert res.returncode == 3
    assert "ERROR actor_gate checked=0 failed=0" in res.stdout
