"""L3-P8-02: tests for gap diff-audit of the gap window (spec §53.7 bullet 2)."""

from __future__ import annotations

from datetime import date
import pytest

from reconciler.gap.audit import AuditItem, diff_audit
from reconciler.gap.detect import GapWindow

WINDOW = GapWindow(
    kind="reconciliation",
    start=date(2026, 8, 1),
    end=date(2026, 8, 27),
    missed_cycles=3,
)

DECLARED_BASE = {
    "people": {
        "dev-1": {"availability": "active", "role": "senior_developer"},
        "lead-1": {"availability": "active", "role": "team_lead"},
        "dev-departed": {"availability": "departed", "role": "developer"},
    },
    "production_approvers": ["lead-1"],
}


def test_audits_all_three_classes():
    actual = {
        "access_grants": [
            {"id": "g-1", "login": "dev-1", "date": "2026-08-10", "evidence": "EV-01"}
        ],
        "merges": [
            {"pr": 101, "date": "2026-08-12", "approvers": ["lead-1"], "evidence": "EV-02"}
        ],
        "production_approvals": [
            {
                "deployment_id": "dep-1",
                "date": "2026-08-15",
                "approver": "lead-1",
                "deployer": "dev-1",
                "evidence": "EV-03",
            }
        ],
    }
    results = diff_audit(WINDOW, DECLARED_BASE, actual)
    assert len(results) == 3
    classes = {item.item_class for item in results}
    assert classes == {"access_grant", "merge", "production_approval"}


def test_item_with_no_evidence_is_reported_unverified():
    actual = {
        "access_grants": [
            {"id": "g-unverified", "login": "dev-1", "date": "2026-08-10", "evidence": None}
        ],
        "merges": [],
        "production_approvals": [],
    }
    results = diff_audit(WINDOW, DECLARED_BASE, actual)
    assert len(results) == 1
    assert results[0].status == "unverified"
    assert "no audit evidence" in results[0].detail


def test_unverified_item_is_never_reported_clean():
    actual = {
        "access_grants": [{"id": "g-1", "login": "dev-1", "date": "2026-08-10", "evidence": None}],
        "merges": [{"pr": 42, "date": "2026-08-10", "approvers": ["lead-1"], "evidence": ""}],
        "production_approvals": [
            {"deployment_id": "d-1", "date": "2026-08-10", "approver": "lead-1", "evidence": None}
        ],
    }
    results = diff_audit(WINDOW, DECLARED_BASE, actual)
    assert len(results) == 3
    for r in results:
        assert r.status != "clean"
        assert r.status != "verified"
        assert r.status == "unverified"


def test_audit_produces_list_not_boolean():
    actual = {
        "access_grants": [{"id": "g-1", "login": "dev-1", "date": "2026-08-10", "evidence": "EV-1"}],
        "merges": [],
        "production_approvals": [],
    }
    results = diff_audit(WINDOW, DECLARED_BASE, actual)
    assert isinstance(results, list)
    assert not isinstance(results, bool)
    assert len(results) == 1
    assert results[0].status == "verified"


def test_items_outside_gap_window_are_excluded():
    actual = {
        "access_grants": [
            {"id": "g-before", "login": "dev-1", "date": "2026-07-31", "evidence": "EV-1"},
            {"id": "g-inside", "login": "dev-1", "date": "2026-08-10", "evidence": "EV-2"},
            {"id": "g-after", "login": "dev-1", "date": "2026-08-28", "evidence": "EV-3"},
        ],
        "merges": [],
        "production_approvals": [],
    }
    results = diff_audit(WINDOW, DECLARED_BASE, actual)
    assert len(results) == 1
    assert results[0].identifier == "g-inside"


def test_access_grant_to_departed_or_undeclared_is_flagged_drift():
    actual = {
        "access_grants": [
            {"id": "g-departed", "login": "dev-departed", "date": "2026-08-10", "evidence": "EV-1"},
            {"id": "g-unknown", "login": "dev-unknown", "date": "2026-08-10", "evidence": "EV-2"},
        ],
        "merges": [],
        "production_approvals": [],
    }
    results = diff_audit(WINDOW, DECLARED_BASE, actual)
    assert len(results) == 2
    assert all(r.status == "drift" for r in results)


def test_merge_violating_policy_is_flagged_drift():
    actual = {
        "access_grants": [],
        "merges": [
            {
                "pr": 201,
                "date": "2026-08-10",
                "author": "dev-1",
                "approvers": ["dev-1"],
                "evidence": "EV-SELF",
            },
            {
                "pr": 202,
                "date": "2026-08-10",
                "author": "dev-1",
                "approvers": [],
                "evidence": "EV-NO-APP",
            },
        ],
        "production_approvals": [],
    }
    results = diff_audit(WINDOW, DECLARED_BASE, actual)
    assert len(results) == 2
    assert results[0].status == "drift"
    assert "self-approved" in results[0].detail
    assert results[1].status == "drift"
    assert "zero approvers" in results[1].detail


def test_production_approval_violations_flagged_drift():
    actual = {
        "access_grants": [],
        "merges": [],
        "production_approvals": [
            {
                "deployment_id": "dep-self",
                "date": "2026-08-10",
                "approver": "lead-1",
                "deployer": "lead-1",
                "evidence": "EV-01",
            },
            {
                "deployment_id": "dep-unauth",
                "date": "2026-08-10",
                "approver": "dev-1",
                "deployer": "lead-1",
                "evidence": "EV-02",
            },
        ],
    }
    results = diff_audit(WINDOW, DECLARED_BASE, actual)
    assert len(results) == 2
    assert results[0].status == "drift"
    assert "approver" in results[0].detail and "deployer" in results[0].detail
    assert results[1].status == "drift"
    assert "not in declared production_approvers" in results[1].detail
