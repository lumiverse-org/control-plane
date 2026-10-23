"""R-VER-13: Unsupported product compatibility blocks deployment.

Spec anchor: Section 60.3; Invariant 74.
Task: lanes/L1-05-tasks.md, L1-702.

A product declaring platform_compatibility: unsupported is blocked.
"""
from __future__ import annotations

RULE_ID = "R-VER-13"
SPEC = "Section 60.3"
APPLIES_TO = ["product", "platform"]


def _product_id(product_doc: dict) -> str:
    return (product_doc.get("identity") or {}).get("id", "<unknown-product>")


def check(product_doc: dict, platform_doc: dict | None = None, today=None) -> list[str]:
    if not product_doc:
        return []
    if product_doc.get("platform_compatibility") != "unsupported":
        return []
    pid = _product_id(product_doc)
    return [
        f"product '{pid}' is unsupported; Section 60.3 blocks deployment "
        f"until it migrates"
    ]
