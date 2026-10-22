"""R-PRD-07, R-PRD-18, R-PRD-19 -- the `recovery` block rules.

Section 15.1 `recovery:`; Section 15.4; Section 15.5; Section 44.1;
Section 44.3; invariant 3; invariant 4; SIG-17 (task L1-307).

Standalone, directly-tested rule functions -- see the module docstring of
``r_svc_01.py`` and ``r_prd_05.py`` for why these are not wired into the
frozen Option B (FD-094) ``R01``..``R18`` dispatch table in
``validators/registry/rules/registry.py``. The CLI grammar and the
per-fixture ``echo "BOUNDARY_OK_EXIT=$?"`` acceptance command written into
``lanes/L1-05-tasks.md`` predate FD-094 and are superseded by it, exactly
as ``validators/registry/tests/test_r_prd_05.py`` documents: fixtures
still live where the task says
(``validators/registry/fixtures/product/recovery/<case>/``), but they are
exercised by calling these functions directly against a parsed
``product.yaml`` document, not through ``validators/registry/cli.py``.

Rule table (task L1-307):

    R-PRD-07  ``today - restore_tested`` exceeds the cadence required by
              classification.reliability_criticality -- 90 days for
              low/medium/high, 30 days for critical (Section 15.4,
              invariant 4). Strictly ``>`` -- a document exactly at the
              floor still passes.
    R-PRD-18  recovery.encrypted is false (Section 15.1).
    R-PRD-19  recovery.backup_retention_days < 1 -- already rejected by
              the schema's own ``minimum: 1``; this rule exists only to
              give invariant 3 a named register entry and cannot fire
              against a schema-valid document.

``recovery: null`` is schema-legal for every conformance_profile -- all
three rules below are silent when ``recovery`` is null or absent.
Enforcing that null is only legal for ``static-site`` is Section 15.7 /
R-PRD-08 (task L1-308), not this module.
"""
from __future__ import annotations

import datetime

RULE_ID_CADENCE = "R-PRD-07"
RULE_ID_ENCRYPTED = "R-PRD-18"
RULE_ID_RETENTION = "R-PRD-19"
SPEC = "Section 15.1; Section 15.4; Section 15.5; Section 44.1; Section 44.3; invariant 3; invariant 4; SIG-17"
APPLIES_TO = ["product"]

_CADENCE_DAYS_BY_CRITICALITY = {
    "low": 90,
    "medium": 90,
    "high": 90,
    "critical": 30,
}


def _product_id(product_doc: dict) -> str:
    return (product_doc.get("identity") or {}).get("id", "<unknown-product>")


def check_r_prd_07(product_doc: dict, today: datetime.date) -> list[str]:
    """R-PRD-07 -- restore_tested older than the cadence
    reliability_criticality requires. `today` is passed in explicitly
    (never datetime.date.today()) so fixtures never drift -- the task's
    own fixtures are all authored against 2026-08-27."""
    recovery = product_doc.get("recovery")
    if recovery is None:
        return []
    restore_tested = recovery.get("restore_tested")
    if restore_tested is None:
        return []
    criticality = (product_doc.get("classification") or {}).get("reliability_criticality")
    cadence = _CADENCE_DAYS_BY_CRITICALITY.get(criticality)
    if cadence is None:
        return []
    tested_date = datetime.date.fromisoformat(str(restore_tested)[:10])
    age_days = (today - tested_date).days
    if age_days <= cadence:
        return []
    pid = _product_id(product_doc)
    return [
        f"R-PRD-07 {pid}: restore_tested {tested_date.isoformat()} is {age_days} days old; "
        f"the required cadence for reliability_criticality '{criticality}' is {cadence} days; "
        f"Section 15.4 and invariant 4"
    ]


def check_r_prd_18(product_doc: dict) -> list[str]:
    """R-PRD-18 -- recovery.encrypted is false."""
    recovery = product_doc.get("recovery")
    if recovery is None:
        return []
    if recovery.get("encrypted") is not False:
        return []
    pid = _product_id(product_doc)
    return [
        f"R-PRD-18 {pid}: recovery declares unencrypted backups; Section 15.1 requires encryption"
    ]


def check_r_prd_19(product_doc: dict) -> list[str]:
    """R-PRD-19 -- backup_retention_days < 1. Already schema-blocked
    (minimum: 1); kept for the invariant register only, per the task's
    own description of this rule. Not expected to fire against any
    schema-valid fixture."""
    recovery = product_doc.get("recovery")
    if recovery is None:
        return []
    retention = recovery.get("backup_retention_days")
    if retention is None or retention >= 1:
        return []
    pid = _product_id(product_doc)
    return [
        f"R-PRD-19 {pid}: backup retention below one day is no backup; invariant 3"
    ]


def check(product_doc: dict, today: datetime.date) -> list[str]:
    """Run all three rules, R-PRD-07 first, matching the task's own table
    order, and return the combined findings."""
    findings = []
    findings.extend(check_r_prd_07(product_doc, today))
    findings.extend(check_r_prd_18(product_doc))
    findings.extend(check_r_prd_19(product_doc))
    return findings
