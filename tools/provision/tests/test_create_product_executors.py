"""Unit tests for tools/provision/executors.py (Task Group 2).

Covers all 13 automated steps in CREATE_PRODUCT_STEPS per MasterSpec §19.1.
Guarantees:
- Pure local/data writes execute against temporary fixture directories only.
- Real GitHub-API writes execute against FakeGitHubClient (zero live network calls).
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest
import yaml

from reconciler.cli import DeclaredState
from tools.provision.create_product import (
    CREATE_PRODUCT_STEPS,
    _current_product_contract_version,
)
from tools.provision.executors import (
    FakeGitHubClient,
    execute_all_steps,
    execute_branch_protection,
    execute_ci_workflows_pinned_tag,
    execute_codeowners,
    execute_environments,
    execute_local_environment_contract,
    execute_product_yaml,
    execute_register_dependency_graph,
    execute_register_grafana_scorecard_devlake,
    execute_register_portfolio_board,
    execute_repo_from_template,
    execute_required_endpoints,
    execute_step,
    execute_team,
    execute_verification_skeleton,
)
from tools.provision.repo import REQUIRED_COMMANDS, TEMPLATE_REPO


@pytest.fixture
def temp_fixture(tmp_path: Path) -> Path:
    """Creates a temporary fixture matching fixture-a layout."""
    fix_dir = tmp_path / "fixture-test"
    fix_dir.mkdir(parents=True)
    declared = fix_dir / "declared"
    declared.mkdir(parents=True)
    (declared / "products").mkdir(parents=True)
    (declared / "templates").mkdir(parents=True)

    # Minimal platform.yaml
    (declared / "platform.yaml").write_text(
        yaml.safe_dump({"reusable_workflow_versions": {"current": "workflows/v3"}}),
        encoding="utf-8",
    )

    # Minimal people.yaml
    (declared / "people.yaml").write_text(
        yaml.safe_dump({
            "people": [
                {
                    "id": "founder-1",
                    "github_login": "founder-1",
                    "availability": "active",
                    "capabilities": ["strategy", "platform-admin"],
                },
                {
                    "id": "lead-1",
                    "github_login": "lead-1",
                    "availability": "active",
                    "capabilities": ["reviewer-matrix-change"],
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
                    "capabilities": ["verification"],
                },
            ]
        }),
        encoding="utf-8",
    )

    # Minimal templates/branch-protection.json
    (declared / "templates" / "branch-protection.json").write_text(
        json.dumps({
            "required_status_checks": {"strict": True, "contexts": []},
            "enforce_admins": True,
            "required_pull_request_reviews": {"required_approving_review_count": 1},
        }),
        encoding="utf-8",
    )

    # Minimal board.yaml
    (declared / "board.yaml").write_text(
        yaml.safe_dump({"items": [], "open_gate_items": []}),
        encoding="utf-8",
    )

    # Minimal os-health.yaml
    (declared / "os-health.yaml").write_text(
        yaml.safe_dump({"products": {}}),
        encoding="utf-8",
    )

    # Minimal shared-services.yaml
    (declared / "shared-services.yaml").write_text(
        yaml.safe_dump({"services": []}),
        encoding="utf-8",
    )

    return fix_dir


def test_step_1_repo_from_template(temp_fixture: Path):
    client = FakeGitHubClient()
    res = execute_repo_from_template("omega", temp_fixture, client)
    assert res["name"] == "omega"
    assert len(client.calls) == 1
    op, payload = client.calls[0]
    assert op == "create_repo_from_template"
    assert payload["name"] == "omega"
    assert payload["template"] == TEMPLATE_REPO
    assert payload["private"] is True


def test_step_2_product_yaml(temp_fixture: Path):
    res = execute_product_yaml("omega", temp_fixture)
    expected_path = temp_fixture / "declared" / "products" / "omega.yaml"
    assert expected_path.is_file()
    data = yaml.safe_load(expected_path.read_text(encoding="utf-8"))
    assert data["product"] == "omega"
    assert data["contract_version"] == _current_product_contract_version()
    assert data["lifecycle"] == "draft"
    assert "assignments" in data


def test_step_3_team(temp_fixture: Path):
    execute_product_yaml("omega", temp_fixture)
    client = FakeGitHubClient()
    res = execute_team("omega", temp_fixture, client)
    assert res["name"] == "omega"
    assert "lead-1" in res["members"]
    assert "dev-1" in res["members"]
    assert "founder-1" in res["members"]


def test_step_4_codeowners(temp_fixture: Path):
    execute_product_yaml("omega", temp_fixture)
    client = FakeGitHubClient()
    res = execute_codeowners("omega", temp_fixture, client)
    assert res["status"] == "written"
    assert ("set_codeowners", {"repo": "omega", "content": client.files[("omega", ".github/CODEOWNERS")]}) in client.calls
    content = client.files[("omega", ".github/CODEOWNERS")]
    assert "verification/" in content


def test_step_5_branch_protection(temp_fixture: Path):
    client = FakeGitHubClient()
    res = execute_branch_protection("omega", temp_fixture, client)
    assert res["protected"] is True
    assert len(client.protections) == 1
    settings = client.protections[("omega", "main")]
    assert settings["enforce_admins"] is True


def test_step_6_environments(temp_fixture: Path):
    client = FakeGitHubClient()
    res = execute_environments("omega", temp_fixture, client)
    envs = [call[1]["name"] for call in client.calls if call[0] == "create_environment"]
    assert envs == ["development", "staging", "production"]
    assert client.environments[("omega", "production")]["protected_branches"] is True


def test_step_7_ci_workflows_pinned_tag(temp_fixture: Path):
    client = FakeGitHubClient()
    res = execute_ci_workflows_pinned_tag("omega", temp_fixture, client)
    assert res["status"] == "written"
    assert ("omega", ".github/workflows/ci.yml") in client.files
    content = client.files[("omega", ".github/workflows/ci.yml")]
    assert "workflows/v3" in content
    assert "omega" in content


def test_step_8_verification_skeleton(temp_fixture: Path):
    res = execute_verification_skeleton("omega", temp_fixture)
    v_dir = temp_fixture / "declared" / "products" / "omega" / "verification"
    assert (v_dir / "contract.yaml").is_file()
    assert (v_dir / "security-baseline.json").is_file()
    assert (v_dir / "licence-baseline.json").is_file()
    assert (v_dir / "slopsquat-baseline.json").is_file()


def test_step_9_local_environment_contract(temp_fixture: Path):
    res = execute_local_environment_contract("omega", temp_fixture)
    makefile = temp_fixture / "declared" / "products" / "omega" / "Makefile"
    assert makefile.is_file()
    text = makefile.read_text(encoding="utf-8")
    for cmd in REQUIRED_COMMANDS:
        assert f"{cmd}:" in text


def test_step_10_required_endpoints(temp_fixture: Path):
    client = FakeGitHubClient()
    res = execute_required_endpoints("omega", temp_fixture, client)
    assert res["status"] == "written"
    assert ("omega", "app/endpoints.py") in client.files
    text = client.files[("omega", "app/endpoints.py")]
    assert "def health()" in text
    assert "def version()" in text
    assert "def metrics()" in text


def test_step_11_register_portfolio_board(temp_fixture: Path):
    res = execute_register_portfolio_board("omega", temp_fixture)
    board_path = temp_fixture / "declared" / "board.yaml"
    data = yaml.safe_load(board_path.read_text(encoding="utf-8"))
    assert any(it.get("product") == "omega" for it in data.get("items", []))


def test_step_12_register_grafana_scorecard_devlake(temp_fixture: Path):
    res = execute_register_grafana_scorecard_devlake("omega", temp_fixture)
    health_path = temp_fixture / "declared" / "os-health.yaml"
    data = yaml.safe_load(health_path.read_text(encoding="utf-8"))
    assert "omega" in data.get("products", {})
    assert data["products"]["omega"]["grafana_dashboard"] is True


def test_step_13_register_dependency_graph(temp_fixture: Path):
    res = execute_register_dependency_graph("omega", temp_fixture)
    services_path = temp_fixture / "declared" / "shared-services.yaml"
    data = yaml.safe_load(services_path.read_text(encoding="utf-8"))
    assert "omega" in data.get("services", [])


def test_execute_all_13_steps_in_order(temp_fixture: Path):
    client = FakeGitHubClient()
    results = execute_all_steps("omega", temp_fixture, client)
    assert list(results.keys()) == list(CREATE_PRODUCT_STEPS)
    assert len(results) == 13

    # Confirm pure local files were created in fixture
    assert (temp_fixture / "declared" / "products" / "omega.yaml").is_file()
    assert (temp_fixture / "declared" / "products" / "omega" / "verification" / "contract.yaml").is_file()
    assert (temp_fixture / "declared" / "products" / "omega" / "Makefile").is_file()

    # Confirm client recorded the 7 API calls
    call_names = [c[0] for c in client.calls]
    assert "create_repo_from_template" in call_names
    assert "create_team" in call_names
    assert "set_codeowners" in call_names
    assert "apply_branch_protection" in call_names
    assert "create_environment" in call_names
    assert "put_file" in call_names
