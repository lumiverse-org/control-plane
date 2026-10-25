"""tools/provision/tests/test_cli_safety_regression.py

Adversarial and regression test suite for:
- FIX 1: Guard ordering bug (--roster-source live with --apply) & dangerous --org default
- FIX 2: Refusal of --live --apply on add-person, change-role, remove-person
- FIX 3: GitHub team slug handling in RealGitHubClient.create_team

SAFETY DISCIPLINE:
- Subprocess.run is globally backstopped via an autouse fixture to RAISE immediately
  if ever invoked in this test module. Zero live gh CLI calls, zero network access.
- Spies on RealGitHubClient.__init__ and execute_step prove that no client is ever
  constructed and no step is ever executed under forbidden conditions.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tools.provision import cli
from tools.provision.cli import (
    LiveRosterApplyForbidden,
    OperationApplyNotImplemented,
    OrgRequiredForApply,
    build_parser,
)
from tools.provision.executors import FakeGitHubClient
from tools.provision.github_client import RealGitHubClient
from tools.provision.plan import Plan, Step, StepKind


@pytest.fixture(autouse=True)
def hard_subprocess_backstop(monkeypatch: pytest.MonkeyPatch):
    """Safety backstop: raise immediately if subprocess.run is ever called in this test suite."""
    def _forbidden_subprocess_run(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError(
            f"SAFETY VIOLATION: subprocess.run was invoked during offline safety test!\n"
            f"args: {args!r}, kwargs: {kwargs!r}"
        )

    monkeypatch.setattr(subprocess, "run", _forbidden_subprocess_run)


# ==============================================================================
# FIX 1 REGRESSION TESTS: Guard Ordering & Dangerous --org Default
# ==============================================================================


@patch("tools.provision.cli.execute_step")
@patch("tools.provision.cli.RealGitHubClient.__init__", return_value=None)
def test_regression_incident_argv_rejected_before_client_or_step(
    mock_client_init: MagicMock,
    mock_execute_step: MagicMock,
    capsys: pytest.CaptureFixture[str],
):
    """Regression test for the incident's exact command:
    create-product --live --roster-source live --product Product-9 --apply [--org lumiverse-org]

    Must be rejected with LiveRosterApplyForbidden BEFORE RealGitHubClient is constructed
    and BEFORE execute_step is ever called.
    """
    # 1. Exact incident argv with explicit --org
    argv_with_org = [
        "create-product",
        "--live",
        "--roster-source",
        "live",
        "--product",
        "Product-9",
        "--apply",
        "--org",
        "lumiverse-org",
    ]
    rc1 = cli.main(argv_with_org)
    assert rc1 == 1
    out1, err1 = capsys.readouterr()
    assert "error: --apply cannot be used with --roster-source live: live roster planning is dry-run only." in err1
    assert mock_client_init.call_count == 0, "RealGitHubClient must NEVER be instantiated!"
    assert mock_execute_step.call_count == 0, "execute_step must NEVER be called!"

    # 2. Exact incident argv without --org
    argv_no_org = [
        "create-product",
        "--live",
        "--roster-source",
        "live",
        "--product",
        "Product-9",
        "--apply",
    ]
    rc2 = cli.main(argv_no_org)
    assert rc2 == 1
    out2, err2 = capsys.readouterr()
    # Guard ordering: LiveRosterApplyForbidden is raised FIRST before checking --org or declared/
    assert "error: --apply cannot be used with --roster-source live" in err2
    assert mock_client_init.call_count == 0, "RealGitHubClient must NEVER be instantiated!"
    assert mock_execute_step.call_count == 0, "execute_step must NEVER be called!"


def test_programmatic_create_product_raises_live_roster_apply_forbidden():
    """Verify _cmd_create_product raises LiveRosterApplyForbidden directly when roster_source=live and apply=True."""
    parser = build_parser()
    args = parser.parse_args([
        "create-product",
        "--live",
        "--roster-source",
        "live",
        "--product",
        "Product-9",
        "--apply",
        "--org",
        "lumiverse-org",
    ])
    with pytest.raises(LiveRosterApplyForbidden, match="live roster planning is dry-run only"):
        cli._cmd_create_product(args)


@patch("tools.provision.cli.execute_step")
@patch("tools.provision.cli.RealGitHubClient.__init__", return_value=None)
def test_regression_missing_org_under_live_apply_rejected(
    mock_client_init: MagicMock,
    mock_execute_step: MagicMock,
    capsys: pytest.CaptureFixture[str],
):
    """Verify that omitting --org under --live --apply is rejected and never defaults to production org."""
    argv = [
        "create-product",
        "--live",
        "--product",
        "Product-9",
        "--apply",
    ]
    rc = cli.main(argv)
    assert rc == 1
    out, err = capsys.readouterr()
    assert "error: --org must be explicitly specified when running with --live --apply: refusing to default to a production organisation." in err
    assert mock_client_init.call_count == 0, "RealGitHubClient must NEVER be instantiated!"
    assert mock_execute_step.call_count == 0, "execute_step must NEVER be called!"


def test_programmatic_run_operation_raises_org_required_for_apply():
    """Verify _run_operation raises OrgRequiredForApply when args.org is None or empty under applied=True."""
    parser = build_parser()
    args = parser.parse_args([
        "create-product",
        "--live",
        "--product",
        "Product-9",
        "--apply",
    ])
    plan = Plan(steps=[Step("step1", "dummy", StepKind.WRITE)])
    with pytest.raises(OrgRequiredForApply, match="--org must be explicitly specified when running with --live --apply"):
        cli._run_operation(args, "create-product", plan)


# ==============================================================================
# FIX 2 REGRESSION TESTS: Refusal of --live --apply for add/change/remove-person
# ==============================================================================


@pytest.mark.parametrize(
    "subcommand,extra_args",
    [
        ("add-person", ["--login", "dev-1"]),
        ("change-role", ["--login", "dev-1", "--to-role", "qa"]),
        ("remove-person", ["--login", "dev-1"]),
    ],
)
@patch("tools.provision.cli.execute_step")
@patch("tools.provision.cli.RealGitHubClient.__init__", return_value=None)
def test_regression_person_subcommands_refuse_live_apply(
    mock_client_init: MagicMock,
    mock_execute_step: MagicMock,
    subcommand: str,
    extra_args: list[str],
    capsys: pytest.CaptureFixture[str],
):
    """Verify add-person, change-role, and remove-person refuse --live --apply upfront.

    RealGitHubClient must NEVER be instantiated and execute_step must NEVER be called.
    """
    argv = [subcommand, "--live", "--apply", "--org", "lumiverse-org", *extra_args]
    rc = cli.main(argv)
    assert rc == 1
    out, err = capsys.readouterr()
    expected_msg = f"error: --live --apply is not supported for {subcommand}: apply-execution is currently implemented only for create-product."
    assert expected_msg in err
    assert mock_client_init.call_count == 0, f"RealGitHubClient must NEVER be instantiated for {subcommand}!"
    assert mock_execute_step.call_count == 0, f"execute_step must NEVER be called for {subcommand}!"


@pytest.mark.parametrize(
    "subcommand,extra_args",
    [
        ("add-person", ["--login", "dev-1"]),
        ("change-role", ["--login", "dev-1", "--to-role", "qa"]),
        ("remove-person", ["--login", "dev-1"]),
    ],
)
def test_programmatic_person_subcommands_raise_operation_apply_not_implemented(
    subcommand: str,
    extra_args: list[str],
):
    """Verify calling subcommand functions directly raises OperationApplyNotImplemented under --live --apply."""
    parser = build_parser()
    args = parser.parse_args([subcommand, "--live", "--apply", "--org", "lumiverse-org", *extra_args])
    with pytest.raises(OperationApplyNotImplemented, match=f"--live --apply is not supported for {subcommand}"):
        args.func(args)


# ==============================================================================
# FIX 3 ADVERSARIAL TEST: Slug Handling in create_team
# ==============================================================================


def test_adversarial_create_team_slug_demonstration():
    """Adversarial check demonstrating that create_team extracts and uses the server-returned slug.

    If the code were using the raw name instead of the slug, the membership URL
    would have contained 'Product Nine Team' rather than 'product-nine-team'.
    """
    raw_name = "Product Nine Team"
    returned_slug = "product-nine-team"
    calls: list[list[str]] = []

    class MockedClient(RealGitHubClient):
        def _run_gh(self, cmd: list[str], input_str: str | None = None) -> Any:
            calls.append(cmd)
            if any("teams" in arg for arg in cmd) and "-f" in cmd:
                # Team creation response
                mock_proc = MagicMock()
                mock_proc.returncode = 0
                mock_proc.stdout = f'{{"id": 999, "name": "{raw_name}", "slug": "{returned_slug}"}}'
                return mock_proc
            # Membership call response
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = "{}"
            return mock_proc

    client = MockedClient(org="test-org")
    result = client.create_team(raw_name, ["member-a", "member-b"])

    assert result["name"] == raw_name
    assert result["slug"] == returned_slug

    # 1 team creation call + 2 membership calls
    assert len(calls) == 3
    team_create_cmd = calls[0]
    assert team_create_cmd == ["gh", "api", "orgs/test-org/teams", "-f", f"name={raw_name}"]

    mem1_cmd = calls[1]
    assert mem1_cmd == ["gh", "api", f"orgs/test-org/teams/{returned_slug}/memberships/member-a", "-X", "PUT"]
    assert raw_name not in mem1_cmd[2], "Membership call must not use unslugified raw name!"

    mem2_cmd = calls[2]
    assert mem2_cmd == ["gh", "api", f"orgs/test-org/teams/{returned_slug}/memberships/member-b", "-X", "PUT"]
    assert raw_name not in mem2_cmd[2], "Membership call must not use unslugified raw name!"
