"""Regression tests for --allow-step-failure flag in tools.provision.cli.

Verifies:
(a) step 3 fails, --allow-step-failure absent -> halts at step 3 (no regression);
(b) step 3 fails, --allow-step-failure=<step3_id> -> records failure, steps 4-5 execute,
    final output marks step 3 as FAILED-BUT-ALLOWED in summary, writes count is accurate;
(c) different step fails, --allow-step-failure=<step3_id> -> halts at the other failing step;
(d) tools/provision/create-product wrapper forwards --allow-step-failure correctly.
"""

from __future__ import annotations

import argparse
from importlib.machinery import SourceFileLoader
from pathlib import Path
import types
from typing import Any

import pytest
import yaml

from tools.provision.cli import _run_operation, build_parser
from tools.provision.executors import FakeGitHubClient
from tools.provision.github_client import GitHubClientError
from tools.provision.plan import Plan, Step, StepKind

REPO_ROOT = Path(__file__).resolve().parents[3]
CREATE_PRODUCT_SCRIPT = REPO_ROOT / "tools" / "provision" / "create-product"


class SelectiveFailingGitHubClient(FakeGitHubClient):
    """Subclass of FakeGitHubClient that fails on a chosen API method."""

    def __init__(self, failing_method: str, error_msg: str = "Simulated API failure") -> None:
        super().__init__()
        self.failing_method = failing_method
        self.error_msg = error_msg

    def create_team(self, name: str, members: list[str]) -> dict[str, Any]:
        self.calls.append(("create_team", name, members))
        if self.failing_method == "create_team":
            raise GitHubClientError(self.error_msg)
        return {"id": 12345, "name": name, "slug": name, "members": members}

    def apply_branch_protection(
        self, repo: str, branch: str, settings: dict[str, Any]
    ) -> dict[str, Any]:
        self.calls.append(("apply_branch_protection", repo, branch, settings))
        if self.failing_method == "apply_branch_protection":
            raise GitHubClientError(self.error_msg)
        return {"status": "protected", "repo": repo, "branch": branch}


@pytest.fixture
def temp_declared_root(tmp_path: Path) -> Path:
    """Fixture providing minimal declared files needed by executors."""
    declared = tmp_path / "declared"
    declared.mkdir(parents=True, exist_ok=True)
    (declared / "products").mkdir(parents=True, exist_ok=True)
    (declared / "templates").mkdir(parents=True, exist_ok=True)

    people_content = {
        "people": [
            {
                "id": "dev-1",
                "github_login": "dev-1",
                "availability": "active",
                "capabilities": ["code-review"],
            }
        ]
    }
    (declared / "people.yaml").write_text(yaml.safe_dump(people_content), encoding="utf-8")
    (declared / "platform.yaml").write_text(
        yaml.safe_dump({"reusable_workflow_versions": {"current": "workflows/v1"}}),
        encoding="utf-8",
    )
    (declared / "templates" / "branch-protection.json").write_text("{}", encoding="utf-8")
    (declared / "templates" / "environments.json").write_text(
        yaml.safe_dump({
            "environments": [
                {"name": "development", "deployment_branch_policy": {"protected_branches": False}}
            ]
        }),
        encoding="utf-8",
    )
    return tmp_path


def _five_step_plan() -> Plan:
    return Plan(
        steps=[
            Step("repo_from_template", "step 1: create repo", StepKind.WRITE),
            Step("product_yaml", "step 2: write local product yaml", StepKind.WRITE),
            Step("branch_protection", "step 3: branch protection", StepKind.WRITE),
            Step("environments", "step 4: create environments", StepKind.WRITE),
            Step("ci_workflows_pinned_tag", "step 5: pin ci workflows", StepKind.WRITE),
        ]
    )


def test_step3_fails_without_allow_flag_halts_at_step3(
    temp_declared_root: Path, capsys: pytest.CaptureFixture[str]
):
    """Case (a): step 3 fails and --allow-step-failure is NOT given -> halts at step 3."""
    parser = build_parser()
    args = parser.parse_args([
        "create-product",
        "--product",
        "pilot-test",
        "--live",
        "--apply",
        "--org",
        "lumiverse-org",
        "--steps",
    ])

    failing_client = SelectiveFailingGitHubClient(
        failing_method="apply_branch_protection",
        error_msg="HTTP 403: Upgrade to GitHub Pro/Team or make repo public",
    )

    rc = _run_operation(
        args=args,
        operation="create-product",
        plan=_five_step_plan(),
        client=failing_client,
        declared_dir=temp_declared_root,
    )

    assert rc == 1  # Execution halted with error
    out, err = capsys.readouterr()

    # Step 3 failure was reported
    assert "FAILED during create-product at step branch_protection" in err
    assert "Upgrade to GitHub Pro/Team" in err

    # Steps 1-2 succeeded before failure
    assert "Steps succeeded before failure (2/5):" in err
    assert "- [write] repo_from_template: OK" in err
    assert "- [write] product_yaml: OK" in err
    assert "PLAN create-product steps=5 writes=2 manual=0 (EXECUTION FAILED)" in err

    # Steps 4 and 5 NEVER ran. product_yaml may already have written product.yaml.
    calls = [c[0] for c in failing_client.calls]
    assert "create_repo_from_template" in calls
    assert "apply_branch_protection" in calls
    assert "create_environment" not in calls
    workflow_puts = [
        c for c in failing_client.calls
        if c[0] == "put_file" and str(c[1].get("path", "")).startswith(".github/workflows/")
    ]
    assert workflow_puts == []
    product_puts = [
        c for c in failing_client.calls
        if c[0] == "put_file" and c[1].get("path") == "product.yaml"
    ]
    assert len(product_puts) == 1


