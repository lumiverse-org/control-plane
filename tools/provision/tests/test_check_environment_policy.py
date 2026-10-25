"""Unit tests for tools/provision/check-environment-policy (CP-0106, Section 33.4)."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CHECK_ENV_POLICY_SCRIPT = REPO_ROOT / "tools" / "provision" / "check-environment-policy"


def test_check_environment_policy_happy_path(tmp_path: pathlib.Path):
    """Passes when both staging and production environments exist with custom_branch_policies
    restricting strictly to default branch and protected release tags (Section 33.4)."""
    fixture_data = {
        "default_branch": "main",
        "environments": [
            {
                "name": "staging",
                "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True},
                "policies": [
                    {"id": 1, "name": "main", "type": "branch"},
                    {"id": 2, "name": "v*", "type": "tag"},
                ],
            },
            {
                "name": "production",
                "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True},
                "policies": [
                    {"id": 3, "name": "main", "type": "branch"},
                    {"id": 4, "name": "v*", "type": "tag"},
                ],
            },
        ]
    }
    fixture_file = tmp_path / "envs_valid.json"
    fixture_file.write_text(json.dumps(fixture_data), encoding="utf-8")

    cmd = [
        sys.executable,
        str(CHECK_ENV_POLICY_SCRIPT),
        "--repo",
        "lumiverse-org/pilot-one",
        "--env",
        "staging",
        "--env",
        "production",
        "--expect",
        "default-branch,protected-tags",
        "--fixture-file",
        str(fixture_file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "CHECK-ENVIRONMENT-POLICY OK" in proc.stdout
    assert "staging, production" in proc.stdout


def test_check_environment_policy_rejects_extra_unrestricted_ref(tmp_path: pathlib.Path):
    """Fails when an extra unrestricted ref (e.g. '*' or 'feature/anything-goes') is present (Bug A Scenario 1)."""
    fixture_data = {
        "default_branch": "main",
        "environments": [
            {
                "name": "staging",
                "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True},
                "policies": [
                    {"id": 1, "name": "main", "type": "branch"},
                    {"id": 2, "name": "v*", "type": "tag"},
                    {"id": 3, "name": "feature/anything-goes", "type": "branch"},
                ],
            },
            {
                "name": "production",
                "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True},
                "policies": [
                    {"id": 4, "name": "main", "type": "branch"},
                    {"id": 5, "name": "*", "type": "tag"},  # bare wildcard tag
                ],
            },
        ]
    }
    fixture_file = tmp_path / "envs_extra_ref.json"
    fixture_file.write_text(json.dumps(fixture_data), encoding="utf-8")

    cmd = [
        sys.executable,
        str(CHECK_ENV_POLICY_SCRIPT),
        "--repo",
        "lumiverse-org/pilot-one",
        "--env",
        "staging",
        "--env",
        "production",
        "--expect",
        "default-branch,protected-tags",
        "--fixture-file",
        str(fixture_file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "CHECK-ENVIRONMENT-POLICY FAIL" in proc.stderr
    assert "unauthorized branch policy 'feature/anything-goes'" in proc.stderr
    assert "unrestricted wildcard tag policy '*'" in proc.stderr


def test_check_environment_policy_rejects_nonsense_and_typeless_entries(tmp_path: pathlib.Path):
    """Fails when policy entries have no 'type' key or nonsense names like 'veto-whatever' (Bug A Scenario 2)."""
    fixture_data = {
        "default_branch": "main",
        "environments": [
            {
                "name": "staging",
                "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True},
                "policies": [
                    {"id": 1, "name": "zzz-totally-unrelated-entry"},  # missing type
                    {"id": 2, "name": "veto-whatever", "type": "tag"},  # starts with 'v' but not release tag
                ],
            },
            {
                "name": "production",
                "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True},
                "policies": [
                    {"id": 3, "name": "main", "type": "branch"},
                    {"id": 4, "name": "v*", "type": "tag"},
                ],
            },
        ]
    }
    fixture_file = tmp_path / "envs_nonsense.json"
    fixture_file.write_text(json.dumps(fixture_data), encoding="utf-8")

    cmd = [
        sys.executable,
        str(CHECK_ENV_POLICY_SCRIPT),
        "--repo",
        "lumiverse-org/pilot-one",
        "--env",
        "staging",
        "--env",
        "production",
        "--expect",
        "default-branch,protected-tags",
        "--fixture-file",
        str(fixture_file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "CHECK-ENVIRONMENT-POLICY FAIL" in proc.stderr
    assert "missing or invalid type" in proc.stderr
    assert "unauthorized tag policy 'veto-whatever'" in proc.stderr


def test_check_environment_policy_rejects_protected_branches_mode(tmp_path: pathlib.Path):
    """Fails when environment has protected_branches: true instead of custom_branch_policies: true (Bug B)."""
    fixture_data = {
        "default_branch": "main",
        "environments": [
            {
                "name": "staging",
                "deployment_branch_policy": {"protected_branches": True, "custom_branch_policies": False},
                "policies": [],
            },
            {
                "name": "production",
                "deployment_branch_policy": {"protected_branches": True, "custom_branch_policies": False},
                "policies": [],
            },
        ]
    }
    fixture_file = tmp_path / "envs_protected_branches.json"
    fixture_file.write_text(json.dumps(fixture_data), encoding="utf-8")

    cmd = [
        sys.executable,
        str(CHECK_ENV_POLICY_SCRIPT),
        "--repo",
        "lumiverse-org/pilot-one",
        "--env",
        "staging",
        "--env",
        "production",
        "--expect",
        "default-branch,protected-tags",
        "--fixture-file",
        str(fixture_file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "CHECK-ENVIRONMENT-POLICY FAIL" in proc.stderr
    assert "protected_branches: true" in proc.stderr
    assert "lacks 'custom_branch_policies: true'" in proc.stderr


def test_check_environment_policy_missing_environment(tmp_path: pathlib.Path):
    """Fails when one of the required environments is missing."""
    fixture_data = {
        "environments": [
            {
                "name": "staging",
                "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True},
                "policies": [
                    {"id": 1, "name": "main", "type": "branch"},
                    {"id": 2, "name": "v*", "type": "tag"},
                ],
            }
        ]
    }
    fixture_file = tmp_path / "envs_missing.json"
    fixture_file.write_text(json.dumps(fixture_data), encoding="utf-8")

    cmd = [
        sys.executable,
        str(CHECK_ENV_POLICY_SCRIPT),
        "--repo",
        "lumiverse-org/pilot-one",
        "--env",
        "staging",
        "--env",
        "production",
        "--expect",
        "default-branch,protected-tags",
        "--fixture-file",
        str(fixture_file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "CHECK-ENVIRONMENT-POLICY FAIL" in proc.stderr
    assert "environment 'production' does not exist" in proc.stderr


def test_check_environment_policy_missing_tag_policy(tmp_path: pathlib.Path):
    """Fails when an environment lacks the required protected-tags policy (§33.4)."""
    fixture_data = {
        "environments": [
            {
                "name": "staging",
                "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True},
                "policies": [
                    {"id": 1, "name": "main", "type": "branch"},
                ],
            },
            {
                "name": "production",
                "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True},
                "policies": [
                    {"id": 2, "name": "main", "type": "branch"},
                ],
            },
        ]
    }
    fixture_file = tmp_path / "envs_no_tags.json"
    fixture_file.write_text(json.dumps(fixture_data), encoding="utf-8")

    cmd = [
        sys.executable,
        str(CHECK_ENV_POLICY_SCRIPT),
        "--repo",
        "lumiverse-org/pilot-one",
        "--env",
        "staging",
        "--env",
        "production",
        "--expect",
        "default-branch,protected-tags",
        "--fixture-file",
        str(fixture_file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "CHECK-ENVIRONMENT-POLICY FAIL" in proc.stderr
    assert "lacks policy restricting deployments to protected release tags" in proc.stderr
