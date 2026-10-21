"""R-VER-03 -- a high/critical product with no declared performance
verification mechanism.

Section 31.3: "For products whose classification.reliability_criticality
is high or critical, the performance mechanism is required:
contract.yaml must declare it, and the verification-contract check in
CI fails if it is absent." The second bullet of the same section makes
the mechanism optional for medium/low products; this rule never fires
for them, however they declare mechanisms.performance or
performance_profile.

Standalone, directly-tested rule function -- see the module docstring of
r_ver_02.py (and, for precedent, r_svc_01.py) for why this is not wired
into the frozen Option B (FD-094) dispatch engine
(validators/registry/rules/registry.py, R01..R18). This is a cross-file
rule like R-PPL-04 and R-SVC-01: it reads both product.yaml and
verification-contract.yaml and returns zero findings when either is
absent from context, rather than raising. Exercised directly by
validators/registry/tests/test_r_ver_03.py against the fixtures in
validators/registry/fixtures/ver03/.
"""
from __future__ import annotations

RULE_ID = "R-VER-03"
SPEC = "Section 31.3"
APPLIES_TO = ["product", "verification-contract"]

_REQUIRES_PERFORMANCE = ("high", "critical")


def check(product_doc: dict | None, contract_doc: dict | None) -> list[str]:
    """Return a finding when a high/critical product's verification
    contract has not declared a performance mechanism.

    ``product_doc`` is the parsed ``product.yaml`` mapping and
    ``contract_doc`` is the parsed ``verification-contract.yaml``
    mapping for the same product. Returns ``[]`` when either is
    ``None`` -- this rule only fires when both documents are present,
    exactly as R-PPL-04 and R-SVC-01 do for their counterpart document.
    """
    if not product_doc or not contract_doc:
        return []
    criticality = (product_doc.get("classification") or {}).get(
        "reliability_criticality"
    )
    if criticality not in _REQUIRES_PERFORMANCE:
        return []
    mechanisms = contract_doc.get("mechanisms") or {}
    performance_declared = (
        mechanisms.get("performance") == "required"
        and contract_doc.get("performance_profile") is not None
    )
    if performance_declared:
        return []
    return [
        f"reliability_criticality '{criticality}' requires a declared "
        f"performance mechanism; Section 31.3"
    ]
