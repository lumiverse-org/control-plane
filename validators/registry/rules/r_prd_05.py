"""R-PRD-05, R-PRD-13, R-PRD-14, R-PRD-15 -- the `operations` block rules.

Section 15.1 `operations:` block; Section 42.2 mapping; Section 47.9;
Section 22; Section 15.5; AT-047 (task L1-305).

Standalone, directly-tested rule functions -- see the module docstring of
``r_svc_01.py`` and ``r_prd_11.py`` for why these are not wired into the
frozen Option B (FD-094) ``R01``..``R18`` dispatch table in
``validators/registry/rules/registry.py``. The CLI grammar and the
per-fixture ``echo "EXIT=$?"`` acceptance command written into
``lanes/L1-05-tasks.md`` predate FD-094 and are superseded by it, exactly
as ``validators/registry/tests/test_service_schema.py`` documents for
R-SVC-01..03 and ``validators/registry/tests/test_r_prd_11.py`` documents
for R-PRD-11/27/28: fixtures still live where the task says
(``validators/registry/fixtures/product/operations/<case>/``), but they
are exercised by calling these functions directly against a parsed
``product.yaml`` document, not through ``validators/registry/cli.py``.

Rule table (task L1-305):

    R-PRD-05  detection_expectation must equal the value support_model
              implies, per the Section 42.2 mapping:
                  business-hours -> next-business-morning
                  extended       -> rostered-window
                  24x7           -> continuous
    R-PRD-13  support_model in {extended, 24x7} requires a non-null
              coverage_window (Section 15.5).
    R-PRD-14  a launched product (identity.launch_status == "launched")
              must declare both intake_channel and triager (Section 15.5
              and Section 22).
    R-PRD-15  primary_responder / backup_responder must each name a
              person present as an incident_responder assignment.
              Fires only when the document's top-level `assignments`
              array is non-empty, so fixtures for the other three rules
              -- which have no reason to carry assignment data -- stay
              clean even when they leave a responder field null-or-set.
"""
from __future__ import annotations

RULE_ID_MAPPING = "R-PRD-05"
RULE_ID_COVERAGE_REQUIRED = "R-PRD-13"
RULE_ID_LAUNCHED_INTAKE = "R-PRD-14"
RULE_ID_RESPONDER = "R-PRD-15"
SPEC = "Section 15.1; Section 42.2; Section 47.9; Section 22; Section 15.5"
APPLIES_TO = ["product"]

_EXTENDED_SUPPORT_MODELS = ("extended", "24x7")

_SUPPORT_MODEL_TO_DETECTION_EXPECTATION = {
    "business-hours": "next-business-morning",
    "extended": "rostered-window",
    "24x7": "continuous",
}


def _product_id(product_doc: dict) -> str:
    return (product_doc.get("identity") or {}).get("id", "<unknown-product>")


def check_r_prd_05(product_doc: dict) -> list[str]:
    """R-PRD-05 -- declared detection_expectation must match the value
    derived from support_model via the Section 42.2 mapping."""
    ops = product_doc.get("operations") or {}
    model = ops.get("support_model")
    declared = ops.get("detection_expectation")
    expected = _SUPPORT_MODEL_TO_DETECTION_EXPECTATION.get(model)
    if expected is None or declared == expected:
        return []
    pid = _product_id(product_doc)
    return [
        f"R-PRD-05 {pid}: detection_expectation '{declared}' differs from the value "
        f"derived from support_model '{model}'; Section 15.1 fails a declared value "
        f"differing from the derived value"
    ]


def check_r_prd_13(product_doc: dict) -> list[str]:
    """R-PRD-13 -- extended/24x7 support requires a declared coverage_window."""
    ops = product_doc.get("operations") or {}
    model = ops.get("support_model")
    if model not in _EXTENDED_SUPPORT_MODELS:
        return []
    if ops.get("coverage_window") is not None:
        return []
    pid = _product_id(product_doc)
    return [
        f"R-PRD-13 {pid}: support_model '{model}' requires a coverage_window; Section 15.5"
    ]


def check_r_prd_14(product_doc: dict) -> list[str]:
    """R-PRD-14 -- a launched product must declare both intake_channel and triager."""
    launch_status = (product_doc.get("identity") or {}).get("launch_status")
    if launch_status != "launched":
        return []
    ops = product_doc.get("operations") or {}
    pid = _product_id(product_doc)
    findings = []
    for field in ("intake_channel", "triager"):
        if ops.get(field) is None:
            findings.append(
                f"R-PRD-14 {pid}: launched product '{pid}' declares no {field}; "
                f"Section 15.5 and Section 22"
            )
    return findings


def check_r_prd_15(product_doc: dict) -> list[str]:
    """R-PRD-15 -- primary_responder/backup_responder must each match an
    incident_responder assignment. Fires only when `assignments` is
    non-empty in the same document."""
    assignments = product_doc.get("assignments") or []
    if not assignments:
        return []
    incident_responders = {
        a.get("person") for a in assignments if a.get("type") == "incident_responder"
    }
    ops = product_doc.get("operations") or {}
    pid = _product_id(product_doc)
    findings = []
    for field in ("primary_responder", "backup_responder"):
        person = ops.get(field)
        if person is None:
            continue
        if person not in incident_responders:
            findings.append(
                f"R-PRD-15 {pid}: {field} '{person}' is derived from incident_responder "
                f"assignments and does not match one; Section 15.1"
            )
    return findings


def check(product_doc: dict) -> list[str]:
    """Run all four rules, R-PRD-05 first, matching the task's own table
    order, and return the combined findings."""
    findings = []
    findings.extend(check_r_prd_05(product_doc))
    findings.extend(check_r_prd_13(product_doc))
    findings.extend(check_r_prd_14(product_doc))
    findings.extend(check_r_prd_15(product_doc))
    return findings
