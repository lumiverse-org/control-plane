"""Unit tests for L2-T519: evidence_chain (tools.evidence.evidence_chain)."""
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

from tools.evidence.evidence_chain import CHECKED, QUESTIONS, check

FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "chain"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.evidence_chain", *args]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def test_complete_record_passes():
    deployment = str(FIXTURES_DIR / "dep-complete.yaml")
    res = run_tool("--deployment", deployment, "--summary")
    assert res.returncode == 0
    assert "OK evidence_chain checked=11 failed=0" in res.stdout


def test_client_app_profile_evidence_passes():
    deployment = str(FIXTURES_DIR / "dep-client-app.yaml")
    res = run_tool("--deployment", deployment, "--summary")
    assert res.returncode == 0
    assert "OK evidence_chain checked=11 failed=0" in res.stdout


def test_missing_approver_fails():
    deployment = str(FIXTURES_DIR / "dep-no-approver.yaml")
    res = run_tool("--deployment", deployment, "--summary")
    assert res.returncode == 2
    assert "FAIL evidence_chain checked=11 failed=1" in res.stdout
    assert "FAIL: evidence-chain question q8_prod_approver is unanswered" in res.stderr


def test_digest_drift_fails():
    deployment = str(FIXTURES_DIR / "dep-digest-drift.yaml")
    res = run_tool("--deployment", deployment, "--summary")
    assert res.returncode == 2
    assert "FAIL evidence_chain checked=11 failed=1" in res.stdout
    assert "FAIL: §32 invariant violated — item 5 digest" in res.stderr


def test_missing_deployment_file_errors():
    deployment = str(FIXTURES_DIR / "nonexistent.yaml")
    res = run_tool("--deployment", deployment, "--summary")
    assert res.returncode == 3
    assert "ERROR evidence_chain checked=0 failed=0" in res.stdout
    assert "deployment record not found" in res.stderr


def test_invalid_yaml_errors(tmp_path: Path):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("not a mapping\n- 1\n- 2\n", encoding="utf-8")
    res = run_tool("--deployment", str(bad_yaml), "--summary")
    assert res.returncode == 3
    assert "ERROR evidence_chain checked=0 failed=0" in res.stdout
    assert "deployment record is not a YAML mapping" in res.stderr


def test_s18_platform_rebuild_substitution_passes(tmp_path: Path):
    record = {
        "q1_git_commit": "abc123def456",
        "q2_pull_request": "PR-42",
        "q3_gate2_approver": "alice (role: tech-lead)",
        "q4_ci_run": "https://github.com/org/repo/actions/runs/12345",
        "q5_artifact_digest": "sha256:build_digest_111",
        "q6_staging_deploy": "2026-09-01T10:00:00Z",
        "q7_staging_passed": True,
        "q8_prod_approver": "bob (role: release-manager)",
        "q9_prod_deploy": "2026-09-01T14:00:00Z",
        "q10_smoke_passed": True,
        "q11_live_digest": "sha256:live_digest_222",  # different digest
        "s18_platform_rebuild": {
            "pinned_commit": "abc123def456",
            "lockfile_hash": "sha256:lockfilehash",
            "build_configuration": "prod-release-v1",
        },
    }
    dep_file = tmp_path / "dep_s18.yaml"
    dep_file.write_text(yaml.safe_dump(record), encoding="utf-8")
    res = run_tool("--deployment", str(dep_file), "--summary")
    assert res.returncode == 0
    assert "OK evidence_chain checked=11 failed=0" in res.stdout


def test_s18_platform_rebuild_missing_component_fails(tmp_path: Path):
    record = {
        "q1_git_commit": "abc123def456",
        "q2_pull_request": "PR-42",
        "q3_gate2_approver": "alice (role: tech-lead)",
        "q4_ci_run": "https://github.com/org/repo/actions/runs/12345",
        "q5_artifact_digest": "sha256:build_digest_111",
        "q6_staging_deploy": "2026-09-01T10:00:00Z",
        "q7_staging_passed": True,
        "q8_prod_approver": "bob (role: release-manager)",
        "q9_prod_deploy": "2026-09-01T14:00:00Z",
        "q10_smoke_passed": True,
        "q11_live_digest": "sha256:live_digest_222",
        "s18_platform_rebuild": {
            "pinned_commit": "abc123def456",
            # missing lockfile_hash and build_configuration
        },
    }
    dep_file = tmp_path / "dep_s18_bad.yaml"
    dep_file.write_text(yaml.safe_dump(record), encoding="utf-8")
    res = run_tool("--deployment", str(dep_file), "--summary")
    assert res.returncode == 2
    assert "FAIL evidence_chain checked=11 failed=1" in res.stdout
    assert "S18 platform-rebuild claimed but missing components" in res.stderr


def test_questions_structure():
    assert CHECKED == 11
    assert len(QUESTIONS) == 11
    fields = [q[0] for q in QUESTIONS]
    assert fields == [
        "q1_git_commit",
        "q2_pull_request",
        "q3_gate2_approver",
        "q4_ci_run",
        "q5_artifact_digest",
        "q6_staging_deploy",
        "q7_staging_passed",
        "q8_prod_approver",
        "q9_prod_deploy",
        "q10_smoke_passed",
        "q11_live_digest",
    ]
