"""R-EXC-02 -- `trigger_satisfied` closure reserved to two non-discretionary
exception types (Section 54.2).

Section 54.2 makes `closure: trigger_satisfied` available only to exception
types whose `deactivation_trigger` is declared non-discretionary --
`bootstrap` and `founder_standing_delegation_activation`. Every other type
closes by `expired`, `remediated` or `promoted_to_policy`; `trigger_satisfied`
on any other type is rejected here.

Standalone, directly-tested module -- see `r_exc_01.py`'s docstring for why
this is not wired into the frozen Option B CLI (`contracts/validator-contract.md`)
and not discovered via `validators.registry.rules.discover()` (superseded
by FD-094, `validators/registry/README.md`).
"""
from __future__ import annotations

from pathlib import Path

import yaml

RULE_ID = "R-EXC-02"
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
        closure = exc.get("closure")
        exc_type = exc.get("type")
        if closure == "trigger_satisfied" and exc_type not in NON_DISCRETIONARY_TYPES:
            exc_id = exc.get("id", "<unknown>")
            findings.append(
                f"{RULE_ID} {source}:/exceptions/{idx}/closure "
                f"closure 'trigger_satisfied' is available only to bootstrap and "
                f"founder_standing_delegation_activation; exception '{exc_id}' is "
                f"type '{exc_type}'; Section 54.2"
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
