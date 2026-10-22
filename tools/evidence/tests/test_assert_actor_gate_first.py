"""Unit tests for assert_actor_gate_first (tools.evidence.assert_actor_gate_first)."""
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

from tools.evidence.assert_actor_gate_first import (
    ACTOR_GATE_MARKERS,
    FIXED_PRIVILEGED,
    _first_step_invokes_gate,
    _resolve_rollback_name,
)


def run_tool(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.assert_actor_gate_first", *args]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def _make_wf(step_0_run: str) -> dict:
    return {
        "name": "Test Workflow",
        "jobs": {
            "entry": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"name": "Check Actor", "run": step_0_run},
                    {"name": "Do Work", "run": "echo work"},
                ],
            }
        },
    }


def test_all_five_workflows_with_actor_gate_passes(tmp_path: Path):
    wf_dir = tmp_path / "workflows"
    wf_dir.mkdir()

    for name in FIXED_PRIVILEGED + ["rollback.yml"]:
        wf_content = _make_wf("python -m tools.evidence.actor_gate --actor $ACTOR")
        (wf_dir / name).write_text(yaml.safe_dump(wf_content), encoding="utf-8")

    res = run_tool("--path", str(wf_dir), "--rollback-workflow", "rollback.yml", "--summary")
    assert res.returncode == 0
    assert "OK assert_actor_gate_first checked=5 failed=0" in res.stdout


def test_missing_privileged_workflow_fails(tmp_path: Path):
    wf_dir = tmp_path / "workflows"
    wf_dir.mkdir()

    # Create only 4 of the 5
    for name in ["deploy-staging.yml", "deploy-production.yml", "migrate.yml", "rollback.yml"]:
        wf_content = _make_wf("python -m tools.evidence.actor_gate")
        (wf_dir / name).write_text(yaml.safe_dump(wf_content), encoding="utf-8")

    res = run_tool("--path", str(wf_dir), "--rollback-workflow", "rollback.yml", "--summary")
    assert res.returncode == 2
    assert "FAIL assert_actor_gate_first checked=5 failed=1" in res.stdout
    assert "FAIL: privileged workflow missing: restore-test.yml" in res.stderr


def test_actor_gate_not_step_0_fails(tmp_path: Path):
    wf_dir = tmp_path / "workflows"
    wf_dir.mkdir()

    # One workflow puts checkout before actor_gate
    bad_wf = {
        "jobs": {
            "entry": {
                "steps": [
                    {"name": "Checkout", "uses": "actions/checkout@v4"},
                    {"name": "Actor Gate", "run": "python -m tools.evidence.actor_gate"},
                ]
            }
        }
    }
    good_wf = _make_wf("python -m tools.evidence.actor_gate")

    for name in FIXED_PRIVILEGED:
        (wf_dir / name).write_text(yaml.safe_dump(good_wf), encoding="utf-8")
    (wf_dir / "rollback.yml").write_text(yaml.safe_dump(bad_wf), encoding="utf-8")

    res = run_tool("--path", str(wf_dir), "--rollback-workflow", "rollback.yml", "--summary")
    assert res.returncode == 2
    assert "FAIL assert_actor_gate_first checked=5 failed=1" in res.stdout
    assert "FAIL: actor gate is not step 0 in rollback.yml" in res.stderr


def test_invalid_path_errors():
    res = run_tool("--path", "nonexistent_dir_12345", "--summary")
    assert res.returncode == 3
    assert "ERROR assert_actor_gate_first checked=0 failed=0" in res.stdout


def test_missing_rollback_resolution_errors(tmp_path: Path):
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    # No --rollback-workflow passed, and MANIFEST_PATH does not resolve in custom cwd
    # Note: run from tmp_path so MANIFEST_PATH doesn't exist relative to it
    res = run_tool("--path", str(empty_dir), "--summary", cwd=empty_dir)
    # If run in empty_dir where templates/workflows/MANIFEST.yaml does not exist
    # _resolve_rollback_name returns None -> exit 3
    assert res.returncode == 3
    assert "ERROR: rollback workflow name unknown" in res.stderr


def test_reusable_workflow_caller_job(tmp_path: Path):
    wf_path = tmp_path / "reusable_caller.yml"
    caller_data = {
        "jobs": {
            "actor-gate": {
                "uses": "./.github/workflows/actor-gate.yml"
            }
        }
    }
    wf_path.write_text(yaml.safe_dump(caller_data), encoding="utf-8")
    assert _first_step_invokes_gate(wf_path) is True


def test_fixed_privileged_constant():
    assert FIXED_PRIVILEGED == [
        "deploy-staging.yml",
        "deploy-production.yml",
        "migrate.yml",
        "restore-test.yml",
    ]
