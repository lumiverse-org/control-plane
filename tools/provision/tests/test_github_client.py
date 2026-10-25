"""Unit tests for RealGitHubClient (tools.provision.github_client).

All tests execute strictly offline with zero live gh CLI calls or network access:
subprocess.run is mocked in every test to simulate GitHub API responses and failure modes.
"""

from __future__ import annotations

import base64
import json
import subprocess
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tools.provision.executors import GitHubClient
from tools.provision.github_client import GitHubClientError, RealGitHubClient


def test_real_github_client_implements_protocol():
    """Verify RealGitHubClient satisfies the GitHubClient Protocol."""
    client = RealGitHubClient(org="test-org")
    assert isinstance(client, GitHubClient)


def test_real_github_client_requires_non_empty_org():
    """Verify RealGitHubClient requires an explicit, non-empty org and forbids silent defaults."""
    with pytest.raises(TypeError):
        RealGitHubClient()  # type: ignore[call-arg]

    with pytest.raises(ValueError, match="org must be a non-empty string"):
        RealGitHubClient(org="")

    with pytest.raises(ValueError, match="org must be a non-empty string"):
        RealGitHubClient(org="   ")


@patch("subprocess.run")
def test_create_repo_from_template_happy_path(mock_run: MagicMock):
    """Happy path: create_repo_from_template invokes gh repo create with correct flags."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=["gh", "repo", "create"],
        returncode=0,
        stdout="https://github.com/test-org/new-prod\n",
        stderr="",
    )

    client = RealGitHubClient(org="test-org")
    res = client.create_repo_from_template("new-prod", "product-template", private=True)

    assert res["status"] == "created"
    assert res["full_name"] == "test-org/new-prod"
    mock_run.assert_called_once_with(
        [
            "gh",
            "repo",
            "create",
            "test-org/new-prod",
            "--template",
            "test-org/product-template",
            "--private",
        ],
        input=None,
        capture_output=True,
        text=True,
    )


@patch("subprocess.run")
def test_create_repo_from_template_failure(mock_run: MagicMock):
    """Failure path: raises GitHubClientError when gh repo create exits non-zero."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=["gh", "repo", "create"],
        returncode=1,
        stdout="",
        stderr="GraphQL: Name already exists on this account (createRepository)",
    )

    client = RealGitHubClient(org="test-org")
    with pytest.raises(GitHubClientError, match="Name already exists"):
        client.create_repo_from_template("existing-prod", "product-template", private=True)


@patch("subprocess.run")
def test_create_team_happy_path(mock_run: MagicMock):
    """Happy path: create_team creates the team and assigns memberships."""
    # First call: team creation. Subsequent calls: memberships.
    mock_run.side_effect = [
        subprocess.CompletedProcess(
            args=["gh", "api"],
            returncode=0,
            stdout=json.dumps({"id": 101, "name": "new-team", "slug": "new-team"}),
            stderr="",
        ),
        subprocess.CompletedProcess(args=["gh", "api"], returncode=0, stdout="{}", stderr=""),
        subprocess.CompletedProcess(args=["gh", "api"], returncode=0, stdout="{}", stderr=""),
    ]

    client = RealGitHubClient(org="test-org")
    res = client.create_team("new-team", ["alice", "bob"])

    assert res["name"] == "new-team"
    assert res["members"] == ["alice", "bob"]
    assert mock_run.call_count == 3

    # Verify team creation call
    mock_run.assert_any_call(
        ["gh", "api", "orgs/test-org/teams", "-f", "name=new-team"],
        input=None,
        capture_output=True,
        text=True,
    )
    # Verify membership calls
    mock_run.assert_any_call(
        ["gh", "api", "orgs/test-org/teams/new-team/memberships/alice", "-X", "PUT"],
        input=None,
        capture_output=True,
        text=True,
    )
    mock_run.assert_any_call(
        ["gh", "api", "orgs/test-org/teams/new-team/memberships/bob", "-X", "PUT"],
        input=None,
        capture_output=True,
        text=True,
    )


