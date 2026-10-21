"""R-PRD-06, R-PRD-16, R-PRD-17 -- the `commitments` block rules.

Section 21.1 code block; Section 21.4; Section 15.5; invariant 111
(task L1-306).

Standalone, directly-tested rule functions -- see the module docstring of
``r_svc_01.py`` and ``r_prd_05.py`` for why these are not wired into the
frozen Option B (FD-094) ``R01``..``R18`` dispatch table in
``validators/registry/rules/registry.py``. Fixtures live at
``validators/registry/fixtures/product/commitments/<case>/`` and are
exercised by calling ``check`` directly against a parsed ``product.yaml``
document, not through ``validators/registry/cli.py``.

Rule table (task L1-306):

    R-PRD-06  conflict_check absent or not one of the two tokens
              (passed, waived-with-decision); Section 15.5.
    R-PRD-16  support_commitment stricter than operations.support_model,
              ordering business-hours < extended < 24x7; Section 21.4.
    R-PRD-17  data_commitments.residency present, data.residency present,
              and the two values unequal; Section 21.4.

Not in this module: the Section 21.4 uptime-SLA feasibility computation
(worst-case undetected window plus RTO against the downtime budget). That
needs the company working calendar, which lives in Lane 4's leave
records (Section 52.6) -- Lane 1 cannot read it (PARTITION rule 4). Per
the task doc, this is deferred to the check-commitment CLI, subsystem B,
out of Lane 1 scope without a contracts/ calendar interface.
"""
from __future__ import annotations

RULE_ID_CONFLICT_CHECK = "R-PRD-06"
RULE_ID_SUPPORT_STRICTNESS = "R-PRD-16"
RULE_ID_RESIDENCY = "R-PRD-17"
SPEC = "Section 21.1; Section 21.4; Section 15.5; invariant 111"
APPLIES_TO = ["product"]

_SUPPORT_ORDER = {"business-hours": 0, "extended": 1, "24x7": 2}
_VALID_CONFLICT_CHECK_TOKENS = ("passed", "waived-with-decision")


def _product_id(product_doc: dict) -> str:
    return (product_doc.get("identity") or {}).get("id", "<unknown-product>")


def _customer(commitment: dict) -> str:
    return commitment.get("customer", "<unknown-customer>")


def check_r_prd_06(product_doc: dict) -> list[str]:
    """R-PRD-06 -- every commitment must record conflict_check as one of
    the two valid tokens."""
    pid = _product_id(product_doc)
    findings = []
    for commitment in product_doc.get("commitments") or []:
        if commitment.get("conflict_check") in _VALID_CONFLICT_CHECK_TOKENS:
            continue
        findings.append(
            f"R-PRD-06 {pid}: commitment for '{_customer(commitment)}' records "
            f"neither passed nor waived-with-decision; Section 15.5"
        )
    return findings


def check_r_prd_16(product_doc: dict) -> list[str]:
    """R-PRD-16 -- a commitment must not promise stricter support than the
    product's declared operations.support_model."""
    declared = (product_doc.get("operations") or {}).get("support_model")
    declared_rank = _SUPPORT_ORDER.get(declared)
    if declared_rank is None:
        return []
    pid = _product_id(product_doc)
    findings = []
    for commitment in product_doc.get("commitments") or []:
        promised = commitment.get("support_commitment")
        promised_rank = _SUPPORT_ORDER.get(promised)
        if promised_rank is None or promised_rank <= declared_rank:
            continue
        findings.append(
            f"R-PRD-16 {pid}: commitment promises '{promised}' support while the "
            f"product operates '{declared}'; Section 21.4"
        )
    return findings


def check_r_prd_17(product_doc: dict) -> list[str]:
    """R-PRD-17 -- a commitment's promised data residency must not
    contradict the product's declared data.residency."""
    declared = (product_doc.get("data") or {}).get("residency")
    if declared is None:
        return []
    pid = _product_id(product_doc)
    findings = []
    for commitment in product_doc.get("commitments") or []:
        data_commitments = commitment.get("data_commitments")
        if not data_commitments:
            continue
        promised = data_commitments.get("residency")
        if promised is None or promised == declared:
            continue
        findings.append(
            f"R-PRD-17 {pid}: commitment promises residency '{promised}' while the "
            f"data block declares '{declared}'; Section 21.4"
        )
    return findings


def check(product_doc: dict) -> list[str]:
    """Run all three rules, R-PRD-06 first, matching the task's own table
    order, and return the combined findings."""
    findings = []
    findings.extend(check_r_prd_06(product_doc))
    findings.extend(check_r_prd_16(product_doc))
    findings.extend(check_r_prd_17(product_doc))
    return findings
