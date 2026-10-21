"""R-BAN-03 -- automated formal people action fields.

Section 91.2; invariant 37; AT-071 (task L1-803).

Standalone, directly-tested rule function -- see r_svc_01.py for the
FD-094 Option B precedent.
"""
from __future__ import annotations

RULE_ID = "R-BAN-03"
SPEC = "Section 91.2 / invariant 37"
APPLIES_TO = ["framework", "os-health", "policies", "people", "product"]

AUTOMATED_PEOPLE_ACTION_FIELDS = frozenset({
    "auto_promote",
    "auto_promotion",
    "auto_terminate",
    "auto_termination",
    "auto_improvement_plan",
    "auto_compensation_change",
    "auto_formal_warning",
    "automated_people_action",
    "automatic_exit_decision",
})


def _walk(node, pointer=""):
    """Yield (key, pointer, value) for every mapping key anywhere under
    node, depth-first, pointer being a JSON-pointer string to that key."""
    if isinstance(node, dict):
        for key, value in node.items():
            child_pointer = f"{pointer}/{key}"
            yield key, child_pointer, value
            yield from _walk(value, child_pointer)
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            yield from _walk(item, f"{pointer}/{idx}")


def check_document(doc: dict | None, source: str = "framework.yaml") -> tuple[bool, list[str]]:
    if not isinstance(doc, dict):
        return True, []
    findings = []
    for key, pointer, _value in _walk(doc):
        if key in AUTOMATED_PEOPLE_ACTION_FIELDS:
            findings.append(
                f"{RULE_ID} {source}:{pointer} field '{key}' at {pointer} configures "
                f"an automated formal people action; invariant 37, AT-071"
            )
    return len(findings) == 0, findings
