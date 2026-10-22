"""Unit tests for L2-T544: records_client."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "records"


def run_tool(*args: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.records_client", *args]
    return subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def test_dry_run_valid_payload_ok():
    payload = str(FIXTURES_DIR / "deployment.yaml")
    res = run_tool("--dry-run", "--kind", "deployment", "--payload", payload, "--summary")
    assert res.returncode == 0
    assert "OK records_client checked=9 failed=0" in res.stdout
    assert "DRY-RUN: payload valid; would write to" in res.stderr


def test_dry_run_missing_digest_fails():
    payload = str(FIXTURES_DIR / "deployment-missing-digest.yaml")
    res = run_tool("--dry-run", "--kind", "deployment", "--payload", payload, "--summary")
    assert res.returncode == 2
    assert "FAIL records_client checked=9 failed=1" in res.stdout
    assert "FAIL: required field 'digest' missing or empty in deployment record" in res.stderr


def test_refuses_to_overwrite_existing_record(tmp_path: Path):
    payload = str(FIXTURES_DIR / "deployment-existing-path.yaml")
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}

    # Run dry-run to get deterministic path
    res = run_tool(
        "--dry-run",
        "--kind",
        "deployment",
        "--payload",
        payload,
        "--summary",
        cwd=tmp_path,
        env=env,
    )
    assert res.returncode == 0
    match = re.search(r"would write to (\S+)", res.stderr)
    assert match is not None
    target_rel = match.group(1)

    target_file = tmp_path / target_rel
    target_file.parent.mkdir(parents=True, exist_ok=True)
    sentinel = b"PRE-EXISTING - DO NOT OVERWRITE\n"
    target_file.write_bytes(sentinel)

    # Now run live write against tmp_path
    res_live = run_tool(
        "--kind",
        "deployment",
        "--payload",
        payload,
        "--summary",
        cwd=tmp_path,
        env=env,
    )
    assert res_live.returncode == 2
    assert "FAIL records_client checked=9 failed=1" in res_live.stdout
    assert "already exists" in res_live.stderr
    assert "invariant 48" in res_live.stderr

    # Sentinel must be unchanged
    assert target_file.read_bytes() == sentinel


def test_no_literal_token_in_source():
    src = (REPO_ROOT / "tools" / "evidence" / "records_client.py").read_text(encoding="utf-8")
    assert re.search(r"gh[pousr]_[A-Za-z0-9]{16,}", src) is None


def test_missing_payload_file_errors():
    payload = str(FIXTURES_DIR / "nonexistent.yaml")
    res = run_tool("--kind", "deployment", "--payload", payload, "--summary")
    assert res.returncode == 3
    assert "ERROR records_client checked=0 failed=0" in res.stdout
    assert "payload not found" in res.stderr
