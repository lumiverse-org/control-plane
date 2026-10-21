"""R-PPL-04 -- referential integrity: people.yaml role names must exist in roles.yaml
(L1-206, Section 99.2 subsystem B, invariant 50, Section 8).

Standalone, directly-tested rule function, not wired into the frozen Option B
(FD-094) dispatch engine -- see the module docstrings of r_svc_01.py and r_svc_03.py.
If roles.yaml is not present in ctx.docs (known_role_ids is None), this rule returns
zero errors -- a single-file validation of people.yaml alone must not fail for a
missing sibling.
"""
from __future__ import annotations

RULE_ID = "R-PPL-04"
SPEC = "Section 99.2 subsystem B"
APPLIES_TO = ["people", "roles"]


def check(people_doc: dict, known_role_ids) -> list[str]:
    """Return one finding per person whose ``role`` names an id absent from
    ``known_role_ids``.

    ``known_role_ids`` is the set of ``id`` values loaded from roles.yaml in
    context, or ``None`` when no roles document is present at all -- in which
    case this rule is silent (returns no findings): a single-file validation
    of people.yaml alone must not fail for a missing sibling.
    """
    if known_role_ids is None:
        return []
    known = set(known_role_ids)
    findings = []

    records = []
    if isinstance(people_doc, dict):
        people_list = people_doc.get("people")
        if isinstance(people_list, list):
            records = [p for p in people_list if isinstance(p, dict)]
        elif "role" in people_doc:
            records = [people_doc]

    for person in records:
        role = person.get("role")
        person_id = person.get("id", "<unknown-person>")
        if role not in known:
            findings.append(
                f"person '{person_id}' names role '{role}' which does not exist in roles.yaml"
            )
    return findings
