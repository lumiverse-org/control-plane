"""L3-P4-07: the `create-product` orchestrator (spec §19.1 CREATE PRODUCT
block; §12.6; AT-001).

Composes the plan in **exactly** the §19.1 order: thirteen automated
steps (`CREATE_PRODUCT_STEPS` below), then two manual steps
(`CREATE_PRODUCT_MANUAL_STEPS`) - §19.1: "or, where the provider offers
no automation, tracked manual steps emitted as issues so neither is
silently missing."

Section 7's dry-run summary line is `PLAN <op> steps=<int> writes=<int>
manual=<int>`, and the worked examples for this operation and for
add-person (§12.6) both read the count of *automated* steps into
`steps=` and the count of manual ones into a separate `manual=` -
thirteen and two here, never fifteen. `CreateProductPlan` keeps that
split by carrying the two manual steps in `.manual_steps`, a field
`tools.provision.plan.Plan` itself has no reason to know about, rather
than folding them into `.steps` where `len()` would count them twice
over.

Steps 11-13 (`register_portfolio_board`, `register_grafana_scorecard_devlake`,
`register_dependency_graph`) enumerate the current product roster by
reading it off the registry (`reconciler.cli.DeclaredState.products`,
the same accessor `tools/provision/teams.py` uses) - never a literal
list of product names anywhere in this module. That is what §101
invariants 52-53 and AT-001 require: "Add product 21" must never need
to hand-edit a dashboard, workflow or script that carries its own copy
of the product list, and this module is one of the places that claim is
checked against.

Step Executor Implementation Status (tools/provision/executors.py):
All 13 automated steps have real executor logic built:
- Purely local/data writes (product_yaml, verification_skeleton,
  local_environment_contract, register_portfolio_board,
  register_grafana_scorecard_devlake, register_dependency_graph) write to
  target fixture directories under test.
- External GitHub API writes (repo_from_template, team, codeowners,
  branch_protection, environments, ci_workflows_pinned_tag, required_endpoints)
  execute against an injectable GitHubClient protocol and are tested with
  FakeGitHubClient.
NOTE: No step is executed against live infrastructure; the live GitHub API
client implementation remains pending separate, explicit authorization.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import json

from reconciler.cli import DeclaredState
from tools.provision.plan import Plan, Step, StepKind
from tools.provision.repo import REQUIRED_COMMANDS, TEMPLATE_REPO

# §19.1 CREATE PRODUCT block, thirteen automated steps, verbatim order.
CREATE_PRODUCT_STEPS: tuple[str, ...] = (
    "repo_from_template",
    "product_yaml",
    "team",
    "codeowners",
    "branch_protection",
    "environments",
    "ci_workflows_pinned_tag",
    "verification_skeleton",
    "local_environment_contract",
    "required_endpoints",
    "register_portfolio_board",
    "register_grafana_scorecard_devlake",
    "register_dependency_graph",
)

# §19.1: the two steps with no available provider automation, tracked as
# issues instead so neither is silently missing.
CREATE_PRODUCT_MANUAL_STEPS: tuple[str, ...] = ("alert_channel", "support_intake_mailbox")


def apply_resolved_product_identity(document: dict[str, Any], repo_name: str) -> dict[str, Any]:
    """Set identity.product_id and identity.repository from the resolved repo name.

    `gh repo create --template` copies product-template's product.yaml unchanged,
    so both fields still say `product-template` until this runs. Other identity
    keys (team, display name) stay as they were.
    """
    name = str(repo_name).strip()
    if not name:
        raise ValueError("resolved repository name is required to stamp product identity")
    identity = document.get("identity")
    if not isinstance(identity, dict):
        identity = {}
        document["identity"] = identity
    identity["product_id"] = name
    identity["repository"] = name
    return document


_CONTRACTS_REGISTRY_ROOT = Path(__file__).resolve().parent.parent.parent / "contracts" / "registry"
_PRODUCT_CONTRACT_FILENAME = re.compile(r"^product\.contract\.v(\d+)\.json$")


class ProductContractVersionUnavailable(RuntimeError):
    """The current product contract_version could not be read from contracts/registry/."""


def _current_product_contract_version() -> int:
    """The `contract_version` new product.yaml files are written at.

    Read from `contracts/registry/product.contract.v<N>.json` (the
    frozen, L0-owned contract every lane consumes rather than reaching
    into another lane's source tree) - never a literal version number
    in this module, so a future contract bump needs no edit here.
    """
    versioned: list[tuple[int, Path]] = []
    if _CONTRACTS_REGISTRY_ROOT.is_dir():
        for path in _CONTRACTS_REGISTRY_ROOT.glob("product.contract.v*.json"):
            match = _PRODUCT_CONTRACT_FILENAME.match(path.name)
            if match:
                versioned.append((int(match.group(1)), path))
    if not versioned:
        raise ProductContractVersionUnavailable(
            f"no product.contract.v<N>.json found under {_CONTRACTS_REGISTRY_ROOT}"
        )
    _, latest_path = max(versioned)
    schema: dict[str, Any] = json.loads(latest_path.read_text(encoding="utf-8"))
    const = (schema.get("properties") or {}).get("contract_version", {}).get("const")
    if const is None:
        raise ProductContractVersionUnavailable(
            f"{latest_path} does not pin contract_version via a JSON Schema 'const'"
        )
    return const


def registered_product_ids(fixture: str) -> tuple[str, ...]:
    """The product roster read off the registry for `fixture`, sorted.

    The one accessor steps 11-13 use to learn what is already
    registered - `reconciler.cli.DeclaredState.products`, loaded from
    `declared/products/*.yaml`. Nothing in this module holds a second,
    hand-maintained copy of that roster (§101 invariants 52-53).
    """
    return tuple(sorted(DeclaredState(fixture).products.keys()))


@dataclass
class CreateProductPlan(Plan):
    """The create-product plan: `.steps` holds the thirteen automated
    steps (`StepKind.WRITE`); `.manual_steps` holds the two manual ones,
    kept out of `.steps` so `summary_line`'s `steps=` reports thirteen,
    not fifteen, while `manual=` still reports both.
    """

    manual_steps: tuple[Step, ...] = ()

    def summary_line(self, operation: str, *, applied: bool = False, writes: int | None = None) -> str:
        if writes is None:
            writes = self.count(StepKind.WRITE) if applied else 0
        return f"PLAN {operation} steps={len(self.steps)} writes={writes} manual={len(self.manual_steps)}"


def _automated_step_descriptions_from_roster(
    product: str, existing: tuple[str, ...]
) -> dict[str, str]:
    version = _current_product_contract_version()
    roster_note = (
        f"enumerated from the registry - {len(existing)} product(s) registered today, "
        f"{product} would make {len(existing) + 1} (§101 invariants 52-53)"
    )
    return {
        "repo_from_template": f"{product}: create the repository from the {TEMPLATE_REPO} template (§19.1 step 1)",
        "product_yaml": f"{product}: write product.yaml at contract_version={version}",
        "team": f"{product}: create the GitHub Team {product!r}, membership derived from assignments (§11.2)",
        "codeowners": f"{product}: generate CODEOWNERS from {product}'s assignments",
        "branch_protection": f"{product}: apply branch protection from the template (§11.3)",
        "environments": f"{product}: create environments development, staging, production",
        "ci_workflows_pinned_tag": (
            f"{product}: wire CI workflows that consume the reusable workflows by pinned tag"
        ),
        "verification_skeleton": f"{product}: scaffold the verification/ skeleton",
        "local_environment_contract": (
            f"{product}: establish the local environment contract - the eight commands "
            f"({', '.join(REQUIRED_COMMANDS)})"
        ),
        "required_endpoints": f"{product}: expose the health, version and metrics endpoints",
        "register_portfolio_board": f"{product}: register on the portfolio board, {roster_note}",
        "register_grafana_scorecard_devlake": (
            f"{product}: register with Grafana, Scorecard and DevLake, {roster_note}"
        ),
        "register_dependency_graph": f"{product}: register in the dependency graph, {roster_note}",
    }


def _automated_step_descriptions(product: str, fixture: str) -> dict[str, str]:
    existing = registered_product_ids(fixture)
    return _automated_step_descriptions_from_roster(product, existing)


def _manual_step_descriptions(product: str) -> dict[str, str]:
    return {
        "alert_channel": (
            f"{product}: create the alerting channel for {product} - no provider automation "
            "exists for this, tracked here as a manual step so it is never silently missing "
            "(§19.1)"
        ),
        "support_intake_mailbox": (
            f"{product}: create the support-intake mailbox for {product} - no provider "
            "automation exists for this, tracked here as a manual step so it is never "
            "silently missing (§19.1)"
        ),
    }


def build_create_product_plan(product: str, fixture: str) -> CreateProductPlan:
    """Build the create-product plan for `product` (spec §19.1), in order.

    `fixture` names the registry to read the current product roster
    from (steps 11-13) - the same fixture-name convention
    `tools/provision/teams.py` and `tools/provision/environments.py`
    already use. Every automated step is `StepKind.WRITE`; the two
    manual steps are `StepKind.MANUAL`, carried separately in
    `.manual_steps` (see `CreateProductPlan`).
    """
    automated = _automated_step_descriptions(product, fixture)
    steps = [Step(step_id, automated[step_id], StepKind.WRITE) for step_id in CREATE_PRODUCT_STEPS]

    manual_text = _manual_step_descriptions(product)
    manual_steps = tuple(
        Step(step_id, manual_text[step_id], StepKind.MANUAL) for step_id in CREATE_PRODUCT_MANUAL_STEPS
    )

    return CreateProductPlan(steps=steps, manual_steps=manual_steps)




def declared_registered_product_ids(declared_dir: Path | None = None) -> tuple[str, ...]:
    """The product roster read from declared/products/*.yaml, sorted."""
    if declared_dir is None:
        declared_dir = Path(__file__).resolve().parent.parent.parent / "declared"
    products_dir = declared_dir / "products" if declared_dir.name != "products" else declared_dir
    if not products_dir.is_dir():
        return ()
    return tuple(sorted(p.stem for p in products_dir.glob("*.yaml") if not p.name.startswith(".")))


def build_create_product_plan_against_declared(
    product: str, declared_dir: Path | None = None
) -> CreateProductPlan:
    """Build the create-product plan for `product` using the permanent declared/ directory."""
    existing = declared_registered_product_ids(declared_dir)
    automated = _automated_step_descriptions_from_roster(product, existing)
    steps = [Step(step_id, automated[step_id], StepKind.WRITE) for step_id in CREATE_PRODUCT_STEPS]

    manual_text = _manual_step_descriptions(product)
    manual_steps = tuple(
        Step(step_id, manual_text[step_id], StepKind.MANUAL) for step_id in CREATE_PRODUCT_MANUAL_STEPS
    )

    return CreateProductPlan(steps=steps, manual_steps=manual_steps)


def build_create_product_plan_against_live_roster(
    product: str, onboarding_root: Path | None = None
) -> CreateProductPlan:
    """Build the create-product plan for `product` using the live product roster.

    Reads current registered product IDs from `docs/onboarding/products/<slot>/facts.tsv`
    (excluding slot 06 per CCR-002 and FD-138) rather than a fixture.
    Produces a dry-run plan only.
    """
    from tools.provision.live_roster import live_registered_product_ids

    existing = live_registered_product_ids(onboarding_root=onboarding_root)
    automated = _automated_step_descriptions_from_roster(product, existing)
    steps = [Step(step_id, automated[step_id], StepKind.WRITE) for step_id in CREATE_PRODUCT_STEPS]

    manual_text = _manual_step_descriptions(product)
    manual_steps = tuple(
        Step(step_id, manual_text[step_id], StepKind.MANUAL) for step_id in CREATE_PRODUCT_MANUAL_STEPS
    )

    return CreateProductPlan(steps=steps, manual_steps=manual_steps)
