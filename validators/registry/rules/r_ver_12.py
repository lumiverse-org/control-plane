"""R-VER-12: Transitional product migration deadline not past.

Spec anchor: Section 60.3; SIG-10; Invariant 74.
Task: lanes/L1-05-tasks.md, L1-702.

A product declaring platform_compatibility: transitional must not have a
platform_migration.deadline strictly before today.
"""
from __future__ import annotations

from datetime import date

RULE_ID = "R-VER-12"
SPEC = "Section 60.3"
APPLIES_TO = ["product", "platform"]


def _product_id(product_doc: dict) -> str:
    return (product_doc.get("identity") or {}).get("id", "<unknown-product>")


def check(product_doc: dict, platform_doc: dict | None = None, today=None) -> list[str]:
    if not product_doc:
        return []
    if product_doc.get("platform_compatibility") != "transitional":
        return []
    migration = product_doc.get("platform_migration") or {}
    deadline_raw = migration.get("deadline")
    if deadline_raw is None:
        return []

    if isinstance(today, date):
        today_date = today
    else:
        try:
            today_date = date.fromisoformat(str(today))
        except (TypeError, ValueError):
            return [f"R-VER-12: invalid --today/--as-of date: {today!r}"]

    if isinstance(deadline_raw, date):
        deadline_date = deadline_raw
    else:
        try:
            deadline_date = date.fromisoformat(str(deadline_raw))
        except ValueError:
            return []

    if deadline_date >= today_date:
        return []

    pid = _product_id(product_doc)
    return [
        f"transitional product '{pid}' is past its migration deadline "
        f"{deadline_raw}; Section 60.3, SIG-10, invariant 74"
    ]
