"""Unit tests for tools.provision.cli apply execution (Part 2).

Exercises _run_operation and _cmd_create_product under --live --apply using
FakeGitHubClient — zero real gh subprocess calls, zero live network access.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pytest
import yaml

from tools.provision.cli import _cmd_create_product, _run_operation, build_parser
from tools.provision.executors import FakeGitHubClient
from tools.provision.github_client import GitHubClientError
from tools.provision.plan import Plan, Step, StepKind


class FailingGitHubClient(FakeGitHubClient):
    """Subclass of FakeGitHubClient that seeds an error on a specific method."""

    def __init__(self, failing_method: str, error_message: str = "Seeded failure") -> None:
        super().__init__()
        self.failing_method = failing_method
        self.error_message = error_message

    def create_team(self, name: str, members: list[str]) -> dict[str, Any]:
        if self.failing_method == "create_team":
            raise GitHubClientError(self.error_message)
        return super().create_team(name, members)

    def apply_branch_protection(
        self, repo: str, branch: str, settings: dict[str, Any]
    ) -> dict[str, Any]:
        if self.failing_method == "apply_branch_protection":
            raise GitHubClientError(self.error_message)
        return super().apply_branch_protection(repo, branch, settings)


@pytest.fixture
def temp_declared_root(tmp_path: Path) -> Path:
    """Create a temporary declared/ structure mirroring the real control plane root."""
    declared = tmp_path / "declared"
    declared.mkdir(parents=True, exist_ok=True)
    (declared / "products").mkdir(parents=True, exist_ok=True)
    (declared / "templates").mkdir(parents=True, exist_ok=True)

    people_content = {
        "people": [
            {
                "id": "founder-1",
                "github_login": "founder-1",
                "availability": "active",
                "capabilities": ["reviewer-matrix-change", "platform-admin"],
            },
            {
                "id": "lead-1",
                "github_login": "lead-1",
                "availability": "active",
                "capabilities": ["reviewer-matrix-change", "code-review", "architecture"],
            },
            {
                "id": "dev-1",
                "github_login": "dev-1",
                "availability": "active",
                "capabilities": ["code-review"],
            },
            {
                "id": "qa-1",
                "github_login": "qa-1",
                "availability": "active",
                "capabilities": ["verification", "code-review"],
            },
        ]
    }
    (declared / "people.yaml").write_text(yaml.safe_dump(people_content), encoding="utf-8")
    (declared / "platform.yaml").write_text(
        yaml.safe_dump({"reusable_workflow_versions": {"current": "workflows/v1"}}),
        encoding="utf-8",
    )
    (declared / "board.yaml").write_text(
        yaml.safe_dump({"items": [], "open_gate_items": [], "migrations": []}),
        encoding="utf-8",
    )
    (declared / "os-health.yaml").write_text(
        yaml.safe_dump({"products": {}}),
        encoding="utf-8",
    )
    (declared / "assets.yaml").write_text(
        yaml.safe_dump({"assets": []}),
        encoding="utf-8",
    )
    (declared / "shared-services.yaml").write_text(
        yaml.safe_dump({"services": [], "dependency_edges": []}),
        encoding="utf-8",
    )
    (declared / "templates" / "branch-protection.json").write_text(
        '{"enforce_admins": true, "required_pull_request_reviews": {"required_approving_review_count": 1}}',
        encoding="utf-8",
    )
    return tmp_path


def test_apply_all_steps_succeed(temp_declared_root: Path, capsys: pytest.CaptureFixture[str]):
    """All planned write steps succeed: writes equals step count and return code is 0."""
    parser = build_parser()
    args = parser.parse_args([
        "create-product",
        "--product",
        "alpha",
        "--live",
        "--apply",
        "--org",
        "lumiverse-org",
    ])

    plan = Plan(
        steps=[
            Step("repo_from_template", "create repo", StepKind.WRITE),
            Step("team", "create team", StepKind.WRITE),
            Step("branch_protection", "apply protection", StepKind.WRITE),
        ]
    )

    client = FakeGitHubClient()
    rc = _run_operation(
        args=args,
        operation="create-product",
        plan=plan,
        client=client,
        declared_dir=temp_declared_root,
    )

    assert rc == 0
    out, err = capsys.readouterr()
    assert "PLAN create-product steps=3 writes=3 manual=0" in out
    assert len(client.calls) == 3
    call_names = [c[0] for c in client.calls]
    assert call_names == ["create_repo_from_template", "create_team", "apply_branch_protection"]


def test_apply_seeded_failure_at_step_n_stops_execution(
    temp_declared_root: Path, capsys: pytest.CaptureFixture[str]
):
    """A seeded failure at step 2 stops execution, reports writes=1, and steps after 2 never run."""
    parser = build_parser()
    args = parser.parse_args([
        "create-product",
        "--product",
        "alpha",
        "--live",
        "--apply",
        "--org",
        "lumiverse-org",
    ])

    plan = Plan(
        steps=[
            Step("repo_from_template", "create repo", StepKind.WRITE),
            Step("team", "create team", StepKind.WRITE),
            Step("branch_protection", "apply protection", StepKind.WRITE),
        ]
    )

    failing_client = FailingGitHubClient(
        failing_method="create_team",
        error_message="HTTP 422: Team name already taken on GitHub org",
    )

    rc = _run_operation(
        args=args,
        operation="create-product",
        plan=plan,
        client=failing_client,
        declared_dir=temp_declared_root,
    )

    assert rc == 1  # Exits non-zero on partial failure
    out, err = capsys.readouterr()

    # Verify error reported to stderr with failed step and exception
    assert "FAILED during create-product at step team" in err
    assert "Team name already taken" in err
    assert "Steps succeeded before failure (1/3):" in err
    assert "- [write] repo_from_template: OK" in err
    assert "PLAN create-product steps=3 writes=1 manual=0 (EXECUTION FAILED)" in err

    # Verify that step 1 ran, but step 3 NEVER ran
    assert len(failing_client.calls) == 1
    assert failing_client.calls[0][0] == "create_repo_from_template"
    assert "apply_branch_protection" not in [c[0] for c in failing_client.calls]


def test_apply_empty_plan_performs_zero_writes(capsys: pytest.CaptureFixture[str]):
    """An empty plan under --live --apply writes=0 and exits 0."""
    parser = build_parser()
    args = parser.parse_args([
        "create-product",
        "--product",
        "alpha",
        "--live",
        "--apply",
        "--org",
        "lumiverse-org",
    ])

    empty_plan = Plan(steps=[])
    client = FakeGitHubClient()

    rc = _run_operation(
        args=args,
        operation="create-product",
        plan=empty_plan,
        client=client,
    )

    assert rc == 0
    out, err = capsys.readouterr()
    assert "PLAN create-product steps=0 writes=0 manual=0" in out
    assert len(client.calls) == 0


def test_cmd_create_product_live_apply_full_13_steps(
    temp_declared_root: Path, capsys: pytest.CaptureFixture[str]
):
    """_cmd_create_product under --live --apply executes all 13 automated steps."""
    parser = build_parser()
    args = parser.parse_args([
        "create-product",
        "--product",
        "pilot-test",
        "--live",
        "--apply",
        "--org",
        "lumiverse-org",
        "--executor",
        "founder-1",
        "--steps",
    ])

    client = FakeGitHubClient()
    rc = _cmd_create_product(
        args=args,
        client=client,
        declared_dir=temp_declared_root,
    )

    assert rc == 0
    out, err = capsys.readouterr()
    assert "PLAN create-product steps=13 writes=13 manual=2" in out
    assert "Action items (tracked manual steps):" in out
    assert "alert_channel" in out
    assert "support_intake_mailbox" in out

    # Verify local declared writes succeeded
    prod_yaml = temp_declared_root / "declared" / "products" / "pilot-test.yaml"
    assert prod_yaml.is_file()
    assert (temp_declared_root / "declared" / "products" / "pilot-test" / "Makefile").is_file()

    # Verify GitHub API writes through client
    call_names = {c[0] for c in client.calls}
    assert "create_repo_from_template" in call_names
    assert "create_team" in call_names
    assert "set_codeowners" in call_names
    assert "apply_branch_protection" in call_names
    assert "create_environment" in call_names
    assert "put_file" in call_names
