"""R-VER-01: Product contract version supported by platform.

Spec anchor: Section 60.3; Invariant 74.
Task: lanes/L1-05-tasks.md, L1-702.

A product declaring platform_compatibility: supported must declare a
contract_version that appears in platform.yaml's supported_contract_versions.product list.
"""
from __future__ import annotations

RULE_ID = "R-VER-01"
SPEC = "Section 60.3"
APPLIES_TO = ["product", "platform"]


def _product_id(product_doc: dict) -> str:
    return (product_doc.get("identity") or {}).get("id", "<unknown-product>")


def check(product_doc: dict, platform_doc: dict | None = None, today=None) -> list[str]:
    if not product_doc or not platform_doc:
        return []
    if product_doc.get("platform_compatibility") != "supported":
        return []
    contract_version = product_doc.get("contract_version")
    supported = (platform_doc.get("supported_contract_versions") or {}).get("product") or []
    if contract_version in supported:
        return []
    pid = _product_id(product_doc)
    return [
        f"product '{pid}' declares platform_compatibility supported at "
        f"contract_version {contract_version}, which is not in the supported "
        f"set {supported}; Section 60.3"
    ]
