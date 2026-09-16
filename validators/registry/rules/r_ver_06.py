"""R-VER-06 -- a requirement mapped to a mechanism the contract declares
``not-applicable``.

Section 31.2, SIG-18: the other half of SIG-18 -- "Requirements shipped
without a mapped verification mechanism" -- needs the shipped-requirement
list, which lives in the record store (Lane 4, ``records/**``, Section
52.6). Lane 1 cannot read it (PARTITION.md rule 4). This rule covers the
part that is fully inside the contract: a ``coverage_map[]`` entry that
points at a mechanism the same contract has switched off in
``mechanisms``.

Standalone, directly-tested rule function -- see the module docstring of
r_ver_02.py (and, for precedent, r_svc_01.py) for why this is not wired
into the frozen Option B (FD-094) dispatch engine. Exercised directly by
validators/registry/tests/test_r_ver_02.py.
"""
from __future__ import annotations

RULE_ID = "R-VER-06"
SPEC = "Section 31.2"
APPLIES_TO = ["verification-contract"]


def check(contract_doc: dict) -> list[str]:
    """Return one finding per ``coverage_map[]`` entry whose ``mechanism``
    is declared ``not-applicable`` in ``mechanisms``.

    ``contract_doc`` is the parsed ``verification-contract.yaml`` mapping.
    """
    mechanisms = contract_doc.get("mechanisms") or {}
    findings = []
    for entry in contract_doc.get("coverage_map") or []:
        mechanism = entry.get("mechanism")
        if mechanisms.get(mechanism) != "not-applicable":
            continue
        requirement_id = entry.get("requirement_id", "<unknown>")
        findings.append(
            f"requirement '{requirement_id}' maps to mechanism "
            f"'{mechanism}', which the contract declares not-applicable; "
            f"SIG-18"
        )
    return findings
