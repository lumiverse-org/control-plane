"""R-REF-04 -- unsupported contract_version.

Section 60.2 (task L1-310).

Standalone, directly-tested rule function -- see r_svc_01.py for the
FD-094 Option B precedent.
"""
from __future__ import annotations

RULE_ID = "R-REF-04"
SPEC = "Section 60.2"
APPLIES_TO = ["product", "platform"]


def _product_id(product_doc: dict) -> str:
    return (product_doc.get("identity") or {}).get("id", "<unknown-product>")


def check(product_doc: dict, platform_doc: dict | None) -> list[str]:
    if platform_doc is None or product_doc is None:
        return []
    pid = _product_id(product_doc)
    supported = (
        (platform_doc.get("supported_contract_versions") or {}).get("product")
    ) or []
    version = product_doc.get("contract_version")
    if version not in supported:
        return [
            f"R-REF-04 {pid}: contract_version {version} is not in the supported set {supported}; Section 60.2"
        ]
    return []
