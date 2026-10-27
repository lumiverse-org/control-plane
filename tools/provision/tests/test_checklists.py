"""L3-P4-08: CONFIGURE checklist and manual-step issue emitter."""

from __future__ import annotations

import pytest

import json
import subprocess

from tools.provision.checklists import (
    BUDGET_BAND_NOTE,
    CONFIGURE_ITEMS,
    CREATE_PRODUCT_MANUAL_STEPS,
    IssueTargetMissing,
    ManualStep,
    MissingToken,
    PostingRefused,
    configure_checklist,
    manual_step_issue,
    manual_step_issues,
    post_issue,
)
from tools.provision.github_client import GitHubClientError, RealGitHubClient


def test_configure_checklist_has_exactly_seven_items_verbatim():
    assert CONFIGURE_ITEMS == (
        "environments",
        "verification contract",
        "observability",
        "backups",
        "classification",
        "budget band",
        "support intake",
    )
    body = configure_checklist("alpha")
    for item in CONFIGURE_ITEMS:
        assert f"- [ ] {item}" in body or item in body
    assert body.count("- [ ] ") == 7


def test_configure_checklist_budget_band_note_is_verbatim():
    body = configure_checklist("alpha")
    assert BUDGET_BAND_NOTE in body
    assert "budget band" in body


def test_two_manual_step_issues_rendered_for_create_product_plan():
    steps = [
        ManualStep(id="alert_channel", description="Create the alert channel."),
        ManualStep(id="support_intake_mailbox", description="Create the support intake mailbox."),
    ]
    assert [s.id for s in steps] == list(CREATE_PRODUCT_MANUAL_STEPS)
    issues = manual_step_issues(steps)
    assert len(issues) == 2
    assert "alert_channel" in issues[0]
    assert "support_intake_mailbox" in issues[1]


def test_manual_step_issue_names_step_id_and_description():
    step = ManualStep(id="alert_channel", description="Create the #alpha-alerts channel.")
    body = manual_step_issue(step)
    assert "alert_channel" in body
    assert "Create the #alpha-alerts channel." in body


def test_post_issue_refused_without_both_apply_and_live():
    with pytest.raises(PostingRefused):
        post_issue("body", apply=False, live=False)
    with pytest.raises(PostingRefused):
        post_issue("body", apply=True, live=False)
    with pytest.raises(PostingRefused):
        post_issue("body", apply=False, live=True)


class _FakeIssueClient:
    """Records create_issue calls. Performs no network I/O."""

    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def create_issue(self, repo: str, title: str, body: str) -> dict[str, int]:
        self.calls.append({"repo": repo, "title": title, "body": body})
        return {"number": 1}


def test_post_issue_apply_live_calls_fake_and_does_not_call_gh(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("gh was called")

    monkeypatch.setattr(subprocess, "run", _boom)
    fake = _FakeIssueClient()
    body = "# CONFIGURE checklist -- alpha\n\n- [ ] environments\n"
    result = post_issue(body, apply=True, live=True, client=fake, repo="control-plane")
    assert result == {"number": 1}
    assert fake.calls == [
        {
            "repo": "control-plane",
            "title": "CONFIGURE checklist -- alpha",
            "body": body,
        }
    ]


def test_post_issue_missing_token_fails_closed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    called: list[object] = []

    def _boom(*args: object, **kwargs: object) -> None:
        called.append((args, kwargs))
        raise AssertionError("gh was called")

    monkeypatch.setattr(subprocess, "run", _boom)
    with pytest.raises(MissingToken, match="fail closed"):
        post_issue(
            "body",
            apply=True,
            live=True,
            repo="control-plane",
            title="CONFIGURE checklist -- alpha",
            org="test-org",
        )
    assert called == []


def test_post_issue_with_token_but_no_org_does_not_call_gh(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GH_TOKEN", "fixture-token-not-a-secret")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("gh was called")

    monkeypatch.setattr(subprocess, "run", _boom)
    with pytest.raises(IssueTargetMissing, match="org is required"):
        post_issue("body", apply=True, live=True, repo="control-plane", title="T")


def test_live_create_issue_calls_gh_api(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GH_TOKEN", "fixture-token-not-a-secret")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    captured: list[tuple[list[str], str | None]] = []

    def _fake_run(cmd: list[str], input: str | None = None, capture_output: bool = True, text: bool = True):
        captured.append((cmd, input))
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=0,
            stdout=json.dumps({"number": 7, "html_url": "https://example.invalid/issues/7"}),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)
    client = RealGitHubClient(org="test-org")
    result = client.create_issue("control-plane", "CONFIGURE checklist -- alpha", "hello")
    assert result["number"] == 7
    assert len(captured) == 1
    cmd, payload = captured[0]
    assert cmd[:3] == ["gh", "api", "repos/test-org/control-plane/issues"]
    assert cmd[cmd.index("-X") + 1] == "POST"
    assert json.loads(payload or "") == {
        "title": "CONFIGURE checklist -- alpha",
        "body": "hello",
    }
    assert "fixture-token-not-a-secret" not in cmd
    assert "fixture-token-not-a-secret" not in (payload or "")


def test_live_create_issue_missing_token_fails_closed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("gh was called")

    monkeypatch.setattr(subprocess, "run", _boom)
    client = RealGitHubClient(org="test-org")
    with pytest.raises(GitHubClientError, match="fail closed"):
        client.create_issue("control-plane", "Title", "Body")
