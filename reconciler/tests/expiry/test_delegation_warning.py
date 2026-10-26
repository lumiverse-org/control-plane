"""L3-P0-DEL14: 14-day delegation expiry warning."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from reconciler.expiry.warnings import (
    WARNING_LEAD_DAYS_DELEGATION,
    delegation_warnings,
    warning_payloads,
)
from reconciler.orphans.loader import load_control_plane

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "expiry"
AS_OF = date(2026, 8, 27)


def _ctx(name: str):
    return load_control_plane(FIXTURES / name, AS_OF, "current")


def test_lead_time_is_fourteen_days():
    assert WARNING_LEAD_DAYS_DELEGATION == 14


def test_window_includes_day_0_and_day_14_only():
    warnings = delegation_warnings(_ctx("DELEGATION-WARN"))
    days = [item.days_remaining for item in sorted(warnings, key=lambda item: item.days_remaining)]
    assert days == [0, 14]
    assert warning_payloads(warnings)[0]["event_type"] == "delegation expiry warning issued"


def test_non_delegation_types_never_warn():
    assert delegation_warnings(_ctx("DELEGATION-NO-WARN")) == []
