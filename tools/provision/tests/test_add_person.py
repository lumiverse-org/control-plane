"""L3-P4-09: the `add-person` orchestrator (spec 12.6, 12.1; §36.4; AT-002)."""

from __future__ import annotations

import subprocess

import pytest

from tools.provision.add_person import (
    ADD_PERSON_STEPS,
    CONDUCT_ADVISER_PLACEHOLDER,
    MILESTONE_BANDS,
    AiRuntimeRestricted,
    PlanLoginMissing,
    apply_add_person_step,
    build_add_person_plan,
    login_from_plan,
    onboarding_checklist,
    resolve_ai_runtime,
)
from tools.provision.cli import _run_operation, build_parser
from tools.provision.executors import FakeGitHubClient
from tools.provision.plan import StepKind


def test_plan_has_exactly_seven_steps_in_spec_order():
    plan = build_add_person_plan("dev-3")
    assert [s.id for s in plan.steps] == list(ADD_PERSON_STEPS)
    assert len(plan.steps) == 7


def test_dry_run_summary_line_matches_spec_exactly():
    plan = build_add_person_plan("dev-3")
    assert plan.summary_line("add-person") == "PLAN add-person steps=7 writes=0 manual=1"


def test_exactly_one_manual_step_and_it_is_self_view_key_exchange():
    plan = build_add_person_plan("dev-3")
    manual_steps = [s for s in plan.steps if s.kind == StepKind.MANUAL]
    assert len(manual_steps) == 1
    assert manual_steps[0].id == "self_view_key_exchange"
    assert plan.count(StepKind.MANUAL) == 1


def test_every_other_step_is_write_kind():
    plan = build_add_person_plan("dev-3")
    non_manual = [s for s in plan.steps if s.id != "self_view_key_exchange"]
    assert len(non_manual) == 6
    assert all(s.kind == StepKind.WRITE for s in non_manual)


def test_invitation_step_grants_base_read_only():
    plan = build_add_person_plan("dev-3")
    invitation = next(s for s in plan.steps if s.id == "org_invitation")
    assert "Read only" in invitation.description
    assert "Write" not in invitation.description


def test_only_team_membership_step_names_a_write_grant():
    # §11.2: Write is Team-derived only. No other step's description may
    # claim to grant Write directly.
    plan = build_add_person_plan("dev-3")
    for step in plan.steps:
        if step.id == "team_membership_per_assignments":
            assert "grants Write" in step.description
        else:
            assert "grants Write" not in step.description


def test_step_descriptions_name_the_login():
    plan = build_add_person_plan("mira-8")
    for step in plan.steps:
        assert "mira-8" in step.description


def test_resolve_ai_runtime_passes_through_when_unrestricted():
    assert resolve_ai_runtime("assistant-a", ["assistant-b"]) == "assistant-a"
    assert resolve_ai_runtime("assistant-a", None) == "assistant-a"
    assert resolve_ai_runtime("assistant-a", []) == "assistant-a"


def test_resolve_ai_runtime_refuses_a_restricted_runtime_at_onboarding():
    # §36.4: honoured now, not deferred to a later reconciliation pass --
    # this raises immediately, at call time, never returning a value that
    # a caller could go on to apply.
    with pytest.raises(AiRuntimeRestricted):
        resolve_ai_runtime("assistant-a", ["assistant-a", "assistant-c"])


def test_ai_runtime_step_description_references_ai_restrictions():
    plan = build_add_person_plan("dev-3")
    step = next(s for s in plan.steps if s.id == "ai_runtime_assignment")
    assert "ai_restrictions" in step.description
    assert "never deferred" in step.description


def test_onboarding_checklist_names_conduct_adviser_and_fairness_rules():
    checklist = onboarding_checklist("dev-3")
    assert checklist.conduct_adviser == CONDUCT_ADVISER_PLACEHOLDER
    assert "conduct adviser" in checklist.body
    assert "fairness rules" in checklist.body


def test_onboarding_checklist_never_invents_a_real_identity():
    # No real conduct-adviser name has been supplied to this lane; the
    # default must be the clearly-marked placeholder, not a fabricated name.
    checklist = onboarding_checklist("dev-3")
    assert "PENDING-FOUNDER-INPUT" in checklist.body


def test_onboarding_checklist_accepts_a_supplied_conduct_adviser():
    checklist = onboarding_checklist("dev-3", conduct_adviser="Jordan Rivas <jrivas@example.com>")
    assert checklist.conduct_adviser == "Jordan Rivas <jrivas@example.com>"
    assert "Jordan Rivas" in checklist.body
    assert "PENDING-FOUNDER-INPUT" not in checklist.body


def test_onboarding_checklist_renders_all_seven_milestone_bands():
    checklist = onboarding_checklist("dev-3")
    assert len(MILESTONE_BANDS) == 7
    for milestone, band in MILESTONE_BANDS:
        assert milestone in checklist.body
        assert band in checklist.body


def _forbid_gh(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("live GitHub API was called")

    monkeypatch.setattr(subprocess, "run", _boom)


def test_apply_uses_login_from_plan_and_does_not_invite(monkeypatch: pytest.MonkeyPatch):
    _forbid_gh(monkeypatch)
    plan = build_add_person_plan("dev-3")
    assert login_from_plan(plan) == "dev-3"
    fake = FakeGitHubClient()
    args = build_parser().parse_args(
        ["add-person", "--live", "--apply", "--org", "test-org", "--login", "invented-login"]
    )
    rc = _run_operation(args, "add-person", plan, client=fake)
    assert rc == 0
    assert [name for name, _payload in fake.calls] == [
        "put_file",
        "put_file",
        "put_file",
        "put_file",
        "create_issue",
    ]
    blob = repr(fake.calls)
    assert "dev-3" in blob
    assert "invented-login" not in blob
    assert "invitations" not in blob
    assert all("invit" not in name for name, _payload in fake.calls)
    issue = next(payload for name, payload in fake.calls if name == "create_issue")
    assert issue["title"] == "Onboarding -- dev-3"
    assert "dev-3" in issue["body"]
    assert CONDUCT_ADVISER_PLACEHOLDER in issue["body"]
    assert all(payload.get("content", "").startswith("github_login: dev-3\n") for name, payload in fake.calls if name == "put_file")


def test_apply_fails_closed_when_planner_has_no_login(monkeypatch: pytest.MonkeyPatch):
    _forbid_gh(monkeypatch)
    plan = build_add_person_plan("   ")
    fake = FakeGitHubClient()
    with pytest.raises(PlanLoginMissing, match="refusing to invent"):
        apply_add_person_step(plan, plan.steps[0], fake, repo="control-plane")
    assert fake.calls == []
    args = build_parser().parse_args(
        ["add-person", "--live", "--apply", "--org", "test-org", "--login", "invented-login"]
    )
    with pytest.raises(PlanLoginMissing, match="refusing to invent"):
        _run_operation(args, "add-person", plan, client=fake)
    assert fake.calls == []
