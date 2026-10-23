"""R-TOP-03: Active domains must have a designated lead.

Spec anchor: Section 66.2.
Task: lanes/L1-05-tasks.md, L1-503.

This module is a standalone, directly-tested rule function, not registered
in validators/registry/rules/registry.py's frozen R01-R18 catalogue (FD-094)
and not discovered by any harness. Exercised directly by test_r_top_01.py
against fixtures under validators/registry/fixtures/top01/.
RULES.md does not exist in this repository (see test_exceptions_minimal.py).
"""
from __future__ import annotations

RULE_ID = "R-TOP-03"
SPEC = "Section 66.2"
APPLIES_TO = ["topology"]


def check(doc: dict, source: str = "topology.yaml") -> list[str]:
    """Return findings for R-TOP-03: an active domain with lead: null."""
    if not doc or not doc.get("domains_active"):
        return []
    findings = []
    for idx, domain in enumerate(doc.get("domains") or []):
        if domain.get("lead") is None:
            domain_id = domain.get("id", "<unknown>")
            findings.append(
                f"{RULE_ID} {source}:/domains/{idx}/lead domain '{domain_id}' is "
                f"active with no lead; Section 66.2 resolves a domain reference to "
                f"the portfolio Team Lead only while domains are dormant"
            )
    return findings
