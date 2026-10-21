"""R-VER-11: Transitional product migration block completeness.

Spec anchor: Section 60.3; Invariant 74.
Task: lanes/L1-05-tasks.md, L1-702.

A product declaring platform_compatibility: transitional must declare a
platform_migration block with owner, target_contract_version, and deadline.
"""
from __future__ import annotations

RULE_ID = "R-VER-11"
SPEC = "Section 60.3"
APPLIES_TO = ["product", "platform"]
_REQUIRED_MIGRATION_FIELDS = ("owner", "target_contract_version", "deadline")


def _product_id(product_doc: dict) -> str:
    return (product_doc.get("identity") or {}).get("id", "<unknown-product>")


def check(product_doc: dict, platform_doc: dict | None = None, today=None) -> list[str]:
    if not product_doc:
        return []
    if product_doc.get("platform_compatibility") != "transitional":
        return []
    migration = product_doc.get("platform_migration")
    pid = _product_id(product_doc)
    if migration is None:
        return [
            f"transitional product '{pid}' declares no platform_migration; "
            f"Section 60.3 and invariant 74"
        ]
    findings = []
    for field in _REQUIRED_MIGRATION_FIELDS:
        if migration.get(field) is None:
            findings.append(
                f"transitional product '{pid}' declares no {field}; "
                f"Section 60.3 and invariant 74"
            )
    return findings
