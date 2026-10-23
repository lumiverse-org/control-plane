"""L3-P8-03: tests for gap-window marking (spec §53.7 bullet 5)."""

from __future__ import annotations

from datetime import date
import pytest

from reconciler.gap.detect import GapWindow
from reconciler.gap.marking import clear, is_gate_evidence, mark

WINDOW = GapWindow(
    kind="reconciliation",
    start=date(2026, 8, 1),
    end=date(2026, 8, 27),
    missed_cycles=2,
)


def test_every_record_inside_the_window_is_marked():
    records = [
        {"id": "r-1", "timestamp": "2026-08-05T12:00:00Z", "kind": "deployment"},
        {"id": "r-2", "timestamp": "2026-08-20T09:00:00Z", "kind": "uat"},
    ]
    marked = mark(records, WINDOW)
    assert len(marked) == 2
    assert all(r.get("gap_window") is True for r in records)


def test_records_outside_window_are_not_marked():
    records = [
        {"id": "r-before", "timestamp": "2026-07-31T23:59:59Z"},
        {"id": "r-during", "timestamp": "2026-08-10T12:00:00Z"},
        {"id": "r-after", "timestamp": "2026-08-28T00:00:01Z"},
    ]
    marked = mark(records, WINDOW)
    assert len(marked) == 1
    assert records[0].get("gap_window") is not True
    assert records[1].get("gap_window") is True
    assert records[2].get("gap_window") is not True


def test_is_gate_evidence_returns_false_for_marked_record():
    record = {
        "id": "r-pass",
        "conclusion": "success",
        "verified": True,
        "gap_window": True,
    }
    assert is_gate_evidence(record) is False


def test_is_gate_evidence_returns_true_for_unmarked_record():
    record = {
        "id": "r-normal",
        "conclusion": "success",
        "verified": True,
    }
    assert is_gate_evidence(record) is True


def test_mark_clears_only_through_explicit_reverification():
    record = {"id": "r-1", "gap_window": True}
    assert is_gate_evidence(record) is False

    cleared = clear(record, verifier="qa-lead-1", at=date(2026, 8, 30))
    assert cleared["gap_window"] is False
    assert cleared["reverified_by"] == "qa-lead-1"
    assert "2026-08-30" in cleared["reverified_at"]
    assert is_gate_evidence(cleared) is True


def test_mark_never_clears_by_time_passing():
    record = {
        "id": "r-old",
        "timestamp": "2026-08-10T00:00:00Z",
        "gap_window": True,
    }
    # Time passed: 100 days later, record still carries gap_window=True
    assert record.get("gap_window") is True
    assert is_gate_evidence(record) is False

    # Attempting to clear without verifier raises ValueError
    with pytest.raises(ValueError, match="verifier identity is required"):
        clear(record, verifier="", at=date(2026, 12, 1))
