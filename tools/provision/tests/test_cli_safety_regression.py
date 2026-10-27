"""tools/provision/tests/test_cli_safety_regression.py

Adversarial and regression test suite for:
- FIX 1: Guard ordering bug (--roster-source live with --apply) & dangerous --org default
- FIX 2: add-person, change-role, and remove-person apply against a fake client and never call gh
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
import sys
import types
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tools.provision import cli
from tools.provision.cli import (
    LiveRosterApplyForbidden,
    OrgRequiredForApply,
    build_parser,
)
from tools.provision.executors import FakeGitHubClient
from tools.provision.github_client import GitHubClientError, RealGitHubClient
from tools.provision.plan import Plan, Step, StepKind

REPO_ROOT = Path(__file__).resolve().parents[3]
CREATE_PRODUCT_SCRIPT = REPO_ROOT / "tools" / "provision" / "create-product"
CONTRACT_FIXTURE = REPO_ROOT / "e2e" / "fixtures" / "pilot-one" / "product.yaml"


def _load_create_product_module() -> types.ModuleType:
    loader = SourceFileLoader("create_product_bin", str(CREATE_PRODUCT_SCRIPT))
    mod = types.ModuleType(loader.name)
    mod.__file__ = str(CREATE_PRODUCT_SCRIPT)
    loader.exec_module(mod)
    return mod


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
# FIX 2: person apply uses a fake client and never calls gh
# ==============================================================================


_PERSON_APPLY_CASES = [
    ("add-person", ["--login", "dev-1"], "PLAN add-person steps=7 writes=5 manual=1"),
    ("change-role", ["--login", "dev-1", "--to-role", "qa"], "PLAN change-role steps=7 writes=7 manual=0"),
    ("remove-person", ["--login", "dev-1"], "PLAN remove-person steps=11 writes=11 manual=0"),
]


@pytest.mark.parametrize("subcommand,extra_args,summary", _PERSON_APPLY_CASES)
@patch("tools.provision.cli.execute_step")
def test_person_subcommands_apply_against_fake_not_live_api(
    mock_execute_step: MagicMock,
    subcommand: str,
    extra_args: list[str],
    summary: str,
    capsys: pytest.CaptureFixture[str],
):
    """--live --apply walks the planner against a fake client. gh is not called."""
    created: list[FakeGitHubClient] = []

    class CapturingClient(FakeGitHubClient):
        def __init__(self, org: str | None = None) -> None:
            super().__init__(org)
            created.append(self)

    argv = [subcommand, "--live", "--apply", "--org", "lumiverse-org", *extra_args]
    with patch("tools.provision.cli.RealGitHubClient", CapturingClient):
        rc = cli.main(argv)
    assert rc == 0
    out, _err = capsys.readouterr()
    assert summary in out
    assert mock_execute_step.call_count == 0
    assert len(created) == 1
    calls = created[0].calls
    assert calls
    assert all("invit" not in name for name, _payload in calls)
    assert "invitations" not in repr(calls)
    assert all("dev-1" in repr(payload) for _name, payload in calls)
    if subcommand == "add-person":
        assert "does not invite users" in out
        assert [name for name, _payload in calls] == [
            "put_file",
            "put_file",
            "put_file",
            "put_file",
            "create_issue",
        ]
    elif subcommand == "remove-person":
        assert calls[0] == ("remove_org_member", {"login": "dev-1"})


@pytest.mark.parametrize("subcommand,extra_args,summary", _PERSON_APPLY_CASES)
@patch("tools.provision.cli.RealGitHubClient")
def test_programmatic_person_apply_uses_injected_fake(
    mock_real: MagicMock,
    subcommand: str,
    extra_args: list[str],
    summary: str,
    capsys: pytest.CaptureFixture[str],
):
    """An injected fake is used. The live client is not constructed."""
    fake = FakeGitHubClient()
    args = build_parser().parse_args(
        [subcommand, "--live", "--apply", "--org", "lumiverse-org", *extra_args]
    )
    rc = args.func(args, client=fake)
    assert rc == 0
    out, _err = capsys.readouterr()
    assert summary in out
    assert mock_real.call_count == 0
    assert fake.calls
    assert all("invit" not in name for name, _payload in fake.calls)


@pytest.mark.parametrize(
    "subcommand,extra_args",
    [
        ("add-person", ["--login", "   "]),
        ("change-role", ["--login", "   ", "--to-role", "qa"]),
        ("remove-person", ["--login", "   "]),
    ],
)
@patch("tools.provision.cli.RealGitHubClient")
def test_blank_login_fails_closed_without_a_live_client(
    mock_real: MagicMock,
    subcommand: str,
    extra_args: list[str],
    capsys: pytest.CaptureFixture[str],
):
    """A planner with no login refuses before any GitHub client is constructed."""
    rc = cli.main([subcommand, "--live", "--apply", "--org", "test-org", *extra_args])
    assert rc == 1
    _out, err = capsys.readouterr()
    assert "refusing to invent" in err
    assert mock_real.call_count == 0


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


# ==============================================================================
# FIX A: Environment-variable ORG gap under --apply in create-product wrapper
# ==============================================================================


@patch("tools.provision.cli.execute_step")
@patch("tools.provision.cli.RealGitHubClient.__init__", return_value=None)
def test_regression_wrapper_env_var_org_rejected_under_apply(
    mock_client_init: MagicMock,
    mock_execute_step: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    """Verify that when os.environ['ORG'] is set to 'lumiverse-org' and --apply is given
    without an explicit CLI --org flag, create-product refuses the invocation.

    Must reject BEFORE RealGitHubClient is constructed and BEFORE execute_step is called.
    """
    monkeypatch.setenv("ORG", "lumiverse-org")
    mod = _load_create_product_module()

    argv = [
        "--id",
        "pilot-one",
        "--contract",
        str(CONTRACT_FIXTURE),
        "--template",
        "product-template",
        "--executor",
        "devops-1",
        "--apply",
    ]

    rc = mod.main(argv)
    assert rc == 1
    out, err = capsys.readouterr()
    expected = (
        "CREATE-PRODUCT FAIL: --org must be passed explicitly on the command line when using --apply; "
        "it cannot be sourced from the ORG environment variable for a real write."
    )
    assert expected in err
    assert mock_client_init.call_count == 0, "RealGitHubClient must NEVER be instantiated!"
    assert mock_execute_step.call_count == 0, "execute_step must NEVER be called!"


def test_regression_wrapper_explicit_cli_org_accepted_under_apply(
    monkeypatch: pytest.MonkeyPatch,
):
    """Verify that an explicit CLI --org flag is properly forwarded to cli.main under --apply."""
    monkeypatch.setenv("ORG", "should-be-ignored")
    mod = _load_create_product_module()

    intercepted_cli_args: list[str] = []

    def mock_cli_main(args: list[str]) -> int:
        intercepted_cli_args.extend(args)
        return 0

    monkeypatch.setattr(mod.cli, "main", mock_cli_main)

    argv = [
        "--id",
        "pilot-one",
        "--contract",
        str(CONTRACT_FIXTURE),
        "--template",
        "product-template",
        "--executor",
        "devops-1",
        "--apply",
        "--org",
        "lumiverse-org",
    ]

    rc = mod.main(argv)
    assert rc == 0
    assert "--apply" in intercepted_cli_args
    assert "--live" in intercepted_cli_args
    assert "--org" in intercepted_cli_args
    idx = intercepted_cli_args.index("--org")
    assert intercepted_cli_args[idx + 1] == "lumiverse-org"


def test_wrapper_dry_run_falls_back_to_env_org(monkeypatch: pytest.MonkeyPatch):
    """Verify that dry-run planning still conveniently falls back to the ORG environment variable."""
    monkeypatch.setenv("ORG", "env-dry-org")
    mod = _load_create_product_module()

    intercepted_cli_args: list[str] = []

    def mock_cli_main(args: list[str]) -> int:
        intercepted_cli_args.extend(args)
        return 0

    monkeypatch.setattr(mod.cli, "main", mock_cli_main)

    argv = [
        "--id",
        "pilot-one",
        "--contract",
        str(CONTRACT_FIXTURE),
        "--template",
        "product-template",
        "--executor",
        "devops-1",
    ]

    rc = mod.main(argv)
    assert rc == 0
    assert "--apply" not in intercepted_cli_args
    assert "--org" in intercepted_cli_args
    idx = intercepted_cli_args.index("--org")
    assert intercepted_cli_args[idx + 1] == "env-dry-org"


# ==============================================================================
# FIX B: Double-layered LiveRosterApplyForbidden guard in _run_operation
# ==============================================================================


@patch("tools.provision.cli.execute_step")
def test_regression_run_operation_double_layered_live_roster_apply_forbidden(
    mock_execute_step: MagicMock,
):
    """Verify calling _run_operation directly with roster_source='live' and apply=True
    is refused before execute_step runs.
    """
    parser = build_parser()
    args = parser.parse_args([
        "create-product",
        "--live",
        "--apply",
        "--roster-source",
        "live",
        "--product",
        "alpha",
        "--org",
        "test-org",
    ])
    plan = Plan(steps=[Step("repo_from_template", "create repo", StepKind.WRITE)])

    with pytest.raises(LiveRosterApplyForbidden, match="live roster planning is dry-run only"):
        cli._run_operation(args, "create-product", plan)

    assert mock_execute_step.call_count == 0, "execute_step must NEVER be called!"


# ==============================================================================
# FIX C: create_team response parse failure raises GitHubClientError
# ==============================================================================


def test_regression_create_team_malformed_json_raises():
    """Verify create_team raises GitHubClientError instead of silently falling back on malformed JSON."""
    class MockedClient(RealGitHubClient):
        def _run_gh(self, cmd: list[str], input_str: str | None = None) -> Any:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = "{ malformed truncated response"
            return mock_proc

    client = MockedClient(org="test-org")
    with pytest.raises(GitHubClientError, match="Failed to parse team creation response"):
        client.create_team("Product Nine Team", ["alice"])


def test_regression_create_team_empty_json_raises():
    """Verify create_team raises GitHubClientError instead of silently falling back on empty JSON object."""
    class MockedClient(RealGitHubClient):
        def _run_gh(self, cmd: list[str], input_str: str | None = None) -> Any:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = "{}"
            return mock_proc

    client = MockedClient(org="test-org")
    with pytest.raises(GitHubClientError, match="returned empty JSON object"):
        client.create_team("Product Nine Team", ["alice"])