@patch("subprocess.run")
def test_create_team_uses_slug_from_response_for_memberships(mock_run: MagicMock):
    """Verify create_team uses the server-returned slug rather than the raw input name for memberships."""
    # Deliberately non-slug-shaped name with spaces and uppercase letters
    team_name = "Product 9 Core Team"
    returned_slug = "product-9-core-team"

    mock_run.side_effect = [
        subprocess.CompletedProcess(
            args=["gh", "api"],
            returncode=0,
            stdout=json.dumps({"id": 102, "name": team_name, "slug": returned_slug}),
            stderr="",
        ),
        subprocess.CompletedProcess(args=["gh", "api"], returncode=0, stdout="{}", stderr=""),
    ]

    client = RealGitHubClient(org="test-org")
    res = client.create_team(team_name, ["alice"])

    assert res["name"] == team_name
    assert res["slug"] == returned_slug
    assert res["members"] == ["alice"]
    assert mock_run.call_count == 2

    # Creation call uses raw name
    mock_run.assert_any_call(
        ["gh", "api", f"orgs/test-org/teams", "-f", f"name={team_name}"],
        input=None,
        capture_output=True,
        text=True,
    )
    # Membership call MUST use the slug, NOT the raw name
    mock_run.assert_any_call(
        ["gh", "api", f"orgs/test-org/teams/{returned_slug}/memberships/alice", "-X", "PUT"],
        input=None,
        capture_output=True,
        text=True,
    )


@patch("subprocess.run")
def test_create_team_failure_on_team_creation(mock_run: MagicMock):
    """Failure path: raises GitHubClientError when team creation fails."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=["gh", "api"],
        returncode=1,
        stdout="",
        stderr="HTTP 422: Validation Failed",
    )

    client = RealGitHubClient(org="test-org")
    with pytest.raises(GitHubClientError, match="Validation Failed"):
        client.create_team("bad-team", ["alice"])


@patch("subprocess.run")
def test_create_team_failure_on_membership(mock_run: MagicMock):
    """Failure path: raises GitHubClientError when assigning a team member fails."""
    mock_run.side_effect = [
        subprocess.CompletedProcess(
            args=["gh", "api"],
            returncode=0,
            stdout=json.dumps({"id": 101, "name": "new-team"}),
            stderr="",
        ),
        subprocess.CompletedProcess(
            args=["gh", "api"],
            returncode=1,
            stdout="",
            stderr="HTTP 404: Not Found user 'unknown-user'",
        ),
    ]

    client = RealGitHubClient(org="test-org")
    with pytest.raises(GitHubClientError, match="Not Found user"):
        client.create_team("new-team", ["unknown-user"])


@patch("subprocess.run")
def test_create_team_failure_on_malformed_json_response(mock_run: MagicMock):
    """Failure path: raises GitHubClientError when team creation returns malformed JSON."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=["gh", "api"],
        returncode=0,
        stdout="{ malformed or truncated json response",
        stderr="",
    )

    client = RealGitHubClient(org="test-org")
    with pytest.raises(GitHubClientError, match="Failed to parse team creation response"):
        client.create_team("new-team", ["alice"])


