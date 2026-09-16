"""R-FRM-03 -- a target-bearing field carries a marker-shaped string that
is not the exact "Not defined in Framework v1" literal (Section 77.4,
AT-077).

Section 77.4: "Where a field genuinely does not exist in the framework in
force, it is marked exactly: `Not defined in Framework v1`. No value is
invented to fill it." A near-miss marker -- wrong case, wrong wording,
a bare `TBD` or `N/A` -- is how a captured gap silently becomes a claim,
so this rule treats every string that merely *resembles* a marker as a
defect unless it is byte-identical to the required literal.

The marker-shape set is closed and mechanical (casefolded, whitespace-
collapsed): "not defined", "not defined in framework v1",
"not defined in framework v1.", "undefined", "n/a", "na", "none", "tbd",
"tba", "to be defined", "pending", "unknown". This rule never widens that
set to catch a phrase merely because it *sounds* like a marker (e.g. "not
defined in the framework") -- Section 77.4 forbids normalising a value
automatically, and a rule that expanded the set ad hoc to catch more
phrasings would be doing exactly that by another route.

``review_cadence`` is Section 77.1's field, not this rule's target set in
the general sense: its own valid literal is exactly `Not defined` (see
``valid/review_cadence_not_defined`` / ``valid/custom_structure_no_targets``
in ``validators/registry/fixtures/frm/``), so R-FRM-03 must not fire on
that one exact value there even though it is marker-shaped.

Standalone, directly-tested rule function -- see r_svc_01.py's module
docstring (L1-404) for why this is not wired into the frozen Option B
(FD-094) R01-R18 dispatch engine.
"""
from __future__ import annotations

RULE_ID = "R-FRM-03"
SPEC = "Section 77.4 / AT-077"
APPLIES_TO = ["framework"]

_MARKER_LITERAL = "Not defined in Framework v1"
_REVIEW_CADENCE_EXEMPT = "Not defined"

_MARKER_SHAPES = {
    "not defined",
    "not defined in framework v1",
    "not defined in framework v1.",
    "undefined",
    "n/a",
    "na",
    "none",
    "tbd",
    "tba",
    "to be defined",
    "pending",
    "unknown",
}


def _is_marker_shaped(value) -> bool:
    if not isinstance(value, str):
        return False
    normalized = " ".join(value.strip().casefold().split())
    return normalized in _MARKER_SHAPES


def _finding(source: str, pointer: str, field: str, item_id: str, value: str) -> str:
    return (
        f"R-FRM-03 {source}:{pointer} field '{field}' on '{item_id}' reads '{value}'; "
        f'Section 77.4 requires the exact marker "Not defined in Framework v1" '
        f"where the framework in force defines no value"
    )


def check(framework_docs: list, sources: list | None = None) -> list:
    """Return one finding per marker-shaped, non-exact ``target``,
    ``stretch_target``, ``definition`` (kra or kpi) or ``review_cadence``
    value across every document in ``framework_docs``.

    ``sources`` names each document (e.g. its file path) for the finding's
    ``<source>:<pointer>`` prefix; when omitted, an index placeholder is
    used.
    """
    findings = []
    for idx, doc in enumerate(framework_docs):
        source = sources[idx] if sources else f"framework[{idx}]"
        version = doc.get("framework_version", "<unknown>")

        review_cadence = doc.get("review_cadence")
        if _is_marker_shaped(review_cadence) and review_cadence not in (
            _MARKER_LITERAL,
            _REVIEW_CADENCE_EXEMPT,
        ):
            findings.append(
                _finding(source, "/review_cadence", "review_cadence", version, review_cadence)
            )

        for k_idx, kra in enumerate(doc.get("kras") or []):
            definition = kra.get("definition")
            if _is_marker_shaped(definition) and definition != _MARKER_LITERAL:
                findings.append(
                    _finding(
                        source,
                        f"/kras/{k_idx}/definition",
                        "definition",
                        kra.get("id", "<unknown>"),
                        definition,
                    )
                )

        for k_idx, kpi in enumerate(doc.get("kpis") or []):
            kpi_id = kpi.get("id", "<unknown>")
            for field in ("target", "stretch_target", "definition"):
                value = kpi.get(field)
                if _is_marker_shaped(value) and value != _MARKER_LITERAL:
                    findings.append(
                        _finding(source, f"/kpis/{k_idx}/{field}", field, kpi_id, value)
                    )
    return findings
