"""Unit tests for L2-T551: version_monitor (tools.evidence.version_monitor)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.evidence.version_monitor import NON_SERVICE_PROFILES, check_fixture

FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "version"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.version_monitor", *args]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def test_matching_digest_passes():
    fixture = str(FIXTURES_DIR / "match.json")
    res = run_tool("--fixture", fixture, "--summary")
    assert res.returncode == 0
    assert "OK version_monitor checked=1 failed=0" in res.stdout


def test_mismatched_digest_fails_with_p0():
    fixture = str(FIXTURES_DIR / "mismatch.json")
    res = run_tool("--fixture", fixture, "--summary")
    assert res.returncode == 2
    assert "FAIL version_monitor checked=1 failed=1" in res.stdout
    assert "P0_DIGEST_MISMATCH" in res.stderr
    assert "(§41.2)" in res.stderr


def test_unreachable_endpoint_errors():
    fixture = str(FIXTURES_DIR / "unreachable.json")
    res = run_tool("--fixture", fixture, "--summary")
    assert res.returncode == 3
    assert "ERROR version_monitor checked=0 failed=0" in res.stdout
    assert "unreachable is not matching (§41.2)" in res.stderr


def test_client_app_profile_evidence_passes():
    fixture = str(FIXTURES_DIR / "client-app.json")
    res = run_tool("--fixture", fixture, "--summary")
    assert res.returncode == 0
    assert "OK version_monitor checked=1 failed=0" in res.stdout


def test_client_app_without_profile_evidence_fails(tmp_path: Path):
    data = {
        "conformance_profile": "client-app",
        # missing profile_evidence
    }
    fixture_file = tmp_path / "bad_client_app.json"
    fixture_file.write_text(json.dumps(data), encoding="utf-8")

    res = run_tool("--fixture", str(fixture_file), "--summary")
    assert res.returncode == 2
    assert "FAIL version_monitor checked=1 failed=1" in res.stdout
    assert "declares no profile_evidence for item 11" in res.stderr


def test_http_500_status_errors(tmp_path: Path):
    data = {
        "conformance_profile": "service",
        "status_code": 500,
        "approved_digest": "sha256:1111",
        "live_digest": "sha256:1111",
    }
    fixture_file = tmp_path / "http_500.json"
    fixture_file.write_text(json.dumps(data), encoding="utf-8")

    res = run_tool("--fixture", str(fixture_file), "--summary")
    assert res.returncode == 3
    assert "ERROR version_monitor checked=0 failed=0" in res.stdout
    assert "returned HTTP 500" in res.stderr


def test_missing_fixture_file_errors():
    res = run_tool("--fixture", str(FIXTURES_DIR / "nonexistent.json"), "--summary")
    assert res.returncode == 3
    assert "ERROR version_monitor checked=0 failed=0" in res.stdout
    assert "fixture file not found" in res.stderr


def test_non_service_profiles_constant():
    expected = {
        "client-app",
        "library",
        "batch",
        "customer-hosted",
        "white-label",
        "static-site",
    }
    assert NON_SERVICE_PROFILES == expected
