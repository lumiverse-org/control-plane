"""Unit tests for L2-T553: shipped_assert (tools.evidence.shipped_assert)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.evidence.shipped_assert import CHECKED, CONDITIONS, check

FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "shipped"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.shipped_assert", *args]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def test_complete_deployment_passes():
    deployment = str(FIXTURES_DIR / "complete.yaml")
    res = run_tool("--deployment", deployment, "--summary")
    assert res.returncode == 0
    assert "OK shipped_assert checked=8 failed=0" in res.stdout
    assert "merged=True deployed=True" in res.stderr


def test_merged_only_fails_remaining_conditions():
    deployment = str(FIXTURES_DIR / "merged-only.yaml")
    res = run_tool("--deployment", deployment, "--summary")
    assert res.returncode == 2
    assert "FAIL shipped_assert checked=8 failed=7" in res.stdout
    assert "merged=True deployed=False" in res.stderr
    assert "FAIL: condition not met — 2. Artifact built and digest recorded" in res.stderr
    assert "FAIL: condition not met — 3. Deployed to the target environment" in res.stderr


def test_missing_state_md_fails_single_condition():
    deployment = str(FIXTURES_DIR / "no-state-md.yaml")
    res = run_tool("--deployment", deployment, "--summary")
    assert res.returncode == 2
    assert "FAIL shipped_assert checked=8 failed=1" in res.stdout
    assert "merged=True deployed=True" in res.stderr
    assert "FAIL: condition not met — 8. STATE.md updated" in res.stderr


def test_missing_deployment_file_errors():
    deployment = str(FIXTURES_DIR / "nonexistent.yaml")
    res = run_tool("--deployment", deployment, "--summary")
    assert res.returncode == 3
    assert "ERROR shipped_assert checked=0 failed=0" in res.stdout
    assert "deployment record not found" in res.stderr


def test_invalid_yaml_errors(tmp_path: Path):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("not a yaml mapping\n- 1\n- 2\n", encoding="utf-8")
    res = run_tool("--deployment", str(bad_yaml), "--summary")
    assert res.returncode == 3
    assert "ERROR shipped_assert checked=0 failed=0" in res.stdout
    assert "deployment record is not a YAML mapping" in res.stderr


def test_conditions_count_and_order():
    assert CHECKED == 8
    assert len(CONDITIONS) == 8
    keys = [c[0] for c in CONDITIONS]
    assert keys == [
        "merged",
        "artifact_built",
        "deployed",
        "deploy_success",
        "smoke_passed",
        "version_recorded",
        "health_green",
        "state_md_updated",
    ]


def test_check_unit_truthiness():
    # Test truthiness handling: non-empty string, boolean True, int 1 all count as True
    record = {
        "merged": "yes",
        "artifact_built": 1,
        "deployed": True,
        "deploy_success": "ok",
        "smoke_passed": True,
        "version_recorded": "sha256:abcd",
        "health_green": True,
        "state_md_updated": True,
    }
    failed, states = check(record)
    assert failed == 0
    assert all(states.values())