def test_step3_fails_with_allow_flag_continues_and_marks_summary(
    temp_declared_root: Path, capsys: pytest.CaptureFixture[str]
):
    """Case (b): step 3 fails and --allow-step-failure=branch_protection -> continues past step 3.

    Steps 4 and 5 execute, summary output marks step 3 as FAILED-BUT-ALLOWED,
    writes count reflects only truly succeeded steps (4, not 5), exit code is 0.
    """
    parser = build_parser()
    args = parser.parse_args([
        "create-product",
        "--product",
        "pilot-test",
        "--live",
        "--apply",
        "--org",
        "lumiverse-org",
        "--allow-step-failure",
        "branch_protection",
        "--steps",
    ])

    failing_client = SelectiveFailingGitHubClient(
        failing_method="apply_branch_protection",
        error_msg="HTTP 403: Upgrade to GitHub Pro/Team or make repo public",
    )

    rc = _run_operation(
        args=args,
        operation="create-product",
        plan=_five_step_plan(),
        client=failing_client,
        declared_dir=temp_declared_root,
    )

    assert rc == 0  # Succeeded because the only failure was explicitly allowed
    out, err = capsys.readouterr()

    # Stderr received warning when failure occurred
    assert "WARNING: step branch_protection failed but allowed via --allow-step-failure" in err

    # Final summary line on stdout contains FAILED-BUT-ALLOWED and writes=4 (not 5)
    assert "PLAN create-product steps=5 writes=4 manual=0 [FAILED-BUT-ALLOWED: branch_protection]" in out

    # Detailed allowed step failures block printed
    assert "Allowed step failures (1):" in out
    assert "- [write] branch_protection: FAILED-BUT-ALLOWED (HTTP 403: Upgrade to GitHub Pro/Team or make repo public)" in out

    # Steps 4 and 5 were actually executed!
    calls = [c[0] for c in failing_client.calls]
    assert "create_repo_from_template" in calls
    assert "apply_branch_protection" in calls
    assert "create_environment" in calls  # Step 4 ran!
    assert "put_file" in calls            # Step 5 ran!


def test_different_step_fails_when_allow_flag_names_step3_halts_normally(
    temp_declared_root: Path, capsys: pytest.CaptureFixture[str]
):
    """Case (c): step 2 fails when --allow-step-failure names branch_protection -> halts at step 2."""
    parser = build_parser()
    args = parser.parse_args([
        "create-product",
        "--product",
        "pilot-test",
        "--live",
        "--apply",
        "--org",
        "lumiverse-org",
        "--allow-step-failure",
        "branch_protection",
    ])

    # Plan with step 2 being 'team', and client configured to fail on create_team
    plan = Plan(
        steps=[
            Step("repo_from_template", "step 1", StepKind.WRITE),
            Step("team", "step 2", StepKind.WRITE),
            Step("branch_protection", "step 3", StepKind.WRITE),
            Step("environments", "step 4", StepKind.WRITE),
            Step("ci_workflows_pinned_tag", "step 5", StepKind.WRITE),
        ]
    )

    failing_client = SelectiveFailingGitHubClient(
        failing_method="create_team",
        error_msg="HTTP 422: Team exists",
    )

    rc = _run_operation(
        args=args,
        operation="create-product",
        plan=plan,
        client=failing_client,
        declared_dir=temp_declared_root,
    )

    assert rc == 1  # Halts because step 'team' was NOT the allowed failure
    out, err = capsys.readouterr()

    assert "FAILED during create-product at step team" in err
    assert "Team exists" in err
    assert "PLAN create-product steps=5 writes=1 manual=0 (EXECUTION FAILED)" in err

    # Step 3, 4, 5 never ran
    calls = [c[0] for c in failing_client.calls]
    assert "create_team" in calls
    assert "apply_branch_protection" not in calls
    assert "create_environment" not in calls


def test_create_product_wrapper_forwards_allow_step_failure(monkeypatch: pytest.MonkeyPatch):
    """Case (d): tools/provision/create-product CLI wrapper parses and forwards the flag."""
    loader = SourceFileLoader("create_product_bin", str(CREATE_PRODUCT_SCRIPT))
    mod = types.ModuleType(loader.name)
    mod.__file__ = str(CREATE_PRODUCT_SCRIPT)
    loader.exec_module(mod)

    recorded_argv: list[str] = []

    def mock_cli_main(cli_args: list[str]) -> int:
        recorded_argv.extend(cli_args)
        return 0

    monkeypatch.setattr(mod.cli, "main", mock_cli_main)
    monkeypatch.setattr(mod, "record_executor", lambda *a: None)

    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write("name: pilot-one\n")
        f.flush()
        contract_path = f.name

    try:
        rc = mod.main([
            "--id", "pilot-one",
            "--contract", contract_path,
            "--template", "product-template",
            "--executor", "devops-1",
            "--org", "lumiverse-org",
            "--apply",
            "--live",
            "--allow-step-failure", "branch_protection",
        ])
        assert rc == 0
        assert "--allow-step-failure" in recorded_argv
        idx = recorded_argv.index("--allow-step-failure")
        assert recorded_argv[idx + 1] == "branch_protection"
    finally:
        Path(contract_path).unlink(missing_ok=True)
