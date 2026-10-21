"""R-BAN-02 -- non-delegable capabilities and founder-reserved people decisions.

Section 90.4 (D109); invariant 106; AT-090 (task L1-803).

Standalone, directly-tested rule function -- see r_svc_01.py for the
FD-094 Option B precedent.
"""
from __future__ import annotations

import json
from pathlib import Path

RULE_ID = "R-BAN-02"
SPEC = "Section 90.4 (D109)"
APPLIES_TO = ["product", "service", "people"]

_ASSIGNMENTS_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "registry"
    / "common"
    / "assignments.v1.schema.json"
)


def _load_excluded_decisions() -> tuple:
    with _ASSIGNMENTS_SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)
    try:
        enum = schema["properties"]["scope"]["properties"]["decisions"]["not"]["contains"]["enum"]
    except KeyError as e:
        raise RuntimeError(
            "assignments.v1.schema.json no longer has the "
            "properties.scope.properties.decisions.not.contains.enum path; "
            "R-BAN-02's EXCLUDED_DECISIONS must track Section 74.5's ten "
            "excluded decisions by construction, not by a second copy"
        ) from e
    return tuple(enum)


EXCLUDED_DECISIONS = _load_excluded_decisions()


def check_document(doc: dict | None, source: str = "product.yaml") -> tuple[bool, list[str]]:
    if not isinstance(doc, dict):
        return True, []
    findings = []

    # Assignments branch (product.yaml / service.yaml)
    for idx, assignment in enumerate(doc.get("assignments") or []):
        if not isinstance(assignment, dict):
            continue
        a_type = assignment.get("type", "<unknown>")
        person = assignment.get("person", "<unknown>")
        scope = assignment.get("scope") or {}

        for c_idx, cap in enumerate(scope.get("capabilities") or []):
            if cap == "people-intelligence":
                pointer = f"/assignments/{idx}/scope/capabilities/{c_idx}"
                findings.append(
                    f"{RULE_ID} {source}:{pointer} assignment '{a_type}' for '{person}' grants '{cap}', which is not delegable; D109, invariant 106, AT-090"
                )

        if a_type == "founder_decision_delegate":
            for d_idx, dec in enumerate(scope.get("decisions") or []):
                if dec in EXCLUDED_DECISIONS:
                    pointer = f"/assignments/{idx}/scope/decisions/{d_idx}"
                    findings.append(
                        f"{RULE_ID} {source}:{pointer} assignment '{a_type}' for '{person}' grants '{dec}', which is not delegable; D109, invariant 106, AT-090"
                    )

    # People branch (people.yaml)
    for idx, person in enumerate(doc.get("people") or []):
        if not isinstance(person, dict):
            continue
        person_id = person.get("id", "<unknown>")
        for c_idx, cap in enumerate(person.get("capabilities") or []):
            if cap == "people-intelligence":
                pointer = f"/people/{idx}/capabilities/{c_idx}"
                findings.append(
                    f"{RULE_ID} {source}:{pointer} person '{person_id}' is granted 'people-intelligence', which is not delegable; D109, invariant 106, AT-090"
                )

    return len(findings) == 0, findings
