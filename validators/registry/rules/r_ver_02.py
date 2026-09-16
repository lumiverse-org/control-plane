"""R-VER-02 -- a seeded defect case that passed on its last run.

Section 31.2: "A run in which the seeded defect passes is a FAILED run,
not a clean one" (SIG-18). If ``seeded_defect_case.last_result`` reads
``passed-unexpectedly``, the seeded-canary discipline has stopped
discriminating and the contract itself is broken, independent of any
other result on the build.

Standalone, directly-tested rule function -- see the module docstring of
r_svc_01.py for why this is not wired into the frozen Option B (FD-094)
dispatch engine (validators/registry/rules/registry.py, R01..R18). FD-094
(contracts/validator-contract.md) freezes that rule catalogue and its CLI
grammar; the L1-005 discover()/RULE_ID/APPLIES_TO harness this module's
constants describe was never built (validators/registry/rules/__init__.py
is empty in this tree) and extending R01..R18 for R-VER-02 is not this
task's call to make. This module is exercised directly by
validators/registry/tests/test_r_ver_02.py against the fixtures in
validators/registry/fixtures/ver02/, exactly as test_service_schema.py
documents for R-SVC-01..03 and test_r_prd_11.py documents for
R-PRD-11/27/28.
"""
from __future__ import annotations

RULE_ID = "R-VER-02"
SPEC = "Section 31.2"
APPLIES_TO = ["verification-contract"]


def check(contract_doc: dict) -> list[str]:
    """Return a finding when the seeded defect case passed unexpectedly.

    ``contract_doc`` is the parsed ``verification-contract.yaml`` mapping.
    """
    sdc = contract_doc.get("seeded_defect_case") or {}
    if sdc.get("last_result") != "passed-unexpectedly":
        return []
    case_id = sdc.get("id", "<unknown>")
    return [
        f"seeded defect case '{case_id}' passed on its last run; the "
        f"contract has stopped discriminating; Section 31.2, SIG-18"
    ]
