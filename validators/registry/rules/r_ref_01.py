"""R-REF-01 -- assignment names person missing from people.yaml or departed.

Section 15.5; SIG-02 (task L1-310).

Standalone, directly-tested rule function -- see r_svc_01.py for the
FD-094 Option B precedent.
"""
from __future__ import annotations

RULE_ID = "R-REF-01"
SPEC = "Section 15.5; SIG-02"
APPLIES_TO = ["product", "people"]


def _product_id(product_doc: dict) -> str:
    return (product_doc.get("identity") or {}).get("id", "<unknown-product>")


def check(product_doc: dict, people_doc: dict | None) -> list[str]:
    if people_doc is None or product_doc is None:
        return []
    pid = _product_id(product_doc)
    people_index = {
        p.get("id"): p
        for p in (people_doc.get("people") or [])
        if isinstance(p, dict)
    }
    findings = []
    for a in product_doc.get("assignments") or []:
        if not isinstance(a, dict):
            continue
        person_id = a.get("person")
        atype = a.get("type", "<unknown-type>")
        if person_id not in people_index:
            findings.append(
                f"R-REF-01 {pid}: assignment '{atype}' names person '{person_id}' which does not exist in people.yaml; Section 15.5"
            )
        elif people_index[person_id].get("availability") == "departed":
            findings.append(
                f"R-REF-01 {pid}: assignment '{atype}' names person '{person_id}' which is departed; Section 15.5"
            )
    return findings
