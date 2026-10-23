"""Unit tests for L2-T552: restore_rotation (tools.evidence.restore_rotation)."""
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

from tools.evidence.restore_rotation import (
    WINDOW_CRITICAL_DAYS,
    WINDOW_FLOOR_DAYS,
    _get_window_days,
    compute,
)

FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "rotation"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.restore_rotation", *args]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def test_clean_estate_passes_within_windows(tmp_path: Path):
    clean_estate = {
        "products": [
            {
                "name": "product-alpha",
                "classification": {"reliability_criticality": "critical"},
            },
            {
                "name": "product-gamma",
                "classification": {"reliability_criticality": "standard"},
            },
        ]
    }
    estate_file = tmp_path / "clean_estate.yaml"
    estate_file.write_text(yaml.safe_dump(clean_estate), encoding="utf-8")

    # On 2026-08-20:
    # alpha: tested 2026-07-30 + 30d = 2026-08-29 (9 days remaining)
    # gamma: tested 2026-05-30 + 90d = 2026-08-28 (8 days remaining)
    res = run_tool(
        "--estate", str(estate_file),
        "--as-of", "2026-08-20",
        "--records-dir", str(FIXTURES_DIR / "records"),
        "--summary",
    )
    assert res.returncode == 0
    assert "OK restore_rotation checked=2 failed=0" in res.stdout
    assert "OK: product 'product-alpha'" in res.stderr
    assert "OK: product 'product-gamma'" in res.stderr


def test_hand_edited_date_drift_fails():
    # estate.yaml has product-delta with declared restore_tested '2026-08-26', differing from derived '2026-08-20'
    estate_file = str(FIXTURES_DIR / "estate.yaml")
    res = run_tool(
        "--estate", estate_file,
        "--as-of", "2026-08-20",
        "--records-dir", str(FIXTURES_DIR / "records"),
        "--summary",
    )
    assert res.returncode == 2
    assert "FAIL restore_rotation checked=4 failed=1" in res.stdout
    assert "differs from derived date" in res.stderr
    assert "a hand-edited date is drift" in res.stderr


def test_overdue_product_fails():
    # On 2026-08-27:
    # beta: tested 2026-07-27 + 30d = 2026-08-26 (1 day overdue!)
    # delta: hand-edited drift
    estate_file = str(FIXTURES_DIR / "estate.yaml")
    res = run_tool(
        "--estate", estate_file,
        "--as-of", "2026-08-27",
        "--records-dir", str(FIXTURES_DIR / "records"),
        "--summary",
    )
    assert res.returncode == 2
    assert "FAIL restore_rotation checked=4 failed=2" in res.stdout
    assert "product 'product-beta' is past its 30-day restore window" in res.stderr


def test_missing_estate_file_errors():
    res = run_tool(
        "--estate", str(FIXTURES_DIR / "nonexistent.yaml"),
        "--as-of", "2026-08-20",
        "--summary",
    )
    assert res.returncode == 3
    assert "ERROR restore_rotation checked=0 failed=0" in res.stdout
    assert "estate file not found" in res.stderr


def test_invalid_as_of_date_errors():
    estate_file = str(FIXTURES_DIR / "estate.yaml")
    res = run_tool(
        "--estate", estate_file,
        "--as-of", "not-a-valid-date",
        "--summary",
    )
    assert res.returncode == 3
    assert "ERROR restore_rotation checked=0 failed=0" in res.stdout
    assert "invalid --as-of date" in res.stderr


def test_product_with_no_restore_records_fails(tmp_path: Path):
    untested_estate = {
        "products": [
            {
                "name": "product-never-tested",
                "classification": {"reliability_criticality": "standard"},
            }
        ]
    }
    estate_file = tmp_path / "untested_estate.yaml"
    estate_file.write_text(yaml.safe_dump(untested_estate), encoding="utf-8")

    res = run_tool(
        "--estate", str(estate_file),
        "--as-of", "2026-08-20",
        "--records-dir", str(FIXTURES_DIR / "records"),
        "--summary",
    )
    assert res.returncode == 2
    assert "FAIL restore_rotation checked=1 failed=1" in res.stdout
    assert "has no passing restore record" in res.stderr


def test_window_days_never_exceeds_90():
    assert _get_window_days("critical") == WINDOW_CRITICAL_DAYS == 30
    assert _get_window_days("standard") == WINDOW_FLOOR_DAYS == 90
    assert _get_window_days("low") == 90
    assert _get_window_days("unknown_value") == 90
