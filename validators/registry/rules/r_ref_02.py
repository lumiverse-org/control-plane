"""R-REF-02 -- assignment past its end_date.

Section 15.5; SIG-02 (task L1-310).

Standalone, directly-tested rule function -- see r_svc_01.py for the
FD-094 Option B precedent.
"""
from __future__ import annotations

import datetime

RULE_ID = "R-REF-02"
SPEC = "Section 15.5; SIG-02"
APPLIES_TO = ["product"]


def _product_id(product_doc: dict) -> str:
    return (product_doc.get("identity") or {}).get("id", "<unknown-product>")


def _as_date(value) -> datetime.date:
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(str(value)[:10])


def check(product_doc: dict, today) -> list[str]:
    if today is None or product_doc is None:
        return []
    today_date = _as_date(today)
    pid = _product_id(product_doc)
    findings = []
    for a in product_doc.get("assignments") or []:
        if not isinstance(a, dict):
            continue
        end_date_raw = a.get("end_date")
        if end_date_raw is None:
            continue
        end_date = _as_date(end_date_raw)
        if end_date < today_date:
            person_id = a.get("person")
            atype = a.get("type", "<unknown-type>")
            findings.append(
                f"R-REF-02 {pid}: assignment '{atype}' for '{person_id}' expired on {end_date}; Section 15.5 and SIG-02"
            )
    return findings
