"""L3-P0-CMP12 (ported from L3-01-14) - CMP-11: assignment `end_date`
versus current Team membership, and people.yaml `end_date` versus
current organisation membership (spec 53.1 row 11; 10.2; 12.2;
invariant 55).

PROPOSED, NEVER EXECUTED, in this phase. Rule R1, and section 99.4
item 6: "Auto-repair is deferred until detection has run clean for
weeks." Every finding here carries a proposed repair whose class name
matches section 53.2's Level-3 list - "removing expired assignments
and expired access" - and whose ``applied`` flag is always the literal
``False``, so that a later, explicitly-enabled Level-3 executor
recognises the shape without this comparator ever calling it.

Two sources of expiry, both checked:

  - a product `temporary_assignments` row whose `end_date` is in the
    past, where the person is still a member of the product Team.
    This overlaps `expiry.py` (L3-P1-09) by design - both comparators
    are independent detectors of the same spec-53.1 row 11 condition,
    registered under different ids, and either firing is sufficient;
    this one exists so CMP-11's id is present in a run's own right.
  - a `people.yaml` entry whose `end_date` is in the past, whose
    `access_status` is not already `revoked`, and who is still an
    organisation member (section 12.2: a person's exit is not
    complete until access is actually gone).

`compared` counts every row this comparator actually examined -
`temporary_assignments` rows across every product, plus every
`people.yaml` entry - the comparator's only declared inputs.
"""

from __future__ import annotations

from datetime import date

from reconciler.model import DriftClass, Finding, Level
from reconciler.registry import comparator

# Section 53.2's Level-3 repair-class name, transcribed verbatim so a
# future executor's class-name lookup matches this proposal exactly.
REPAIR_CLASS = "expired-access-removal"

# Two independent proposal sites (product-assignment side, people.yaml
# side) - each below is its own literal, never a shared f-string, so
# that a proposal is never mistaken for having been carried out.
_PRODUCT_REPAIR_TEMPLATE = '{"class": "expired-access-removal", "team": %r, "login": %r, "applied": False}'
_PEOPLE_REPAIR_TEMPLATE = '{"class": "expired-access-removal", "organisation": %r, "login": %r, "applied": False}'


@comparator("cmp_11_expired_access", fail_class=DriftClass.BLOCKING)
def compare(declared, actual, as_of: date):
    findings: list[Finding] = []
    compared = 0
    first_seen = f"{as_of.isoformat()}T00:00:00Z"

    # -- source 1: product temporary_assignments vs Team membership ----
    for product_name, product_yaml in declared.products.items():
        rows = product_yaml.get("temporary_assignments") or []
        if not rows:
            continue
        team_members = set(actual.team_members(product_name))
        for row in rows:
            end_date_raw = row.get("end_date")
            if end_date_raw is None:
                continue
            compared += 1
            person = row.get("person")
            if date.fromisoformat(end_date_raw) >= as_of:
                continue
            if person not in team_members:
                continue
            proposed = _PRODUCT_REPAIR_TEMPLATE % (product_name, person)
            findings.append(
                Finding(
                    id=f"cmp_11_expired_access:{product_name}:{person}:team",
                    comparator="cmp_11_expired_access",
                    scope=f"{product_name}:{person}",
                    drift_class=DriftClass.BLOCKING,
                    level=Level.AUTO_REPAIR,
                    evidence=(
                        f"{person}'s {row.get('type')} assignment on {product_name} "
                        f"expired {end_date_raw} but they remain on the Team; "
                        f"repair_class={REPAIR_CLASS} proposed={proposed}"
                    ),
                    first_seen=first_seen,
                )
            )

    # -- source 2: people.yaml end_date vs organisation membership ------
    org_members = set(actual.org_members())
    for person in declared.people:
        end_date_raw = person.get("end_date")
        if end_date_raw is None:
            continue
        compared += 1
        login = person.get("github_login")
        if date.fromisoformat(end_date_raw) >= as_of:
            continue
        if person.get("access_status") == "revoked":
            continue
        if login not in org_members:
            continue
        proposed = _PEOPLE_REPAIR_TEMPLATE % ("org", login)
        findings.append(
            Finding(
                id=f"cmp_11_expired_access:{login}:org",
                comparator="cmp_11_expired_access",
                scope=login,
                drift_class=DriftClass.BLOCKING,
                level=Level.AUTO_REPAIR,
                evidence=(
                    f"{login}'s people.yaml end_date {end_date_raw} has passed, "
                    f"access_status={person.get('access_status')!r}, but they remain an "
                    f"organisation member; repair_class={REPAIR_CLASS} proposed={proposed}"
                ),
                first_seen=first_seen,
            )
        )

    return findings, compared
