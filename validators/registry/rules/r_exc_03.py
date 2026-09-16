"""R-EXC-03 -- a non-discretionary exception type declares no deactivation
trigger (Section 54.2).

Section 54.2 makes `deactivation_trigger` mandatory for the two exception
types that close on an event rather than a date or a remediation --
`bootstrap` and `founder_standing_delegation_activation`. A null trigger on
either type means the exception has no way to close at all.

Standalone, directly-tested module -- see `r_exc_01.py`'s docstring for why
this is not wired into the frozen Option B CLI (`contracts/validator-contract.md`)
and not discovered via `validators.registry.rules.discover()` (superseded
by FD-094, `validators/registry/README.md`).
"""
from __future__ import annotations

from pathlib import Path

import yaml

RULE_ID = "R-EXC-03"
SPEC = "Section 54.2"
APPLIES_TO = ["exceptions"]

NON_DISCRETIONARY_TYPES = {"bootstrap", "founder_standing_delegation_activation"}


def check_document(doc, source="exceptions.yaml"):
    """Check one already-parsed exceptions.yaml-shaped document."""
    if not isinstance(doc, dict):
        return True, []

    findings = []
    for idx, exc in enumerate(doc.get("exceptions", []) or []):
        if not isinstance(exc, dict):
            continue
        exc_type = exc.get("type")
        if exc_type in NON_DISCRETIONARY_TYPES and exc.get("deactivation_trigger") is None:
            exc_id = exc.get("id", "<unknown>")
            findings.append(
                f"{RULE_ID} {source}:/exceptions/{idx}/deactivation_trigger "
                f"{exc_type} exception '{exc_id}' declares no deactivation_trigger; "
                f"Section 54.2 makes it mandatory for types that close on an event"
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
