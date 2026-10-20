"""R-VER-05 -- a seeded defect case that claims a result with no run date.

Section 31.2. Any ``last_result`` other than ``not-run`` (i.e. the case
claims to have actually executed and produced ``failed-as-expected`` or
``passed-unexpectedly``) must carry the date it ran on; a claimed result
with ``last_run`` null is unsupported.

Standalone, directly-tested rule function -- see the module docstring of
r_ver_02.py (and, for precedent, r_svc_01.py) for why this is not wired
into the frozen Option B (FD-094) dispatch engine. Exercised directly by
validators/registry/tests/test_r_ver_02.py.
"""
from __future__ import annotations

RULE_ID = "R-VER-05"
SPEC = "Section 31.2"
APPLIES_TO = ["verification-contract"]


def check(contract_doc: dict) -> list[str]:
    """Return a finding when ``last_result`` is not ``not-run`` but
    ``last_run`` is null.

    ``contract_doc`` is the parsed ``verification-contract.yaml`` mapping.
    """
    sdc = contract_doc.get("seeded_defect_case") or {}
    result = sdc.get("last_result")
    if result == "not-run":
        return []
    if sdc.get("last_run") is not None:
        return []
    case_id = sdc.get("id", "<unknown>")
    return [
        f"seeded defect case '{case_id}' claims result '{result}' with no "
        f"run date"
    ]
