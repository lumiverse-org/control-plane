"""R-REF-03 -- dependency on a shared service absent from the registry.

Section 20.1 (task L1-310).

Standalone, directly-tested rule function -- see r_svc_01.py for the
FD-094 Option B precedent.
"""
from __future__ import annotations

RULE_ID = "R-REF-03"
SPEC = "Section 20.1"
APPLIES_TO = ["product", "service"]


def _product_id(product_doc: dict) -> str:
    return (product_doc.get("identity") or {}).get("id", "<unknown-product>")


def check(product_doc: dict, known_service_ids) -> list[str]:
    if known_service_ids is None or product_doc is None:
        return []
    known = set(known_service_ids)
    pid = _product_id(product_doc)
    findings = []
    for svc in (product_doc.get("dependencies") or {}).get("internal") or []:
        if svc not in known:
            findings.append(
                f"R-REF-03 {pid}: dependency '{svc}' names a shared service absent from the registry; Section 20.1"
            )
    return findings
