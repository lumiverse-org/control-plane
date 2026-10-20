"""R-VER-04 -- a seeded defect case recorded as ``not-run`` that still
carries a run date.

Section 31.2. If ``seeded_defect_case.last_result`` is ``not-run``, the
case has never actually executed, so ``last_run`` recording a date is
self-contradictory -- the two fields disagree about whether the case
ran at all.

Standalone, directly-tested rule function -- see the module docstring of
r_ver_02.py (and, for precedent, r_svc_01.py) for why this is not wired
into the frozen Option B (FD-094) dispatch engine. Exercised directly by
validators/registry/tests/test_r_ver_02.py.
"""
from __future__ import annotations

RULE_ID = "R-VER-04"
SPEC = "Section 31.2"
APPLIES_TO = ["verification-contract"]


def check(contract_doc: dict) -> list[str]:
    """Return a finding when ``last_result`` is ``not-run`` but ``last_run``
    is not null.

    ``contract_doc`` is the parsed ``verification-contract.yaml`` mapping.
    """
    sdc = contract_doc.get("seeded_defect_case") or {}
    if sdc.get("last_result") != "not-run":
        return []
    last_run = sdc.get("last_run")
    if last_run is None:
        return []
    case_id = sdc.get("id", "<unknown>")
    return [
        f"seeded defect case '{case_id}' records a run date of {last_run} "
        f"with last_result not-run"
    ]
