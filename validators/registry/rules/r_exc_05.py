"""R-EXC-05 -- a third renewal on a type with no re-affirmation branch
(Section 54.2).

Section 54.2: "A third renewal raises Red and forces one of three outcomes
... The third branch is available only to exception types whose
`deactivation_trigger` is declared non-discretionary -- `bootstrap` and
`founder_standing_delegation_activation`." For every other type a third
renewal must be resolved (closed), not carried indefinitely -- so this
rule fires only while the exception is still open (`closure is null`); a
renewed-three-times exception that has since been closed is not this
rule's concern (R-EXC-01 is what re-opens the question of an expired-but-
still-open exception).

Standalone, directly-tested module -- see `r_exc_01.py`'s docstring for why
this is not wired into the frozen Option B CLI (`contracts/validator-contract.md`)
and not discovered via `validators.registry.rules.discover()` (superseded
by FD-094, `validators/registry/README.md`).
"""
from __future__ import annotations

from pathlib import Path

import yaml

RULE_ID = "R-EXC-05"
SPEC = "Section 54.2"
APPLIES_TO = ["exceptions"]

NON_DISCRETIONARY_TYPES = {"bootstrap", "founder_standing_delegation_activation"}
RENEWAL_THRESHOLD = 3


def check_document(doc, source="exceptions.yaml"):
    """Check one already-parsed exceptions.yaml-shaped document."""
    if not isinstance(doc, dict):
        return True, []

    findings = []
    for idx, exc in enumerate(doc.get("exceptions", []) or []):
        if not isinstance(exc, dict):
            continue
        renewals = exc.get("renewals")
        if not isinstance(renewals, int) or renewals < RENEWAL_THRESHOLD:
            continue
        if exc.get("closure") is not None:
            continue
        exc_type = exc.get("type")
        if exc_type in NON_DISCRETIONARY_TYPES:
            continue
        exc_id = exc.get("id", "<unknown>")
        findings.append(
            f"{RULE_ID} {source}:/exceptions/{idx}/renewals "
            f"exception '{exc_id}' has been renewed {renewals} times; Section 54.2 "
            f"permits the re-affirmation branch only for bootstrap and "
            f"founder_standing_delegation_activation"
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
