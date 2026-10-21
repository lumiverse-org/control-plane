"""Unit tests for L2-T518: profile_evidence."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "profile"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.profile_evidence", *args]
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_client_app_fixture_mode_passes():
    res = run_tool("--profile", "client-app", "--summary")
    assert res.returncode == 0
    assert "OK profile_evidence checked=2 failed=0" in res.stdout


def test_client_app_complete_evidence_file_passes():
    evidence = str(FIXTURES_DIR / "client-app-complete.yaml")
    res = run_tool("--profile", "client-app", "--evidence-file", evidence, "--summary")
    assert res.returncode == 0
    assert "OK profile_evidence checked=2 failed=0" in res.stdout


def test_client_app_missing_adoption_fails():
    evidence = str(FIXTURES_DIR / "client-app-missing-adoption.yaml")
    res = run_tool("--profile", "client-app", "--evidence-file", evidence, "--summary")
    assert res.returncode == 2
    assert "FAIL profile_evidence checked=2 failed=1" in res.stdout
    assert "evidence-chain item 11 missing" in res.stderr
    assert "store_version_adoption" in res.stderr


def test_unknown_profile_errors():
    res = run_tool("--profile", "mobile-app", "--summary")
    assert res.returncode == 3
    assert "ERROR profile_evidence checked=0 failed=0" in res.stdout
    assert "unknown conformance profile 'mobile-app'" in res.stderr


def test_no_profile_defaults_to_service():
    res = run_tool("--summary")
    assert res.returncode == 0
    assert "OK profile_evidence checked=2 failed=0" in res.stdout
    assert "defaulting to 'service'" in res.stderr


def test_exactly_seven_profiles_declared():
    source = (REPO_ROOT / "tools" / "evidence" / "profile_evidence.py").read_text(encoding="utf-8")
    import re

    matches = re.findall(
        r'^\s*"(service|client-app|library|batch|customer-hosted|white-label|static-site)":',
        source,
        flags=re.MULTILINE,
    )
    assert len(matches) == 7
