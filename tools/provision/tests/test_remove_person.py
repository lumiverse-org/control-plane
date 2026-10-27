"""L3-P7-02: the `remove-person` operation (spec 12.2, 12.6; invariant 57; AT-017)."""

from __future__ import annotations

from datetime import date

import pytest

from reconciler.orphans import OrphanContext, OrphanFinding
import subprocess

from tools.provision.remove_person import (
    REMOVE_PERSON_STEPS,
    BlockingOrphanUnresolved,
    PlanLoginMissing,
    apply_remove_person_step,
    build_remove_person_plan,
    dismiss,
    identifier_available,
    login_from_plan,
    retire_identifier,
    run_orphan_detection,
    succession_alerts,
)
from tools.provision.cli import _run_operation, build_parser
from tools.provision.executors import FakeGitHubClient


def test_plan_has_exactly_eleven_steps_in_spec_order():
    plan = build_remove_person_plan("dev-1")
    assert [s.id for s in plan.steps] == list(REMOVE_PERSON_STEPS)
    assert len(plan.steps) == 11


def test_dry_run_summary_line_matches_spec_exactly():
    plan = build_remove_person_plan("dev-1")
    assert plan.summary_line("remove-person") == "PLAN remove-person steps=11 writes=0 manual=0"


def test_no_step_deletes_the_person_record_and_identifier_is_never_reused():
    retired: set[str] = set()
    retired = retire_identifier("dev-2", retired)
    assert identifier_available("dev-2", frozenset(retired)) is False
    # retiring again is idempotent, never a "delete and free the name" path
    retired = retire_identifier("dev-2", retired)
    assert retired == {"dev-2"}
    assert identifier_available("dev-3", frozenset(retired)) is True


def _ctx(**overrides) -> OrphanContext:
    defaults = dict(
        fixture_name="test",
        as_of=date(2026, 8, 27),
        people=[{"github_login": "dev-1", "availability": "active", "access_status": "active"}],
        products={"alpha": {"assignments": {"primary_owner": "dev-1"}}},
        shared_services=[],
        assets=[],
        board_items=[],
        open_gate_items=[],
        migrations=[],
        policies=[],
        exceptions=[],
    )
    defaults.update(overrides)
    return OrphanContext(**defaults)


def test_step_ten_invokes_the_real_phase_two_orphan_detector():
    # alpha has no cross_reviewer, no backup_owner, no incident
    # responder -> real findings from the real detector, not a stub.
    ctx = _ctx()
    findings, compared = run_orphan_detection(ctx)
    assert compared > 0
    assert any(f.subject == "alpha" for f in findings)
    assert any(f.orphan_severity == "Blocking" for f in findings)


def test_blocking_orphans_from_step_ten_cannot_be_dismissed():
    ctx = _ctx()
    findings, _ = run_orphan_detection(ctx)
    blocking = [f for f in findings if f.orphan_severity == "Blocking"]
    assert blocking, "fixture must produce at least one Blocking orphan for this test to mean anything"
    for finding in blocking:
        with pytest.raises(BlockingOrphanUnresolved):
            dismiss(finding, reason="reassigned informally, no registry change yet")


def test_non_blocking_orphans_can_be_dismissed():
    high_finding = OrphanFinding(
        index=3, name="Product with no Backup Owner", orphan_severity="High",
        subject="alpha", detail="alpha: Product with no Backup Owner (holder: empty)",
    )
    dismissed = dismiss(high_finding, reason="backup owner assigned out of band, registry PR pending")
    assert dismissed is high_finding


def test_succession_designate_is_flagged_immediately():
    topology = {"succession": {"lead-engineer": "dev-1", "on-call-secondary": "dev-2"}}
    alerts = succession_alerts("dev-1", topology)
    assert len(alerts) == 1
    assert alerts[0].slot == "lead-engineer"
    assert "flagged immediately" in alerts[0].message


def test_no_succession_alert_for_a_non_designate():
    topology = {"succession": {"lead-engineer": "dev-2"}}
    assert succession_alerts("dev-1", topology) == ()


def test_no_succession_alert_when_topology_is_absent():
    assert succession_alerts("dev-1", None) == ()
    assert succession_alerts("dev-1", {}) == ()


def test_apply_removes_plan_login_and_does_not_invite(monkeypatch: pytest.MonkeyPatch):
    def _boom(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("live GitHub API was called")

    monkeypatch.setattr(subprocess, "run", _boom)
    plan = build_remove_person_plan("dev-1")
    assert login_from_plan(plan) == "dev-1"
    fake = FakeGitHubClient()
    args = build_parser().parse_args(
        ["remove-person", "--live", "--apply", "--org", "test-org", "--login", "invented-login"]
    )
    rc = _run_operation(args, "remove-person", plan, client=fake)
    assert rc == 0
    assert fake.calls[0] == ("remove_org_member", {"login": "dev-1"})
    assert [name for name, _payload in fake.calls].count("put_file") == 10
    blob = repr(fake.calls)
    assert "invented-login" not in blob
    assert "invitations" not in blob
    assert all("person_record: retained" in payload["content"] for name, payload in fake.calls if name == "put_file")


def test_apply_fails_closed_when_planner_has_no_login():
    plan = build_remove_person_plan("   ")
    fake = FakeGitHubClient()
    with pytest.raises(PlanLoginMissing, match="refusing to invent"):
        apply_remove_person_step(plan, plan.steps[0], fake, repo="control-plane")
    assert fake.calls == []
