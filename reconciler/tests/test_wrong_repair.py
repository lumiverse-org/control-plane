"""L3-P8-04: tests for wrong-repair freeze and revert branch (spec §53.7)."""

from __future__ import annotations

from datetime import date
import pytest

from reconciler.gap.detect import GapWindow
from reconciler.gap.wrong_repair import (
    ACTIONS,
    MissingCompensatingActionError,
    on_wrong_repair,
    WrongRepairResult,
)
from reconciler.repair.enablement import REPAIR_CLASSES, enable, reset_for_tests

WINDOW = GapWindow(
    kind="reconciliation",
    start=date(2026, 8, 1),
    end=date(2026, 8, 27),
    missed_cycles=2,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    reset_for_tests()
    yield
    reset_for_tests()


def test_actions_constant_has_exact_four_steps_in_order():
    assert ACTIONS == ("freeze", "enumerate", "revert_or_confirm", "mark_gap_window")


def test_freezing_sets_class_disabled():
    enable("team_sync", enabled_on="2026-08-01", enabled_by="DEC-001")
    assert REPAIR_CLASSES["team_sync"].enabled is True

    result = on_wrong_repair("team_sync", WINDOW, repair_records=[])
    assert REPAIR_CLASSES["team_sync"].enabled is False
    assert result.actions_taken[0] == "freeze"


def test_enumeration_reads_repair_records_not_live_state():
    repairs = [
        {
            "repair_class": "team_sync",
            "scope": "alpha:dev-1",
            "performed_at": "2026-08-10T00:00:00Z",
            "before": {"team_member": True},
            "after": {"team_member": False},
            "compensating_action": "re-add dev-1 to alpha",
        }
    ]
    result = on_wrong_repair("team_sync", WINDOW, repair_records=repairs)
    assert len(result.enumerated_repairs) == 1
    assert result.enumerated_repairs[0]["scope"] == "alpha:dev-1"


def test_enumeration_excludes_repairs_outside_window():
    repairs = [
        {
            "repair_class": "team_sync",
            "scope": "alpha:dev-before",
            "performed_at": "2026-07-15T00:00:00Z",
            "compensating_action": "revert",
        },
        {
            "repair_class": "team_sync",
            "scope": "alpha:dev-inside",
            "performed_at": "2026-08-10T00:00:00Z",
            "compensating_action": "revert",
        },
        {
            "repair_class": "team_sync",
            "scope": "alpha:dev-after",
            "performed_at": "2026-09-01T00:00:00Z",
            "compensating_action": "revert",
        },
    ]
    result = on_wrong_repair("team_sync", WINDOW, repair_records=repairs)
    assert len(result.enumerated_repairs) == 1
    assert result.enumerated_repairs[0]["scope"] == "alpha:dev-inside"


def test_enumeration_excludes_other_repair_classes():
    repairs = [
        {
            "repair_class": "team_sync",
            "scope": "alpha:dev-1",
            "performed_at": "2026-08-10T00:00:00Z",
            "compensating_action": "re-add dev-1",
        },
        {
            "repair_class": "codeowners_regen",
            "scope": "alpha",
            "performed_at": "2026-08-10T00:00:00Z",
            "compensating_action": "restore previous CODEOWNERS",
        },
    ]
    result = on_wrong_repair("team_sync", WINDOW, repair_records=repairs)
    assert len(result.enumerated_repairs) == 1
    assert result.enumerated_repairs[0]["repair_class"] == "team_sync"


def test_missing_compensating_action_halts_revert_and_escalates():
    repairs = [
        {
            "repair_class": "team_sync",
            "scope": "alpha:dev-1",
            "performed_at": "2026-08-10T00:00:00Z",
            "compensating_action": None,  # Missing!
        }
    ]
    with pytest.raises(MissingCompensatingActionError, match="lacks compensating_action"):
        on_wrong_repair("team_sync", WINDOW, repair_records=repairs)


def test_empty_string_compensating_action_also_halts_and_escalates():
    repairs = [
        {
            "repair_class": "team_sync",
            "scope": "alpha:dev-1",
            "performed_at": "2026-08-10T00:00:00Z",
            "compensating_action": "   ",  # Whitespace only
        }
    ]
    with pytest.raises(MissingCompensatingActionError):
        on_wrong_repair("team_sync", WINDOW, repair_records=repairs)


def test_revert_or_confirm_derives_compensating_reversal():
    repairs = [
        {
            "repair_class": "team_sync",
            "scope": "alpha:dev-1",
            "performed_at": "2026-08-10T00:00:00Z",
            "before": {"team_member": True},
            "after": {"team_member": False},
            "compensating_action": "re-add dev-1 to the alpha Team",
        }
    ]
    result = on_wrong_repair("team_sync", WINDOW, repair_records=repairs)
    assert len(result.reversals) == 1
    rev = result.reversals[0]
    assert rev["scope"] == "alpha:dev-1"
    assert rev["revert_to"] == {"team_member": True}
    assert rev["revert_from"] == {"team_member": False}
    assert rev["compensating_action"] == "re-add dev-1 to the alpha Team"


def test_marks_all_records_in_window_as_gap_window():
    all_recs = [
        {"id": "rec-1", "timestamp": "2026-08-10T00:00:00Z"},
        {"id": "rec-2", "timestamp": "2026-07-10T00:00:00Z"},
    ]
    result = on_wrong_repair("team_sync", WINDOW, repair_records=[], all_records=all_recs)
    assert all_recs[0].get("gap_window") is True
    assert all_recs[1].get("gap_window") is not True
    assert len(result.marked_records) == 1
