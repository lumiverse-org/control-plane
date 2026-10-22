"""Unit tests for L4-P4-05: event append (tools.records.event_append).
Master Spec v4.0 Section 97.3 lines 8929–8947; L4-06-tasks.md row L4-P4-05; FD-131.
"""
from __future__ import annotations

import pathlib
import sys
import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.records.event_append import emit_event, load_event_types, validate_event_dict, main


def test_load_event_types_contains_canonical():
    types = load_event_types(cp_root=REPO_ROOT)
    assert "uat_executed" in types
    assert "restore_test_executed" in types
    assert "work_item_created" in types
    assert len(types) >= 86


def test_validate_event_dict_clean():
    doc = {
        "event_schema_version": 1,
        "event_id": "EVT-2026-10-22-000001",
        "event_type": "uat_executed",
        "occurred_at": "2026-10-22T08:00:00+00:00",
        "recorded_at": "2026-10-22T08:00:05+00:00",
        "actor": "qa-lead",
        "product": "test-product",
        "subject_ref": "records/uat/UAT-2026-10-22-001.yaml",
        "payload": {"result": "pass"},
    }
    validate_event_dict(doc, cp_root=REPO_ROOT)


def test_validate_event_seeded_unknown_event_type():
    doc = {
        "event_schema_version": 1,
        "event_id": "EVT-2026-10-22-000001",
        "event_type": "not_a_real_event_type",
        "occurred_at": "2026-10-22T08:00:00+00:00",
        "recorded_at": "2026-10-22T08:00:05+00:00",
        "actor": "qa-lead",
        "product": "test-product",
        "subject_ref": "records/uat/UAT-001.yaml",
        "payload": {},
    }
    with pytest.raises(ValueError, match="unknown-event-type not_a_real_event_type"):
        validate_event_dict(doc, cp_root=REPO_ROOT)


def test_validate_event_seeded_missing_envelope():
    doc = {
        "event_schema_version": 1,
        "event_id": "EVT-001",
        "event_type": "uat_executed",
        # missing actor, occurred_at, etc.
    }
    with pytest.raises(ValueError, match="missing-envelope-field"):
        validate_event_dict(doc, cp_root=REPO_ROOT)


def test_emit_event_live_write_and_overwrite_refusal(tmp_path: pathlib.Path):
    cpr = tmp_path / "cpr"

    out = emit_event(
        event_type="uat_executed",
        actor="qa-engineer",
        product="test-prod",
        subject_ref="records/uat/UAT-001.yaml",
        payload_input={"test": "ok"},
        cpr_root=str(cpr),
        cp_root=REPO_ROOT,
        event_id="EVT-2026-10-22-000099",
        occurred_at="2026-10-22T08:00:00+00:00",
    )
    assert out.is_file()
    assert out.name == "EVT-2026-10-22-000099.yaml"

    # Second write with same event_id must be refused (Invariant 48)
    with pytest.raises(FileExistsError, match="overwrite-refused"):
        emit_event(
            event_type="uat_executed",
            actor="qa-engineer",
            product="test-prod",
            subject_ref="records/uat/UAT-001.yaml",
            payload_input={"test": "duplicate"},
            cpr_root=str(cpr),
            cp_root=REPO_ROOT,
            event_id="EVT-2026-10-22-000099",
            occurred_at="2026-10-22T08:00:00+00:00",
        )
