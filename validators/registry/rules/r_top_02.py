"""R-TOP-02: Escalation resolves to a declared role or active domain.

Spec anchor: Section 66.2.
Task: lanes/L1-05-tasks.md, L1-503.

This module is a standalone, directly-tested rule function, not registered
in validators/registry/rules/registry.py's frozen R01-R18 catalogue (FD-094)
and not discovered by any harness. Exercised directly by test_r_top_01.py
against fixtures under validators/registry/fixtures/top01/.
RULES.md does not exist in this repository (see test_exceptions_minimal.py).
"""
from __future__ import annotations

RULE_ID = "R-TOP-02"
SPEC = "Section 66.2"
APPLIES_TO = ["product", "service", "roles", "topology"]


def check(doc: dict, known_role_ids, known_domain_ids, source: str = "product.yaml") -> list[str]:
    """Return findings for R-TOP-02: `escalation` resolves to no role and no domain.

    known_role_ids / known_domain_ids are the id sets loaded from roles.yaml /
    topology.yaml respectively, or None when that document is absent. Silent only
    when BOTH counterparts are absent (nothing to resolve against at all); when
    exactly one is present, resolution is checked against that one set alone --
    this is how `valid/no_topology_file` passes on a role match with no
    topology.yaml in the case directory at all.
    """
    if not doc:
        return []
    escalation = doc.get("escalation")
    if escalation is None:
        return []
    if known_role_ids is None and known_domain_ids is None:
        return []
    roles = known_role_ids or set()
    domains = known_domain_ids or set()
    if escalation not in roles and escalation not in domains:
        return [
            f"{RULE_ID} {source}:/escalation escalation '{escalation}' resolves to "
            f"no role in roles.yaml and no domain in topology.yaml; Section 66.2"
        ]
    return []
