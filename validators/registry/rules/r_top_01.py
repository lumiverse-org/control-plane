"""R-TOP-01: Escalation names a role, never a person.

Spec anchor: Section 10.2; Invariant 51; AT-016.
Task: lanes/L1-05-tasks.md, L1-503.

This module is a standalone, directly-tested rule function, not registered
in validators/registry/rules/registry.py's frozen R01-R18 catalogue (FD-094)
and not discovered by any harness. Exercised directly by test_r_top_01.py
against fixtures under validators/registry/fixtures/top01/.
RULES.md does not exist in this repository (see test_exceptions_minimal.py).

Note on escalation fallback resolution (Lane 3 / Lane 5): Section 10.2's
escalation fallback chain (Acting designate -> Founder -> recorded exception)
depends on reachability and response-time facts at incident time, which is not
Lane 1 data.
"""
from __future__ import annotations

RULE_ID = "R-TOP-01"
SPEC = "Section 10.2"
APPLIES_TO = ["product", "service", "people"]


def check(doc: dict, known_person_ids, source: str = "product.yaml") -> list[str]:
    """Return findings for R-TOP-01: `escalation` names a known person.

    ``doc`` is an already-parsed product.yaml or service.yaml mapping (or None/empty
    if the document itself is absent -- returns no findings).
    ``known_person_ids`` is the set of ids loaded from people.yaml, or ``None`` when
    people.yaml is absent from context -- in which case this rule is silent, exactly
    as R-PPL-04 is silent when its counterpart document is absent.
    """
    if not doc or known_person_ids is None:
        return []
    escalation = doc.get("escalation")
    if escalation is None:
        return []
    if escalation in known_person_ids:
        return [
            f"{RULE_ID} {source}:/escalation escalation '{escalation}' names a "
            f"person; Section 10.2 declares escalation as a role, never a person"
        ]
    return []
