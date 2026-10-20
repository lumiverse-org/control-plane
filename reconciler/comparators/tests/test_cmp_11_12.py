"""L3-P0-CMP12 (ported from L3-01-14): CMP-11 expired access and CMP-12
Shared Service registry dependency check.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from reconciler.comparators.cmp_11_expired_access import compare as cmp_11_compare
from reconciler.comparators.cmp_12_dependencies import Dependencies
from reconciler.comparators.cmp_12_dependencies import compare as cmp_12_compare
from reconciler.model import DriftClass, Level

AS_OF = date(2026, 8, 27)


class _Actual:
    """A minimal GitHubState stand-in - only the two methods CMP-11
    reads (team_members, org_members). CMP-12 calls neither."""

    def __init__(self, teams=None, org_members=None):
        self._teams = teams or {}
        self._org_members = org_members or []

    def team_members(self, product):
        return list(self._teams.get(product, []))

    def org_members(self):
        return list(self._org_members)


def _declared(products=None, people=None, services=None):
    return SimpleNamespace(products=products or {}, people=people or [], services=services)


# --------------------------------------------------------------- CMP-11


def test_no_findings_when_nothing_has_expired():
    declared = _declared(
        products={
            "gamma": {
                "temporary_assignments": [
                    {"person": "temp-1", "type": "temporary_contributor", "end_date": "2026-12-31"},
                ]
            }
        },
        people=[{"github_login": "p-1", "access_status": "active", "end_date": "2026-12-31"}],
    )
    actual = _Actual(teams={"gamma": ["temp-1"]}, org_members=["p-1"])
    findings, compared = cmp_11_compare(declared, actual, AS_OF)
    assert findings == []
    assert compared == 2


def test_expired_assignment_still_on_team_is_blocking_and_proposed_only():
    declared = _declared(
        products={
            "gamma": {
                "temporary_assignments": [
                    {"person": "temp-1", "type": "temporary_contributor", "end_date": "2026-01-01"},
                ]
            }
        }
    )
    actual = _Actual(teams={"gamma": ["temp-1"]})
    findings, compared = cmp_11_compare(declared, actual, AS_OF)
    assert compared == 1
    assert len(findings) == 1
    finding = findings[0]
    assert finding.drift_class == DriftClass.BLOCKING
    assert finding.level == Level.AUTO_REPAIR
    assert '"applied": False' in finding.evidence
    assert "expired-access-removal" in finding.evidence


def test_expired_person_still_an_org_member_is_blocking_but_already_revoked_is_clean():
    active = _declared(people=[{"github_login": "p-1", "access_status": "active", "end_date": "2026-01-01"}])
    actual = _Actual(org_members=["p-1"])
    findings, compared = cmp_11_compare(active, actual, AS_OF)
    assert compared == 1
    assert len(findings) == 1
    assert findings[0].drift_class == DriftClass.BLOCKING
    assert findings[0].level == Level.AUTO_REPAIR
    assert '"applied": False' in findings[0].evidence

    revoked = _declared(people=[{"github_login": "p-1", "access_status": "revoked", "end_date": "2026-01-01"}])
    findings2, compared2 = cmp_11_compare(revoked, actual, AS_OF)
    assert compared2 == 1
    assert findings2 == []


# --------------------------------------------------------------- CMP-12


def test_registry_key_is_services():
    assert Dependencies.registry_key == "services"


def test_compared_counts_one_row_per_declared_service():
    declared = _declared(services=[{"name": "auth-service"}, {"name": "billing-service"}])
    findings, compared = cmp_12_compare(declared, _Actual(), AS_OF)
    assert findings == []
    assert compared == 2


def test_an_unknown_dependency_is_blocking_and_a_known_one_is_not():
    declared = _declared(
        products={
            "alpha": {"dependencies": {"internal": ["auth-service"]}},
            "beta": {"dependencies": {"internal": ["ghost-service"]}},
        },
        services=[{"name": "auth-service"}],
    )
    findings, compared = cmp_12_compare(declared, _Actual(), AS_OF)
    assert compared == 1
    assert len(findings) == 1
    assert findings[0].scope == "beta"
    assert findings[0].drift_class == DriftClass.BLOCKING
    assert findings[0].level == Level.BLOCK
    assert "ghost-service" in findings[0].evidence
