"""Unit tests for L2-T543: digest_invariant."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "digest"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.digest_invariant", *args]
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_mismatched_digest_fails():
    record = str(FIXTURES_DIR / "staging-aaaa.yaml")
    res = run_tool("--requested", "sha256:bbbb", "--staging-record", record, "--summary")
    assert res.returncode == 2
    assert "FAIL digest_invariant checked=1 failed=1" in res.stdout
    assert "requested='sha256:bbbb'" in res.stderr
    assert "staging_verified='sha256:aaaa'" in res.stderr


def test_matching_digest_passes():
    record = str(FIXTURES_DIR / "staging-aaaa.yaml")
    res = run_tool("--requested", "sha256:aaaa", "--staging-record", record, "--summary")
    assert res.returncode == 0
    assert "OK digest_invariant checked=1 failed=0" in res.stdout


def test_s18_full_identity_accepted():
    record = str(FIXTURES_DIR / "staging-rebuild.yaml")
    res = run_tool("--requested", "sha256:cccc", "--staging-record", record, "--summary")
    assert res.returncode == 0
    assert "OK digest_invariant checked=1 failed=0" in res.stdout
    assert "S18 platform-rebuild equivalence accepted" in res.stderr


def test_s18_partial_identity_fails():
    record = str(FIXTURES_DIR / "staging-rebuild-partial.yaml")
    res = run_tool("--requested", "sha256:cccc", "--staging-record", record, "--summary")
    assert res.returncode == 2
    assert "FAIL digest_invariant checked=1 failed=1" in res.stdout
    assert "S18 platform-rebuild record missing required fields" in res.stderr
    assert "build_configuration" in res.stderr


def test_empty_record_errors():
    record = str(FIXTURES_DIR / "staging-empty.yaml")
    res = run_tool("--requested", "sha256:aaaa", "--staging-record", record, "--summary")
    assert res.returncode == 3
    assert "ERROR digest_invariant checked=0 failed=0" in res.stdout
    assert "staging record has no verified_digest" in res.stderr


def test_missing_record_file_errors():
    record = str(FIXTURES_DIR / "nonexistent.yaml")
    res = run_tool("--requested", "sha256:aaaa", "--staging-record", record, "--summary")
    assert res.returncode == 3
    assert "ERROR digest_invariant checked=0 failed=0" in res.stdout
    assert "staging record not found" in res.stderr


def test_empty_requested_digest_errors():
    record = str(FIXTURES_DIR / "staging-aaaa.yaml")
    res = run_tool("--requested", "", "--staging-record", record, "--summary")
    assert res.returncode == 3
    assert "ERROR digest_invariant checked=0 failed=0" in res.stdout
    assert "requested digest is empty" in res.stderr


def test_no_rebuild_calls_in_source():
    """The module must never contain a build/rebuild/re-tag call (§0.6 rule 1)."""
    source = (REPO_ROOT / "tools" / "evidence" / "digest_invariant.py").read_text()
    import re

    assert re.search(r"docker build|buildx|podman build", source) is None
