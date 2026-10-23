"""L3-P8-04: wrong-repair freeze and revert branch (spec §53.7; §53.2 Level 5; §28.1).

Spec §53.7, transcribed:
"A repair class discovered to have written incorrect state is a Level 5 escalation
in its own right … freeze that repair class, enumerate its repairs in the affected
window from the repair records of Section 26.4, revert or human-confirm each against
the compensating action its change plan was required to name and test (Section 28.1),
and mark every record produced in the window gap-window until re-verified."
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Sequence

from reconciler.gap.detect import GapWindow
from reconciler.gap.marking import mark
from reconciler.repair.enablement import REPAIR_CLASSES, EnablementError

ACTIONS: tuple[str, ...] = ("freeze", "enumerate", "revert_or_confirm", "mark_gap_window")

FROZEN_CLASSES: set[str] = set()


class WrongRepairError(RuntimeError):
    """Base error for wrong-repair failures."""


class MissingCompensatingActionError(WrongRepairError):
    """Raised when a repair record lacks a compensating action.

    Halt and escalate at Level 5 (§53.7: 'A loop that completed is not
    thereby a loop that was right').
    """


@dataclass
class WrongRepairResult:
    """Result of running on_wrong_repair."""

    repair_class: str
    actions_taken: tuple[str, ...]
    enumerated_repairs: list[Any]
    reversals: list[dict[str, Any]]
    marked_records: list[Any]


def _parse_record_date(record: Any) -> date | None:
    val = None
    if isinstance(record, dict):
        val = (
            record.get("performed_at")
            or record.get("timestamp")
            or record.get("created_at")
            or record.get("date")
        )
    else:
        for attr in ("performed_at", "timestamp", "created_at", "date"):
            if hasattr(record, attr):
                val = getattr(record, attr)
                break
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        iso_str = val.split("T")[0]
        try:
            return date.fromisoformat(iso_str)
        except ValueError:
            return None
    return None


def freeze_repair_class(repair_class: str) -> None:
    """Freeze a repair class: disable it in enablement and track it as frozen."""
    if repair_class in REPAIR_CLASSES:
        REPAIR_CLASSES[repair_class].enabled = False
    FROZEN_CLASSES.add(repair_class)


def on_wrong_repair(
    repair_class: str,
    window: GapWindow,
    repair_records: Sequence[Any] | None = None,
    all_records: Sequence[Any] | None = None,
) -> WrongRepairResult:
    """Execute the four-step wrong-repair response in exact spec order:

    1. freeze: set enabled=False and mark frozen.
    2. enumerate: filter repair records by class and window (never read live state).
    3. revert_or_confirm: check compensating_action on each; halt if absent.
    4. mark_gap_window: mark records produced during the window.
    """
    actions_taken: list[str] = []

    # Step 1: freeze
    freeze_repair_class(repair_class)
    actions_taken.append("freeze")

    # Step 2: enumerate
    enumerated: list[Any] = []
    records_to_scan = repair_records or []
    for rec in records_to_scan:
        cls_id = rec.get("repair_class") if isinstance(rec, dict) else getattr(rec, "repair_class", None)
        if cls_id != repair_class:
            continue
        rec_date = _parse_record_date(rec)
        if rec_date and window.contains(rec_date):
            enumerated.append(rec)
    actions_taken.append("enumerate")

    # Step 3: revert_or_confirm
    reversals: list[dict[str, Any]] = []
    for rec in enumerated:
        comp_action = (
            rec.get("compensating_action")
            if isinstance(rec, dict)
            else getattr(rec, "compensating_action", None)
        )
        if not comp_action or str(comp_action).strip() == "":
            raise MissingCompensatingActionError(
                f"repair record {rec} lacks compensating_action; cannot derive reversal (Level 5 escalation)"
            )
        before_state = rec.get("before") if isinstance(rec, dict) else getattr(rec, "before", None)
        after_state = rec.get("after") if isinstance(rec, dict) else getattr(rec, "after", None)
        scope = rec.get("scope") if isinstance(rec, dict) else getattr(rec, "scope", None)
        reversals.append(
            {
                "scope": scope,
                "revert_to": before_state,
                "revert_from": after_state,
                "compensating_action": str(comp_action),
                "action": "revert",
            }
        )
    actions_taken.append("revert_or_confirm")

    # Step 4: mark_gap_window
    marked: list[Any] = []
    records_to_mark = list(all_records or records_to_scan)
    marked = mark(records_to_mark, window)
    actions_taken.append("mark_gap_window")

    return WrongRepairResult(
        repair_class=repair_class,
        actions_taken=tuple(actions_taken),
        enumerated_repairs=enumerated,
        reversals=reversals,
        marked_records=marked,
    )
