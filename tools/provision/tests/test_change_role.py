"""L3-P7-01: the `change-role` operation (spec 12.6, 12.3; invariant 56; AT-005)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import subprocess

from tools.provision.change_role import (
    CHANGE_ROLE_STEPS,
    ForbiddenPersonnelAction,
    PlanLoginMissing,
    apply_change_role_step,
    build_change_role_plan,
    ownership_reassessment_prompt,
    subject_from_plan,
)
from tools.provision.cli import _run_operation, build_parser
from tools.provision.executors import FakeGitHubClient
from tools.provision.plan import StepKind


def test_plan_has_exactly_seven_steps_in_spec_order():
    plan = build_change_role_plan("dev-1", "qa")
    assert [s.id for s in plan.steps] == list(CHANGE_ROLE_STEPS)
    assert len(plan.steps) == 7


def test_dry_run_summary_line_matches_spec_exactly():
    plan = build_change_role_plan("dev-1", "qa")
    assert plan.summary_line("change-role") == "PLAN change-role steps=7 writes=0 manual=0"


def test_no_step_is_manual_kind():
    # Section 19.1's "manual" is an automation-gap tracked issue, a
    # different concept from the ownership prompt below - none of the
    # seven steps is StepKind.MANUAL.
    plan = build_change_role_plan("dev-1", "qa")
    assert plan.count(StepKind.MANUAL) == 0


def test_ownership_reassessment_prompt_is_a_message_not_a_reassignment():
    prompt = ownership_reassessment_prompt("dev-1", "qa")
    assert prompt.login == "dev-1"
    assert prompt.to_role == "qa"
    assert "review" in prompt.message
    # a prompt object; no ownership field (primary_owner / cross_reviewer /
    # backup_owner) is ever present on it because nothing here assigns one
    assert not hasattr(prompt, "primary_owner")
    assert not hasattr(prompt, "cross_reviewer")
    assert not hasattr(prompt, "backup_owner")


def test_ownership_step_is_the_prompt_message_verbatim():
    plan = build_change_role_plan("dev-1", "qa")
    prompt = ownership_reassessment_prompt("dev-1", "qa")
    step = next(s for s in plan.steps if s.id == "ownership_reassessment_prompt")
    assert step.description == prompt.message


@pytest.mark.parametrize(
    "forbidden_role",
    [
        "promotion",
        "termination",
        "compensation",
        "improvement_plan",
        "formal_warning",
        "QA-Promotion-Track",  # case-insensitive, substring
    ],
)
def test_refuses_any_role_naming_a_formal_people_decision(forbidden_role):
    with pytest.raises(ForbiddenPersonnelAction):
        build_change_role_plan("dev-1", forbidden_role)


def test_forbidden_words_appear_only_inside_the_refusal_guard():
    # AT-071 acceptance check, verbatim: `grep -riE
    # "promotion|termination|compensation|improvement_plan|formal_warning"
    # tools/provision/change_role.py` returns nothing outside a refusal
    # guard. Every matching line must fall inside `_FORBIDDEN_ROLE_TOKENS`
    # (the guard's own literal list) or `_refuse_personnel_action` (the
    # function that raises on a match) - nowhere else in the file.
    source = Path(__file__).resolve().parent.parent / "change_role.py"
    lines = source.read_text(encoding="utf-8").splitlines()
    pattern = re.compile(r"promotion|termination|compensation|improvement_plan|formal_warning", re.IGNORECASE)

    tokens_start = next(i for i, l in enumerate(lines) if "_FORBIDDEN_ROLE_TOKENS: tuple" in l)
    tokens_end = next(i for i, l in enumerate(lines) if i > tokens_start and l.strip() == ")")
    guard_start = next(i for i, l in enumerate(lines) if l.startswith("def _refuse_personnel_action"))
    guard_end = next(i for i, l in enumerate(lines) if i > guard_start and l.startswith("def "))

    stray = [
        (n, line)
        for n, line in enumerate(lines)
        if pattern.search(line) and not (tokens_start <= n <= tokens_end or guard_start <= n < guard_end)
    ]
    assert stray == [], f"forbidden words found outside the refusal guard: {stray}"


def test_apply_uses_plan_login_and_does_not_invite(monkeypatch: pytest.MonkeyPatch):
    def _boom(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("live GitHub API was called")

    monkeypatch.setattr(subprocess, "run", _boom)
    plan = build_change_role_plan("dev-1", "qa")
    assert subject_from_plan(plan) == ("dev-1", "qa")
    fake = FakeGitHubClient()
    args = build_parser().parse_args(
        ["change-role", "--live", "--apply", "--org", "test-org", "--login", "invented-login", "--to-role", "qa"]
    )
    rc = _run_operation(args, "change-role", plan, client=fake)
    assert rc == 0
    names = [name for name, _payload in fake.calls]
    assert names == [
        "put_file",
        "put_file",
        "put_file",
        "put_file",
        "create_issue",
        "put_file",
        "put_file",
    ]
    blob = repr(fake.calls)
    assert "dev-1" in blob
    assert "invented-login" not in blob
    assert "invitations" not in blob
    issue = next(payload for name, payload in fake.calls if name == "create_issue")
    assert issue["title"] == "Ownership reassessment -- dev-1"
    assert "never reassigns" in issue["body"]
    assert "primary_owner" not in issue["body"]


def test_apply_fails_closed_when_planner_has_no_login():
    plan = build_change_role_plan("   ", "qa")
    fake = FakeGitHubClient()
    with pytest.raises(PlanLoginMissing, match="refusing to invent"):
        apply_change_role_step(plan, plan.steps[0], fake, repo="control-plane")
    assert fake.calls == []
