"""L3-P8-03: gap-window marking (spec §53.7 bullet 5).

Spec §53.7 bullet 5, verbatim:
"Every record produced during the gap window carries the gap-window mark
until re-verified; a gap-window record is not evidence for any gate until
re-verification clears the mark."
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Sequence

from reconciler.gap.detect import GapWindow


def _parse_record_date(record: Any) -> date | None:
    val = None
    if isinstance(record, dict):
        val = (
            record.get("timestamp")
            or record.get("performed_at")
            or record.get("created_at")
            or record.get("date")
        )
    else:
        for attr in ("timestamp", "performed_at", "created_at", "date"):
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


def mark(records: Sequence[Any], window: GapWindow) -> list[Any]:
    """Tag every record produced during the gap window with gap_window=True.

    Records outside the window remain unmarked.
    Returns the list of marked records.
    """
    marked_records: list[Any] = []
    for rec in records:
        rec_date = _parse_record_date(rec)
        if rec_date and window.contains(rec_date):
            if isinstance(rec, dict):
                rec["gap_window"] = True
            else:
                setattr(rec, "gap_window", True)
            marked_records.append(rec)
    return marked_records


def clear(record: Any, verifier: str, at: date | datetime | str) -> Any:
    """Clear the gap_window mark through explicit re-verification.

    Requires an explicit verifier identifier and the verification timestamp.
    The mark never clears automatically by time passing.
    """
    if not verifier:
        raise ValueError("clear: verifier identity is required for explicit re-verification")
    if not at:
        raise ValueError("clear: verification timestamp 'at' is required")

    at_str = at.isoformat() if hasattr(at, "isoformat") else str(at)

    if isinstance(record, dict):
        record["gap_window"] = False
        record["reverified_by"] = verifier
        record["reverified_at"] = at_str
    else:
        setattr(record, "gap_window", False)
        setattr(record, "reverified_by", verifier)
        setattr(record, "reverified_at", at_str)

    return record


def is_gate_evidence(record: Any) -> bool:
    """Return True if the record is valid gate evidence.

    Returns False whenever gap_window mark is True (spec §53.7 bullet 5:
    a gap-window record is not evidence for any gate until re-verification
    clears the mark).
    """
    if isinstance(record, dict):
        if record.get("gap_window") is True:
            return False
    else:
        if getattr(record, "gap_window", False) is True:
            return False
    return True
