"""L3-P4-07 / Generic Product Provisioning Verification (Task Group 2).

Proves the `create-product` plan and actual step content generation are
genuinely correct for ANY product name (fully offline, zero live writes).

Validates:
1. Full plan composition (both fixture-based and live-roster-based) across
   varied synthetic product names: exactly 13 automated + 2 manual steps,
   no unfilled placeholders ('{{' or '{product}' or '{roster_note}').
2. Structured content validity:
   - `product.yaml`: validated against the frozen JSON Schema under
     contracts/registry/product.contract.v<N>.json (resolved dynamically via
     _current_product_contract_version()).
   - `CODEOWNERS`: validated human identities, rule ordering, zero bots.
   - `branch_protection`: validated against branch protection invariant rules.
   - `environments`: validated development, staging, and production policies.
3. Negative tests:
   - Deliberately invalid contract fields rejected by jsonschema validator.
   - Machine identities in CODEOWNERS rejected by MachineIdentityInCodeowners.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
import yaml
import jsonschema

from tools.provision.codeowners import MachineIdentityInCodeowners
from tools.provision.create_product import (
    CREATE_PRODUCT_MANUAL_STEPS,
    CREATE_PRODUCT_STEPS,
    _CONTRACTS_REGISTRY_ROOT,
    _current_product_contract_version,
    build_create_product_plan,
    build_create_product_plan_against_live_roster,
)
from tools.provision.executors import (
    FakeGitHubClient,
    execute_branch_protection,
    execute_codeowners,
    execute_environments,
    execute_product_yaml,
)
from tools.provision.plan import StepKind


# Varied synthetic product names covering casing, characters, edge cases, and collisions
SYNTHETIC_PRODUCT_NAMES: tuple[str, ...] = (
    "Product-9",                 # standard sequence continuation (PascalCase with hyphen & digit)
    "Alpha-Service",             # mixed casing with hyphen
    "product_underscore_42",     # lowercase with underscores and numbers
    "X",                         # single-character edge case
    "team-lead",                 # collision test: collides with org-wide role team @team-lead
    "billing-stream-processor",  # multi-token kebab-case
)


@pytest.fixture
def product_contract_schema() -> dict:
    """Load the current product contract JSON Schema dynamically."""
    version = _current_product_contract_version()
    schema_path = _CONTRACTS_REGISTRY_ROOT / f"product.contract.v{version}.json"
    assert schema_path.is_file(), f"Expected frozen contract schema at {schema_path}"
    return json.loads(schema_path.read_text(encoding="utf-8"))


@pytest.fixture
def temp_provision_fixture(tmp_path: Path) -> Path:
    """Scaffold a temporary fixture with declared platform and people."""
    fix_dir = tmp_path / "fixture-generic"
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

    # Standard people roster
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

    # Branch protection template
    (declared / "templates" / "branch-protection.json").write_text(
        json.dumps({
            "required_status_checks": {"strict": True, "contexts": ["control-plane/blocking-drift"]},
            "enforce_admins": True,
            "allow_force_pushes": False,
            "allow_deletions": False,
            "required_pull_request_reviews": {
                "required_approving_review_count": 1,
                "require_code_owner_reviews": True,
                "dismiss_stale_reviews": True,
                "require_last_push_approval": True,
            },
        }),
        encoding="utf-8",
    )

    return fix_dir


# ==============================================================================
# 2a. Plan Composition & Formatting across Generic Product Names
# ==============================================================================


@pytest.mark.parametrize("product_name", SYNTHETIC_PRODUCT_NAMES)
def test_plan_composition_fixture_based(product_name: str):
    """Assert build_create_product_plan produces exact steps and no unfilled placeholders."""
    plan = build_create_product_plan(product_name, "fixture-a")
    assert len(plan.steps) == 13
    assert len(plan.manual_steps) == 2
    assert [s.id for s in plan.steps] == list(CREATE_PRODUCT_STEPS)
    assert [s.id for s in plan.manual_steps] == list(CREATE_PRODUCT_MANUAL_STEPS)
    assert all(s.kind == StepKind.WRITE for s in plan.steps)
    assert all(s.kind == StepKind.MANUAL for s in plan.manual_steps)

    for s in list(plan.steps) + list(plan.manual_steps):
        assert "{{" not in s.description
        assert "}}" not in s.description
        assert "{product}" not in s.description
        assert "{roster_note}" not in s.description
        assert s.description.startswith(f"{product_name}:")


@pytest.mark.parametrize("product_name", SYNTHETIC_PRODUCT_NAMES)
def test_plan_composition_live_roster_based(product_name: str):
    """Assert build_create_product_plan_against_live_roster produces exact steps and no unfilled placeholders."""
    plan = build_create_product_plan_against_live_roster(product_name)
    assert len(plan.steps) == 13
    assert len(plan.manual_steps) == 2
    assert [s.id for s in plan.steps] == list(CREATE_PRODUCT_STEPS)
    assert [s.id for s in plan.manual_steps] == list(CREATE_PRODUCT_MANUAL_STEPS)
    assert all(s.kind == StepKind.WRITE for s in plan.steps)
    assert all(s.kind == StepKind.MANUAL for s in plan.manual_steps)

    for s in list(plan.steps) + list(plan.manual_steps):
        assert "{{" not in s.description
        assert "}}" not in s.description
        assert "{product}" not in s.description
        assert "{roster_note}" not in s.description
        assert s.description.startswith(f"{product_name}:")
        assert "7 product(s) registered today" in s.description or not s.id.startswith("register_")


# ==============================================================================
# 2b. Structured Content Generation & Real Schema Validation
# ==============================================================================


@pytest.mark.parametrize("product_name", SYNTHETIC_PRODUCT_NAMES)
def test_product_yaml_schema_validity(
    product_name: str, temp_provision_fixture: Path, product_contract_schema: dict
):
    """Assert generated product.yaml content strictly satisfies the frozen contract schema."""
    res = execute_product_yaml(product_name, temp_provision_fixture)
    target_path = Path(res["path"])
    assert target_path.is_file()

    doc = yaml.safe_load(target_path.read_text(encoding="utf-8"))

    # Validate against frozen JSON Schema under contracts/registry/
    jsonschema.validate(instance=doc, schema=product_contract_schema)

    # Assert critical structural bindings
    assert doc["contract_version"] == _current_product_contract_version()
    assert doc["identity"]["product_id"] == product_name
    assert doc["identity"]["repository"] == product_name
    assert doc["conformance_profile"] == "service"
    assert doc["platform_compatibility"] == "supported"
    assert isinstance(doc["assignments"], list)
    assert len(doc["assignments"]) >= 1


@pytest.mark.parametrize("product_name", SYNTHETIC_PRODUCT_NAMES)
def test_codeowners_content_validity(product_name: str, temp_provision_fixture: Path):
    """Assert generated CODEOWNERS content adheres to §11.3 rules and names human logins only."""
    execute_product_yaml(product_name, temp_provision_fixture)
    client = FakeGitHubClient()
    res = execute_codeowners(product_name, temp_provision_fixture, client)
    assert res["status"] == "written"

    content = client.files[(product_name, ".github/CODEOWNERS")]
    assert len(content.strip()) > 0

    # Human-only enforcement (§11.3)
    assert "[bot]" not in content
    assert "ci-bot" not in content

    # Rule checks
    assert "verification/ @qa-1" in content
    assert "product.yaml @lead-1" in content
    assert ".github/workflows/ @lead-1" in content
    assert "migrations/ @lead-1" in content


@pytest.mark.parametrize("product_name", SYNTHETIC_PRODUCT_NAMES)
def test_branch_protection_content_validity(product_name: str, temp_provision_fixture: Path):
    """Assert branch protection settings satisfy §11.3 invariant requirements."""
    client = FakeGitHubClient()
    res = execute_branch_protection(product_name, temp_provision_fixture, client)
    assert res["protected"] is True

    settings = client.protections[(product_name, "main")]

    # Enforce §11.3 non-negotiable security controls
    assert settings["enforce_admins"] is True
    assert settings["allow_force_pushes"] is False
    assert settings["allow_deletions"] is False

    pr_reviews = settings["required_pull_request_reviews"]
    assert pr_reviews["required_approving_review_count"] >= 1
    assert pr_reviews["require_code_owner_reviews"] is True
    assert pr_reviews["require_last_push_approval"] is True
    assert pr_reviews["dismiss_stale_reviews"] is True


@pytest.mark.parametrize("product_name", SYNTHETIC_PRODUCT_NAMES)
def test_environments_content_validity(product_name: str, temp_provision_fixture: Path):
    """Assert environment configurations correctly isolate staging and production policies."""
    client = FakeGitHubClient()
    res = execute_environments(product_name, temp_provision_fixture, client)
    envs = res["environments"]
    assert len(envs) == 3

    env_names = {e["name"] for e in envs}
    assert env_names == {"development", "staging", "production"}

    # Development has no deployment branch policy
    assert client.environments[(product_name, "development")] is None

    # Staging & Production have protected branch and tag policies (§33.4)
    for env in ("staging", "production"):
        policy = client.environments[(product_name, env)]
        assert policy is not None
        assert policy["protected_branches"] is True
        assert policy["custom_branch_policies"] is True


# ==============================================================================
# 2c. Deliberate Negative Tests (Validator & Generator Rejection)
# ==============================================================================


def test_schema_rejection_on_invalid_contract_version(
    temp_provision_fixture: Path, product_contract_schema: dict
):
    """Negative test: a contract_version differing from pinned const 2 must be rejected."""
    res = execute_product_yaml("Invalid-Version-Prod", temp_provision_fixture)
    doc = yaml.safe_load(Path(res["path"]).read_text(encoding="utf-8"))
    doc["contract_version"] = 999

    with pytest.raises(jsonschema.ValidationError) as exc_info:
        jsonschema.validate(instance=doc, schema=product_contract_schema)
    assert "contract_version" in str(exc_info.value) or "2" in str(exc_info.value)


def test_schema_rejection_on_invalid_enum(
    temp_provision_fixture: Path, product_contract_schema: dict
):
    """Negative test: an unapproved reliability_criticality enum value must be rejected."""
    res = execute_product_yaml("Invalid-Enum-Prod", temp_provision_fixture)
    doc = yaml.safe_load(Path(res["path"]).read_text(encoding="utf-8"))
    doc["classification"]["reliability_criticality"] = "extreme-risk-invalid"

    with pytest.raises(jsonschema.ValidationError) as exc_info:
        jsonschema.validate(instance=doc, schema=product_contract_schema)
    assert "extreme-risk-invalid" in str(exc_info.value)


def test_schema_rejection_on_negative_budget(
    temp_provision_fixture: Path, product_contract_schema: dict
):
    """Negative test: PROD-R6 budget ceiling and expected must be positive numbers."""
    res = execute_product_yaml("Negative-Budget-Prod", temp_provision_fixture)
    doc = yaml.safe_load(Path(res["path"]).read_text(encoding="utf-8"))
    doc["infrastructure"]["monthly_budget_band"]["expected"] = -100

    with pytest.raises(jsonschema.ValidationError) as exc_info:
        jsonschema.validate(instance=doc, schema=product_contract_schema)
    assert "exclusiveMinimum" in str(exc_info.value) or "-100" in str(exc_info.value)


def test_schema_rejection_on_rule_prod_r1_violation(
    temp_provision_fixture: Path, product_contract_schema: dict
):
    """Negative test: PROD-R1 requires performance='required' when reliability_criticality is critical."""
    res = execute_product_yaml("R1-Violation-Prod", temp_provision_fixture)
    doc = yaml.safe_load(Path(res["path"]).read_text(encoding="utf-8"))
    doc["classification"]["reliability_criticality"] = "critical"
    doc["verification"]["performance"] = "optional"

    with pytest.raises(jsonschema.ValidationError) as exc_info:
        jsonschema.validate(instance=doc, schema=product_contract_schema)
    assert "verification" in str(exc_info.value) or "performance" in str(exc_info.value)


def test_codeowners_rejection_on_machine_identity(temp_provision_fixture: Path):
    """Negative test: machine accounts or unauthorized identities raise MachineIdentityInCodeowners."""
    # Write a product.yaml with a machine bot in the primary_owner slot
    execute_product_yaml(
        "Bot-Owned-Prod",
        temp_provision_fixture,
        primary_owner="ci-automation-worker[bot]",
    )
    client = FakeGitHubClient()
    with pytest.raises(MachineIdentityInCodeowners) as exc_info:
        execute_codeowners("Bot-Owned-Prod", temp_provision_fixture, client)
    assert "machine identity" in str(exc_info.value) or "ci-automation-worker[bot]" in str(exc_info.value)
