"""R-EXC-04 -- a declared compensating control with no record store or no
cadence (Section 54.2).

Section 54.2 verifies a compensating control "like a restore test": a
declared control is worthless without somewhere it is recorded and a
cadence it is checked on. `compensating_control` is the literal string
`none` when an exception declares no control at all (schema: `minLength 1`,
so it is never null) -- in that one case a null record store and a
`none` cadence are exactly correct, not a defect, and this rule stays
silent (`valid/control_none_declared/`).

Standalone, directly-tested module -- see `r_exc_01.py`'s docstring for why
this is not wired into the frozen Option B CLI (`contracts/validator-contract.md`)
and not discovered via `validators.registry.rules.discover()` (superseded
by FD-094, `validators/registry/README.md`).
"""
from __future__ import annotations

from pathlib import Path

import yaml

RULE_ID = "R-EXC-04"
SPEC = "Section 54.2"
APPLIES_TO = ["exceptions"]

NO_CONTROL_DECLARED = "none"


def check_document(doc, source="exceptions.yaml"):
    """Check one already-parsed exceptions.yaml-shaped document."""
    if not isinstance(doc, dict):
        return True, []

    findings = []
    for idx, exc in enumerate(doc.get("exceptions", []) or []):
        if not isinstance(exc, dict):
            continue
        control = exc.get("compensating_control")
        if control == NO_CONTROL_DECLARED:
            continue
        record = exc.get("compensating_control_record")
        cadence = exc.get("compensating_control_cadence")
        if record is None or cadence == NO_CONTROL_DECLARED:
            exc_id = exc.get("id", "<unknown>")
            findings.append(
                f"{RULE_ID} {source}:/exceptions/{idx}/compensating_control "
                f"exception '{exc_id}' names a compensating control with no record "
                f"store or no cadence; Section 54.2 verifies the control like a "
                f"restore test"
            )
    return len(findings) == 0, findings


def check(registry_root, as_of, records_root=None):
    """Option-B-shaped entry point: scan the exceptions.yaml under records_root
    (falling back to registry_root when records_root is not given)."""
    findings = []
    candidates = []
    if records_root:
        candidates.append(Path(records_root) / "exceptions.yaml")
    else:
        candidates.append(Path(registry_root) / "registries" / "exceptions.yaml")
        candidates.append(Path(registry_root) / "exceptions.yaml")

    for path in candidates:
        if not path.exists():
            continue
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            findings.append(f"{RULE_ID} {path}: could not parse YAML: {e}")
            continue
        _, doc_findings = check_document(doc, source=str(path))
        findings.extend(doc_findings)
    return len(findings) == 0, findings
