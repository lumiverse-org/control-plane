"""Unit tests for L2-T550: verify_digest_chain (tools.evidence.verify_digest_chain)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.evidence.verify_digest_chain import sweep

FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "sweep"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.verify_digest_chain", *args]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def test_clean_estate_sweep_passes():
    estate_dir = str(FIXTURES_DIR / "clean")
    res = run_tool("--estate", estate_dir, "--summary")
    assert res.returncode == 0
    assert "OK verify_digest_chain checked=3 failed=0" in res.stdout
    assert "OK: product 'product-alpha' chain is closed" in res.stderr
    assert "OK: product 'product-beta' chain is closed" in res.stderr
    assert "OK: product 'product-gamma' chain is closed" in res.stderr


def test_one_broken_estate_sweep_fails():
    estate_dir = str(FIXTURES_DIR / "one-broken")
    res = run_tool("--estate", estate_dir, "--summary")
    assert res.returncode == 2
    assert "FAIL verify_digest_chain checked=3 failed=1" in res.stdout
    assert "product 'product-beta' chain does not close" in res.stderr


def test_empty_estate_errors():
    estate_dir = str(FIXTURES_DIR / "empty")
    res = run_tool("--estate", estate_dir, "--summary")
    assert res.returncode == 3
    assert "ERROR verify_digest_chain checked=0 failed=0" in res.stdout
    assert "an empty estate is not a clean estate (§46.1)" in res.stderr


def test_nonexistent_estate_dir_errors():
    estate_dir = str(FIXTURES_DIR / "nonexistent_dir")
    res = run_tool("--estate", estate_dir, "--summary")
    assert res.returncode == 3
    assert "ERROR verify_digest_chain checked=0 failed=0" in res.stdout
    assert "estate directory not found" in res.stderr


def test_corrupt_record_in_estate_reports_failure(tmp_path: Path):
    estate_dir = tmp_path / "corrupt_estate"
    estate_dir.mkdir()
    corrupt_file = estate_dir / "bad-prod.yaml"
    corrupt_file.write_text("not a yaml mapping\n- item 1\n", encoding="utf-8")

    res = run_tool("--estate", str(estate_dir), "--summary")
    assert res.returncode == 2
    assert "FAIL verify_digest_chain checked=1 failed=1" in res.stdout
    assert "record is not a YAML mapping" in res.stderr


def test_sweep_unit_clean():
    estate_dir = str(FIXTURES_DIR / "clean")
    checked, failed = sweep(estate_dir)
    assert checked == 3
    assert failed == 0


def test_sweep_unit_broken():
    estate_dir = str(FIXTURES_DIR / "one-broken")
    checked, failed = sweep(estate_dir)
    assert checked == 3
    assert failed == 1