@patch("subprocess.run")
def test_create_team_failure_on_empty_json_response(mock_run: MagicMock):
    """Failure path: raises GitHubClientError when team creation returns empty JSON object."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=["gh", "api"],
        returncode=0,
        stdout="{}",
        stderr="",
    )

    client = RealGitHubClient(org="test-org")
    with pytest.raises(GitHubClientError, match="returned empty JSON object"):
        client.create_team("new-team", ["alice"])


@patch("subprocess.run")
def test_put_file_create_case_no_prior_file(mock_run: MagicMock):
    """put_file create case: GET returns 404 -> PUT executes without sha."""
    mock_run.side_effect = [
        # GET contents returns 404 Not Found
        subprocess.CompletedProcess(
            args=["gh", "api", "repos/test-org/repo-a/contents/README.md"],
            returncode=1,
            stdout="",
            stderr="gh: Not Found (HTTP 404)",
        ),
        # PUT contents returns 201 Created
        subprocess.CompletedProcess(
            args=["gh", "api", "repos/test-org/repo-a/contents/README.md"],
            returncode=0,
            stdout=json.dumps({"content": {"name": "README.md", "path": "README.md"}}),
            stderr="",
        ),
    ]

    client = RealGitHubClient(org="test-org")
    res = client.put_file("repo-a", "README.md", "# Hello World", "Initial commit")

    assert res["status"] == "written"
    assert res["action"] == "created"
    assert mock_run.call_count == 2

    # Verify PUT payload has no "sha" key
    put_call = mock_run.call_args_list[1]
    put_input = json.loads(put_call.kwargs["input"])
    assert "sha" not in put_input
    assert put_input["message"] == "Initial commit"
    assert base64.b64decode(put_input["content"]).decode("utf-8") == "# Hello World"


@patch("subprocess.run")
def test_put_file_update_case_prior_file_exists(mock_run: MagicMock):
    """put_file update case: GET returns 200 with sha -> PUT supplies sha."""
    prior_sha = "abc123def4567890123456789012345678901234"
    mock_run.side_effect = [
        # GET contents returns 200 OK with blob sha
        subprocess.CompletedProcess(
            args=["gh", "api", "repos/test-org/repo-a/contents/README.md"],
            returncode=0,
            stdout=json.dumps({"name": "README.md", "sha": prior_sha, "type": "file"}),
            stderr="",
        ),
        # PUT contents returns 200 OK
        subprocess.CompletedProcess(
            args=["gh", "api", "repos/test-org/repo-a/contents/README.md"],
            returncode=0,
            stdout=json.dumps({"content": {"name": "README.md", "sha": "newsha999"}}),
            stderr="",
        ),
    ]

    client = RealGitHubClient(org="test-org")
    res = client.put_file("repo-a", "README.md", "# Updated Content", "Update doc")

    assert res["status"] == "written"
    assert res["action"] == "updated"
    assert mock_run.call_count == 2

    # Verify PUT payload includes the prior sha
    put_call = mock_run.call_args_list[1]
    put_input = json.loads(put_call.kwargs["input"])
    assert put_input["sha"] == prior_sha
    assert put_input["message"] == "Update doc"
    assert base64.b64decode(put_input["content"]).decode("utf-8") == "# Updated Content"


@patch("subprocess.run")
def test_put_file_failure_on_non_404_get(mock_run: MagicMock):
    """put_file fails if GET contents fails with a non-404 error (e.g. 401/403)."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=["gh", "api"],
        returncode=1,
        stdout="",
        stderr="gh: Bad credentials (HTTP 401)",
    )

    client = RealGitHubClient(org="test-org")
    with pytest.raises(GitHubClientError, match="Bad credentials"):
        client.put_file("repo-a", "README.md", "content", "msg")


@patch("subprocess.run")
def test_put_file_failure_on_put(mock_run: MagicMock):
    """put_file fails if PUT contents returns non-zero exit code."""
    mock_run.side_effect = [
        subprocess.CompletedProcess(
            args=["gh", "api"],
            returncode=1,
            stdout="",
            stderr="gh: Not Found (HTTP 404)",
        ),
        subprocess.CompletedProcess(
            args=["gh", "api"],
            returncode=1,
            stdout="",
            stderr="gh: Branch protected; require review (HTTP 403)",
        ),
    ]

    client = RealGitHubClient(org="test-org")
    with pytest.raises(GitHubClientError, match="Branch protected"):
        client.put_file("repo-a", "README.md", "content", "msg")


