"""14-day delegation expiry warning.

Spec §10.1: delegation expiry is warned, never silent. The lead time is
14 days and is not configurable. An already-expired delegation is not a
warning; that case belongs to the expiry scan's remove_assignment.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from reconciler.orphans.decisions import DELEGATION_WARNING_TYPES

# §10.1 line 787. Not read from a registry. Not the §49.1 asset clock.
WARNING_LEAD_DAYS_DELEGATION = 14

DELEGATION_EXPIRY_WARNING_ISSUED = "delegation expiry warning issued"


@dataclass(frozen=True)
class ExpiryWarning:
    kind: str
    subject: str
    holder: str
    expiry: str
    days_remaining: int
    recipient: str
    detail: str
    open_items: tuple[str, ...]


def _assignment_rows(document: dict[str, Any]) -> list[dict[str, Any]]:
    rows = document.get("assignments") or []
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _iter_scopes(ctx: Any):
    for scope_id, document in sorted((ctx.products or {}).items()):
        yield scope_id, document
    for scope_id, document in sorted((ctx.services or {}).items()):
        yield scope_id, document


def delegation_warnings(ctx: Any) -> list[ExpiryWarning]:
    """Warn when a delegation-type assignment expires within 14 days, inclusive of day 0 and day 14."""
    if DELEGATION_WARNING_TYPES is None:
        raise RuntimeError("DR-L3-05-B unresolved: DELEGATION_WARNING_TYPES is None")
    as_of: date = ctx.as_of
    allowed = set(DELEGATION_WARNING_TYPES)
    warnings: list[ExpiryWarning] = []
    for scope_id, document in _iter_scopes(ctx):
        for assignment in _assignment_rows(document):
            assignment_type = assignment.get("type")
            if assignment_type not in allowed:
                continue
            end_raw = assignment.get("end_date")
            if end_raw in (None, ""):
                continue
            end = date.fromisoformat(str(end_raw))
            days = (end - as_of).days
            if days < 0 or days > WARNING_LEAD_DAYS_DELEGATION:
                continue
            person = str(assignment.get("person") or "")
            subject = f"assignment:{scope_id}/{person}/{assignment_type}"
            warnings.append(
                ExpiryWarning(
                    kind="delegation",
                    subject=subject,
                    holder=person,
                    expiry=end.isoformat(),
                    days_remaining=days,
                    recipient=person,
                    detail=(
                        f"delegation {assignment_type} on {scope_id} held by {person} "
                        f"expires {end.isoformat()} ({days} days)"
                    ),
                    open_items=(),
                )
            )
    warnings.sort(key=lambda item: (item.expiry, item.subject))
    return warnings


def warning_payloads(warnings: list[ExpiryWarning]) -> list[dict[str, Any]]:
    """Payload files only. The event token is the Section 97.3 phrase, verbatim."""
    stamped = datetime.now().astimezone().isoformat(timespec="seconds")
    payloads: list[dict[str, Any]] = []
    for warning in warnings:
        event_type = DELEGATION_EXPIRY_WARNING_ISSUED
        if warning.kind == "temporary_person":
            event_type = "temporary-person expiry warning issued"
        payloads.append(
            {
                "event_type": event_type,
                "event_schema_version": 1,
                "timestamp": stamped,
                "subject": warning.subject,
                "holder": warning.holder,
                "expiry": warning.expiry,
                "days_remaining": warning.days_remaining,
                "recipient": warning.recipient,
                "detail": warning.detail,
                "open_items": list(warning.open_items),
            }
        )
    return payloads
