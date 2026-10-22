"""R-REF-05 -- residency/region conflict.

Section 15.5 (task L1-310).

Standalone, directly-tested rule function -- see r_svc_01.py for the
FD-094 Option B precedent.
"""
from __future__ import annotations

RULE_ID = "R-REF-05"
SPEC = "Section 15.5"
APPLIES_TO = ["product"]


def _product_id(product_doc: dict) -> str:
    return (product_doc.get("identity") or {}).get("id", "<unknown-product>")


def check(product_doc: dict) -> list[str]:
    if not product_doc:
        return []
    data = product_doc.get("data")
    if not data:
        return []
    residency = data.get("residency")
    region = (product_doc.get("infrastructure") or {}).get("region")
    if residency is None or region is None:
        return []
    if region.startswith(residency):
        return []
    pid = _product_id(product_doc)
    return [
        f"R-REF-05 {pid}: data.residency '{residency}' conflicts with infrastructure.region '{region}' and no resolution is recorded; Section 15.5"
    ]