@patch("subprocess.run")
def test_set_codeowners_delegates_to_put_file(mock_run: MagicMock):
    """set_codeowners delegates to put_file with path .github/CODEOWNERS."""
    mock_run.side_effect = [
        subprocess.CompletedProcess(
            args=["gh", "api"],
            returncode=1,
            stdout="",
            stderr="gh: Not Found (HTTP 404)",
        ),
        subprocess.CompletedProcess(
            args=["gh", "api"],
            returncode=0,
            stdout=json.dumps({"content": {"path": ".github/CODEOWNERS"}}),
            stderr="",
        ),
    ]

    client = RealGitHubClient(org="test-org")
    res = client.set_codeowners("my-repo", "* @lead-1")

    assert res["status"] == "written"
    assert res["path"] == ".github/CODEOWNERS"


@patch("subprocess.run")
def test_apply_branch_protection_happy_path(mock_run: MagicMock):
    """Happy path: apply_branch_protection applies settings JSON on stdin."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=["gh", "api"],
        returncode=0,
        stdout=json.dumps({"url": "https://api.github.com/repos/test-org/repo-a/branches/main/protection"}),
        stderr="",
    )

    client = RealGitHubClient(org="test-org")
    settings = {
        "required_status_checks": {"strict": True, "contexts": ["ci"]},
        "enforce_admins": True,
    }
    res = client.apply_branch_protection("repo-a", "main", settings)

    assert res["branch"] == "main"
    assert res["protected"] is True
    mock_run.assert_called_once_with(
        [
            "gh",
            "api",
            "repos/test-org/repo-a/branches/main/protection",
            "-X",
            "PUT",
            "--input",
            "-",
        ],
        input=json.dumps(settings),
        capture_output=True,
        text=True,
    )


@patch("subprocess.run")
def test_apply_branch_protection_failure(mock_run: MagicMock):
    """Failure path: raises GitHubClientError when applying branch protection fails."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=["gh", "api"],
        returncode=1,
        stdout="",
        stderr="HTTP 422: Upgrade to GitHub Pro or make repository public",
    )

    client = RealGitHubClient(org="test-org")
    with pytest.raises(GitHubClientError, match="Upgrade to GitHub Pro"):
        client.apply_branch_protection("repo-a", "main", {})


@patch("subprocess.run")
def test_create_environment_happy_path(mock_run: MagicMock):
    """Happy path: create_environment sets deployment policy and adds branch/tag rules."""
    mock_run.side_effect = [
        # PUT environment
        subprocess.CompletedProcess(
            args=["gh", "api"],
            returncode=0,
            stdout=json.dumps({"id": 1, "name": "production"}),
            stderr="",
        ),
        # POST branch policy
        subprocess.CompletedProcess(args=["gh", "api"], returncode=0, stdout="{}", stderr=""),
        # POST tag policy
        subprocess.CompletedProcess(args=["gh", "api"], returncode=0, stdout="{}", stderr=""),
    ]

    client = RealGitHubClient(org="test-org")
    policy = {
        "custom_branch_policies": True,
        "policies": [
            {"name": "main", "type": "branch"},
            {"name": "v*", "type": "tag"},
        ],
    }
    res = client.create_environment("repo-a", "production", deployment_policy=policy)

    assert res["name"] == "production"
    assert res["status"] == "created"
    assert mock_run.call_count == 3

    # Check environment PUT had custom_branch_policies enabled
    env_call = mock_run.call_args_list[0]
    env_body = json.loads(env_call.kwargs["input"])
    assert env_body["deployment_branch_policy"]["custom_branch_policies"] is True
    assert env_body["deployment_branch_policy"]["protected_branches"] is False


@patch("subprocess.run")
def test_create_environment_failure(mock_run: MagicMock):
    """Failure path: raises GitHubClientError when creating environment fails."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=["gh", "api"],
        returncode=1,
        stdout="",
        stderr="HTTP 404: Environment feature not available",
    )

    client = RealGitHubClient(org="test-org")
    with pytest.raises(GitHubClientError, match="Environment feature not available"):
        client.create_environment("repo-a", "production")
