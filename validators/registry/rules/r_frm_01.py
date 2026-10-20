"""R-FRM-01 -- a role does not have exactly one active framework on a date
(Section 77.1, SIG-23, AT-077).

Section 77.1: "Exactly one framework version is Active for a given role at
a given date, unless multi-framework operation is explicitly configured
for a transition period." This covers both directions: a role covered by
zero active frameworks (SIG-23, "Outstanding framework mapping") and a
role covered by two or more (the AT-077 failure) share this one rule id,
differing only in the reported ``<n>``.

Standalone, directly-tested rule function -- see the module docstring of
r_svc_01.py (L1-404) for why this is not wired into the frozen Option B
(FD-094) R01-R18 dispatch engine (``validators/registry/rules/registry.py``).
Exercised directly against parsed ``framework.yaml``/``roles.yaml`` fixture
pairs by ``validators/registry/tests/test_framework_rules.py`` (L1-802).
"""
from __future__ import annotations

import datetime

RULE_ID = "R-FRM-01"
SPEC = "Section 77.1"
APPLIES_TO = ["framework", "roles"]


def _as_date(value) -> datetime.date:
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(str(value))


def _covers(doc: dict, role: str, today: datetime.date) -> bool:
    if role not in (doc.get("affected_roles") or []):
        return False
    if doc.get("status") != "active":
        return False
    effective = _as_date(doc["effective_date"])
    if today < effective:
        return False
    retirement = doc.get("retirement_date")
    if retirement is not None and today >= _as_date(retirement):
        return False
    return True


def check(framework_docs: list, role_ids, today) -> list:
    """Return one finding per role for which the number of active-on-``today``
    framework documents naming that role is not exactly one, unless one of
    the covering documents sets ``multi_framework_transition: true``.

    ``role_ids`` is the set of role ids that must be covered, drawn from a
    ``roles.yaml`` fixture. When ``role_ids`` is ``None`` (no ``roles.yaml``
    in context), the rule is silent about roles no framework ever names --
    it still checks every role that *is* named in some ``affected_roles``,
    the same "silent when the counterpart document is absent" posture
    r_svc_01.check documents for R-SVC-01.
    """
    today = _as_date(today)
    domain = set(role_ids) if role_ids is not None else set()
    for doc in framework_docs:
        domain.update(doc.get("affected_roles") or [])

    findings = []
    for role in sorted(domain):
        covering = [d for d in framework_docs if _covers(d, role, today)]
        n = len(covering)
        if n == 1:
            continue
        if any(d.get("multi_framework_transition") for d in covering):
            continue
        findings.append(
            f"R-FRM-01 role '{role}' has {n} active frameworks on {today.isoformat()}; "
            f"Section 77.1 permits exactly one unless multi_framework_transition is set; "
            f"SIG-23"
        )
    return findings
