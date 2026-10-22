"""Unit tests for L4-P4-03: record emission (tools.records.record_write).
Master Spec v4.0 Section 97.2 lines 8890–8892; L4-06-tasks.md row L4-P4-03; FD-131.
"""
from __future__ import annotations

import pathlib
import sys
import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.records.record_write import emit_record, validate_record_dict, main


def test_validate_record_clean():
    doc = {
        "record_schema_version": 1,
        "id": "UAT-2026-10-22-001",
        "product": "test-product",
        "timestamp": "2026-10-22T08:00:00+00:00",
        "result": "pass",
        "executed_by": "qa-lead",
    }
    validate_record_dict(doc, expected_id="UAT-2026-10-22-001")


def test_validate_record_seeded_missing_envelope():
    doc = {
        "record_schema_version": 1,
        "id": "UAT-001",
        # missing product
        "timestamp": "2026-10-22T08:00:00+00:00",
    }
    with pytest.raises(ValueError, match="missing-envelope-field:product"):
        validate_record_dict(doc, expected_id="UAT-001")


def test_validate_record_seeded_naive_timestamp():
    doc = {
        "record_schema_version": 1,
        "id": "UAT-001",
        "product": "test-product",
        "timestamp": "2026-10-22T08:00:00",
    }
    with pytest.raises(ValueError, match="timestamp-without-utc-offset"):
        validate_record_dict(doc, expected_id="UAT-001")


def test_validate_record_seeded_d88_display_name():
    doc = {
        "record_schema_version": 1,
        "id": "UAT-001",
        "product": "test-product",
        "timestamp": "2026-10-22T08:00:00+00:00",
        "executed_by": "Priya Raman",  # D88 violation
    }
    with pytest.raises(ValueError, match="d88-display-name-rejected"):
        validate_record_dict(doc, expected_id="UAT-001")


def test_emit_record_live_write_and_overwrite_refusal(tmp_path: pathlib.Path):
    cpr = tmp_path / "cpr"
    uat_dir = cpr / "records" / "uat"
    uat_dir.mkdir(parents=True)

    body_file = tmp_path / "uat_body.yaml"
    body_data = {
        "record_schema_version": 1,
        "id": "UAT-2026-10-22-001",
        "product": "test-product",
        "timestamp": "2026-10-22T08:00:00+00:00",
        "result": "pass",
    }
    body_file.write_text(yaml.safe_dump(body_data), encoding="utf-8")

    # First write passes
    out = emit_record(
        store="uat",
        record_id="UAT-2026-10-22-001",
        body_path=str(body_file),
        cpr_root=str(cpr),
    )
    assert out.is_file()
    assert out.name == "UAT-2026-10-22-001.yaml"

    # Second write over the same file must be refused (Invariant 48)
    with pytest.raises(FileExistsError, match="overwrite-refused"):
        emit_record(
            store="uat",
            record_id="UAT-2026-10-22-001",
            body_path=str(body_file),
            cpr_root=str(cpr),
        )


def test_record_write_cli_validate_only():
    fixture = REPO_ROOT / "tools" / "records" / "fixtures" / "valid" / "uat.yaml"
    exit_code = main(["--validate-only", "--from-file", str(fixture)])
    assert exit_code == 0
