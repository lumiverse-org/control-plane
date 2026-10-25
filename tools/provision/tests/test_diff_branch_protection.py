"""Unit tests for tools/provision/diff-branch-protection (CP-0107, Section 53.1)."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
DIFF_BRANCH_PROT_SCRIPT = REPO_ROOT / "tools" / "provision" / "diff-branch-protection"
SERVICE_TEMPLATE = REPO_ROOT / "templates" / "protection" / "service.json"


def test_diff_branch_protection_matches_template(tmp_path: pathlib.Path):
    """Passes when actual branch protection matches the template."""
    assert SERVICE_TEMPLATE.is_file(), f"Template missing: {SERVICE_TEMPLATE}"
    actual_data = json.loads(SERVICE_TEMPLATE.read_text(encoding="utf-8"))

    actual_file = tmp_path / "actual.json"
    actual_file.write_text(json.dumps(actual_data), encoding="utf-8")

    cmd = [
        sys.executable,
        str(DIFF_BRANCH_PROT_SCRIPT),
        "--repo",
        "lumiverse-org/pilot-one",
        "--template",
        str(SERVICE_TEMPLATE),
        "--actual-file",
        str(actual_file),
        "--exit-nonzero-on-diff",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "BRANCH-PROTECTION OK" in proc.stdout


def test_diff_branch_protection_detects_mismatch(tmp_path: pathlib.Path):
    """Detects differences in branch protection and exits non-zero with --exit-nonzero-on-diff."""
    actual_data = {
        "required_pull_request_reviews": {
            "required_approving_review_count": 0,  # template requires 1
            "require_code_owner_reviews": False,
        },
        "required_status_checks": {
            "strict": False,
            "contexts": [],
        },
        "enforce_admins": False,
        "allow_force_pushes": True,
        "allow_deletions": True,
    }
    actual_file = tmp_path / "actual_mismatch.json"
    actual_file.write_text(json.dumps(actual_data), encoding="utf-8")

    cmd = [
        sys.executable,
        str(DIFF_BRANCH_PROT_SCRIPT),
        "--repo",
        "lumiverse-org/pilot-one",
        "--template",
        str(SERVICE_TEMPLATE),
        "--actual-file",
        str(actual_file),
        "--exit-nonzero-on-diff",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "DIFF-BRANCH-PROTECTION MISMATCH" in proc.stderr
    assert "-    \"required_approving_review_count\": 1" in proc.stderr
    assert "+    \"required_approving_review_count\": 0" in proc.stderr


def test_diff_branch_protection_missing_template(tmp_path: pathlib.Path):
    """Fails cleanly when the template file does not exist."""
    missing_template = tmp_path / "missing.json"
    cmd = [
        sys.executable,
        str(DIFF_BRANCH_PROT_SCRIPT),
        "--repo",
        "lumiverse-org/pilot-one",
        "--template",
        str(missing_template),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "template file not found" in proc.stderr
