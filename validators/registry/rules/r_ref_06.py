"""R-REF-06 -- orphan structure (no active primary_owner / cross_reviewer / incident_responder).

SIG-05; invariant 7 (task L1-310).

Standalone, directly-tested rule function -- see r_svc_01.py for the
FD-094 Option B precedent.
"""
from __future__ import annotations

import datetime

RULE_ID = "R-REF-06"
SPEC = "SIG-05; invariant 7"
APPLIES_TO = ["product", "people"]

_REQUIRED_ROLES = ("primary_owner", "cross_reviewer", "incident_responder")


def _product_id(product_doc: dict) -> str:
    return (product_doc.get("identity") or {}).get("id", "<unknown-product>")


def _as_date(value) -> datetime.date:
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(str(value)[:10])


def check(product_doc: dict, people_doc: dict | None, today) -> list[str]:
    if people_doc is None or product_doc is None:
        return []
    today_date = _as_date(today)
    pid = _product_id(product_doc)
    people_index = {
        p.get("id"): p
        for p in (people_doc.get("people") or [])
        if isinstance(p, dict)
    }

    active_assignments_by_role = {role: [] for role in _REQUIRED_ROLES}
    for a in product_doc.get("assignments") or []:
        if not isinstance(a, dict):
            continue
        atype = a.get("type")
        if atype not in active_assignments_by_role:
            continue
        end_date_raw = a.get("end_date")
        if end_date_raw is not None and _as_date(end_date_raw) < today_date:
            continue
        person_id = a.get("person")
        person = people_index.get(person_id)
        if not person:
            continue
        avail = person.get("availability")
        if avail in ("active", "on_leave"):
            active_assignments_by_role[atype].append(person_id)

    findings = []
    for role in _REQUIRED_ROLES:
        if not active_assignments_by_role[role]:
            findings.append(
                f"R-REF-06 {pid}: product '{pid}' has no active {role}; SIG-05 orphan risk, invariant 7"
            )
    return findings
