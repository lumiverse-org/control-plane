"""Unit tests for L4-P4-01: writer library (tools.records.lib.writer).
Master Spec v4.0 Section 97.1 line 8839; L4-06-tasks.md row L4-P4-01; FD-131.
"""
from __future__ import annotations

import pathlib
import sys
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.records.lib.writer import (
    assert_utc_offset,
    mint_id,
    record_path,
    resolve_id_prefix,
    utc_day,
    utc_now,
)


def test_utc_now_format_and_offset():
    now_str = utc_now()
    assert "+00:00" in now_str or now_str.endswith("Z")
    # assert_utc_offset should pass cleanly
    assert_utc_offset(now_str)


def test_utc_day_format():
    day_str = utc_day()
    assert len(day_str) == 10
    parts = day_str.split("-")
    assert len(parts) == 3
    assert len(parts[0]) == 4 and len(parts[1]) == 2 and len(parts[2]) == 2


def test_assert_utc_offset_valid():
    assert_utc_offset("2026-10-22T08:00:00+00:00")
    assert_utc_offset("2026-10-22T08:00:00Z")
    assert_utc_offset("2026-10-22T03:00:00-05:00")


def test_assert_utc_offset_seeded_failures():
    # Seeded failure 1: missing offset completely
    with pytest.raises(ValueError, match="timestamp-without-utc-offset"):
        assert_utc_offset("2026-10-22T08:00:00")

    # Seeded failure 2: invalid type
    with pytest.raises(ValueError, match="timestamp must be a string"):
        assert_utc_offset(123456789)


def test_resolve_id_prefix():
    assert resolve_id_prefix("uat", cp_root=REPO_ROOT) == "UAT"
    assert resolve_id_prefix("restore-tests", cp_root=REPO_ROOT) == "RST"
    assert resolve_id_prefix("incidents", cp_root=REPO_ROOT) == "INC"
    assert resolve_id_prefix("deployments", cp_root=REPO_ROOT) == "DEP"


def test_mint_id_default_and_custom(tmp_path: pathlib.Path):
    id_1 = mint_id("uat", cp_root=REPO_ROOT, date_str="2026-10-22", seq=1)
    assert id_1 == "UAT-2026-10-22-001"

    id_42 = mint_id("restore-tests", cp_root=REPO_ROOT, date_str="2026-10-22", seq=42)
    assert id_42 == "RST-2026-10-22-042"


def test_mint_id_auto_increment(tmp_path: pathlib.Path):
    # Setup temporary CPR directory with existing UAT records
    uat_dir = tmp_path / "records" / "uat"
    uat_dir.mkdir(parents=True)
    (uat_dir / "UAT-2026-10-22-001.yaml").write_text("dummy", encoding="utf-8")
    (uat_dir / "UAT-2026-10-22-002.yaml").write_text("dummy", encoding="utf-8")

    next_id = mint_id("uat", cpr_root=tmp_path, cp_root=REPO_ROOT, date_str="2026-10-22")
    assert next_id == "UAT-2026-10-22-003"


def test_record_path():
    path = record_path("uat", "UAT-2026-10-22-001")
    assert path == "records/uat/UAT-2026-10-22-001.yaml"
