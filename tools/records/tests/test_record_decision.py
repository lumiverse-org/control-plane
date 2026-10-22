"""Unit tests for L4-P4-07: record-decision CLI and library.
Master Spec v4.0 Section 97.2 lines 8865–8866; Section 99.2 line 9230; L4-06-tasks.md row L4-P4-07; FD-131.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import pytest
import yaml
import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.records.lib.decision import (
    create_pending_decision,
    decide_pending_decision,
    mint_decision_id,
)
from tools.records.record_decision import main


@pytest.fixture
def schemas():
    pending_path = REPO_ROOT / "schemas" / "records" / "decision-pending.schema.json"
    decided_path = REPO_ROOT / "schemas" / "records" / "decision.schema.json"
    base_path = REPO_ROOT / "schemas" / "records" / "record.base.schema.json"

    with open(pending_path, encoding="utf-8") as f:
        pending_schema = json.load(f)
    with open(decided_path, encoding="utf-8") as f:
        decided_schema = json.load(f)
    with open(base_path, encoding="utf-8") as f:
        base_schema = json.load(f)

    return pending_schema, decided_schema, base_schema


def test_pending_decision_clean(tmp_path: Path, schemas):
    pending_schema, _, _ = schemas
    records_root = tmp_path / "cpr"

    record = create_pending_decision(
        records_root=records_root,
        product="product-1",
        decider="founder",
        subject="Architecture Decision for Cache Layer",
        decision_id="DEC-2026-10-22-001",
        timestamp="2026-10-22T08:00:00+00:00",
        prompt_received="2026-10-22",
        options_considered=["Option A: Redis", "Option B: Memcached"],
        evidence=["docs/adr/001.md"],
    )

    pending_file = records_root / "records" / "decisions" / "pending" / "DEC-2026-10-22-001.yaml"
    assert pending_file.is_file()

    with open(pending_file, "r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f)

    assert loaded["id"] == "DEC-2026-10-22-001"
    assert loaded["decider"] == "founder"
    assert loaded["subject"] == "Architecture Decision for Cache Layer"


def test_pending_decision_seeded_bad_id(tmp_path: Path):
    with pytest.raises(ValueError, match="invalid-decision-id"):
        create_pending_decision(
            records_root=tmp_path,
            product="product-1",
            decider="founder",
            subject="Test Bad ID",
            decision_id="DEC-BAD-001",
        )


def test_pending_decision_seeded_d88_display_name(tmp_path: Path):
    with pytest.raises(ValueError, match="d88-display-name-rejected"):
        create_pending_decision(
            records_root=tmp_path,
            product="product-1",
            decider="Priya Raman",  # D88 violation
            subject="Test Display Name",
            decision_id="DEC-2026-10-22-002",
        )


def test_pending_decision_seeded_naive_timestamp(tmp_path: Path):
    with pytest.raises(ValueError, match="timestamp-without-utc-offset"):
        create_pending_decision(
            records_root=tmp_path,
            product="product-1",
            decider="founder",
            subject="Test Naive Timestamp",
            decision_id="DEC-2026-10-22-003",
            timestamp="2026-10-22T08:00:00",  # missing UTC offset
        )


def test_decide_decision_clean(tmp_path: Path):
    records_root = tmp_path / "cpr"

    # 1. Create pending
    create_pending_decision(
        records_root=records_root,
        product="product-1",
        decider="founder",
        subject="Database Choice",
        decision_id="DEC-2026-10-22-010",
        timestamp="2026-10-22T08:00:00+00:00",
        prompt_received="2026-10-20",
    )

    pending_file = records_root / "records" / "decisions" / "pending" / "DEC-2026-10-22-010.yaml"
    pending_mtime_before = pending_file.stat().st_mtime_ns

    # 2. Decide
    decided = decide_pending_decision(
        records_root=records_root,
        decision_id="DEC-2026-10-22-010",
        options_considered=["Postgres", "MySQL"],
        evidence=["https://example.com/eval.pdf"],
        decided="2026-10-22",
        review_date="2027-10-22",
        timestamp="2026-10-22T10:00:00+00:00",
    )

    assert decided["id"] == "DEC-2026-10-22-010"
    assert decided["decided"] == "2026-10-22"

    decided_file = records_root / "records" / "decisions" / "DEC-2026-10-22-010.yaml"
    assert decided_file.is_file()

    # Invariant 48: pending file was NOT modified in place
    pending_mtime_after = pending_file.stat().st_mtime_ns
    assert pending_mtime_before == pending_mtime_after

    # Superseded record exists
    superseded_file = records_root / "records" / "decisions" / "pending" / "DEC-2026-10-22-010.superseded.yaml"
    assert superseded_file.is_file()


def test_decide_missing_pending_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="pending-decision-not-found"):
        decide_pending_decision(
            records_root=tmp_path,
            decision_id="DEC-2026-10-22-999",
            options_considered=["A"],
            evidence=["ev.md"],
        )


def test_overwrite_refusal(tmp_path: Path):
    records_root = tmp_path / "cpr"

    create_pending_decision(
        records_root=records_root,
        product="product-1",
        decider="founder",
        subject="Duplicate Test",
        decision_id="DEC-2026-10-22-050",
    )

    # Second write must raise FileExistsError (invariant 48)
    with pytest.raises(FileExistsError):
        create_pending_decision(
            records_root=records_root,
            product="product-1",
            decider="founder",
            subject="Duplicate Test 2",
            decision_id="DEC-2026-10-22-050",
        )


def test_cli_subcommands(tmp_path: Path):
    records_root = tmp_path / "cpr"

    # CLI pending
    rc = main([
        "--records-root", str(records_root),
        "pending",
        "--product", "product-2",
        "--decider", "team-lead",
        "--subject", "CLI Pending Test",
        "--id", "DEC-2026-10-22-060",
    ])
    assert rc == 0
    assert (records_root / "records" / "decisions" / "pending" / "DEC-2026-10-22-060.yaml").is_file()

    # CLI decide
    rc = main([
        "--records-root", str(records_root),
        "decide",
        "--id", "DEC-2026-10-22-060",
        "--options", "Option 1", "Option 2",
        "--evidence", "doc1.md",
    ])
    assert rc == 0
    assert (records_root / "records" / "decisions" / "DEC-2026-10-22-060.yaml").is_file()
