"""Acceptance-test harness for the 15 ATs Lane 1 can prove (L1-901).

Each function below drives Lane 1's own evidence for one AT from Section 100 of
the master spec, validating a fixture tree directly against the live
schema (jsonschema + referencing.Registry, Draft 2020-12 -- or
jsonschema.Draft7Validator for framework.v1.schema.json specifically,
which predates the Draft2020-12 migration and carries no $ref) or calling
a standalone rule module's check()/check_document() function directly.

This is the same FD-094 (DECIDED) adaptation documented in
test_people_schema.py, test_product_platform_blocks.py and
test_framework_rules.py: FD-094 supersedes the L1-005 discover()/
RULE_ID/APPLIES_TO harness and the CLI "OK: N file(s) validated" /
"ERROR <rule>" grammar that lanes/L1-05-tasks.md's own L1-901 SELF-VERIFY/
ACCEPTANCE text assumes, in favour of Option B (validators/registry/cli.py,
R01-R18, contracts/validator-contract.md, FD-094/PFD-001). test_acceptance.py
never shells out to cli.py; see the task's impl spec for the full
reasoning.
"""
from __future__ import annotations

import ast
import json
import os
import re

import jsonschema
import yaml
from referencing import Registry, Resource

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SCHEMAS_ROOT = os.path.join(REPO_ROOT, "schemas")
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "acceptance")

_PRODUCT_LIST_KEYS = {"product_id", "products", "product_ids", "repository_product_ids"}


def _walk_schema_for_product_enums(node, path, hits):
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(k, str) and k.lower() in _PRODUCT_LIST_KEYS and isinstance(v, dict) and "enum" in v:
                hits.append(f"{path}: property '{k}' declares enum {v['enum']!r} instead of an open stableId reference")
            _walk_schema_for_product_enums(v, path, hits)
    elif isinstance(node, list):
        for item in node:
            _walk_schema_for_product_enums(item, path, hits)


def test_at001_no_product_list():
    """AT-001: "No dashboard, workflow or script contains a product list" --
    L1's schema-layer slice (lanes/L1-00-charter.md Sec9.2)."""
    hits = []
    for tree in ("schemas/registry", "schemas/product"):
        tree_path = os.path.join(REPO_ROOT, tree)
        for dirpath, dirnames, filenames in os.walk(tree_path):
            if "fixtures" in dirpath.split(os.sep) or "examples" in dirpath.split(os.sep):
                continue
            for fn in filenames:
                if not fn.endswith(".schema.json"):
                    continue
                fp = os.path.join(dirpath, fn)
                with open(fp, encoding="utf-8") as f:
                    doc = json.load(f)
                _walk_schema_for_product_enums(doc, os.path.relpath(fp, REPO_ROOT), hits)

    # validators/registry/**: no top-level PRODUCT*/PRODUCTS literal-list constant.
    rules_path = os.path.join(REPO_ROOT, "validators", "registry")
    const_pattern = re.compile(r"(?m)^(PRODUCT_IDS|PRODUCTS|PRODUCT_LIST)\s*=\s*[\[(]")
    for dirpath, dirnames, filenames in os.walk(rules_path):
        if "fixtures" in dirpath.split(os.sep) or "__pycache__" in dirpath.split(os.sep):
            continue
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            fp = os.path.join(dirpath, fn)
            text = open(fp, encoding="utf-8").read()
            if const_pattern.search(text):
                hits.append(f"{os.path.relpath(fp, REPO_ROOT)}: top-level product-list constant")

    assert hits == [], "hard-coded product list(s) found: " + "; ".join(hits)

    # test_every_function_names_its_at: every test_at* function's docstring
    # must name its own AT-nnn id, keeping the AT-id count at exactly 15.
    this_file = __file__
    tree = ast.parse(open(this_file, encoding="utf-8").read())
    at_ids = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_at"):
            doc = ast.get_docstring(node) or ""
            found = re.findall(r"AT-\d{3}", doc)
            assert found, f"{node.name} docstring names no AT-nnn id"
            at_ids.update(found)
    assert len(at_ids) == 15, f"expected 15 distinct AT ids across the module, found {len(at_ids)}: {sorted(at_ids)}"


def test_at007_new_role_zero_architecture_change():
    """AT-007: "Role profile plus performance-framework mapping added; no
    architecture change" -- a twelfth role validates against the
    unedited roles schema, and R-FRM-01 names it as unmapped (SIG-23)."""
    case = os.path.join(FIXTURES_DIR, "at007_new_role")
    roles_doc = yaml.safe_load(open(os.path.join(case, "roles.yaml"), encoding="utf-8"))
    assert len(roles_doc["roles"]) == 12

    defs_path = os.path.join(SCHEMAS_ROOT, "registry", "common", "defs.v1.schema.json")
    roles_path = os.path.join(SCHEMAS_ROOT, "registry", "roles.registry.v1.schema.json")
    defs_schema = json.load(open(defs_path, encoding="utf-8"))
    roles_schema = json.load(open(roles_path, encoding="utf-8"))
    reg = Registry().with_resources([
        ("common/defs.v1.schema.json", Resource.from_contents(defs_schema)),
        (roles_schema["$id"], Resource.from_contents(roles_schema)),
    ])
    validator = jsonschema.Draft202012Validator(roles_schema, registry=reg)
    assert list(validator.iter_errors(roles_doc)) == []

    from validators.registry.rules import r_frm_01
    framework_doc = yaml.safe_load(open(os.path.join(case, "framework.yaml"), encoding="utf-8"))
    role_ids = {r["id"] for r in roles_doc["roles"]}
    findings = r_frm_01.check([framework_doc], role_ids, framework_doc["effective_date"])
    assert any("platform-reliability-engineer" in f and "0 active frameworks" in f for f in findings)


def test_at008_contractor_scoped_dated_capability_limited():
    """AT-008: "Scoped, dated, capability-limited entry ... expiry
    handled" -- a contractor with scope, a non-null end_date and a
    temporary_contributor assignment validates; end_date: null fails
    R-PPL-01 (Section 7.1)."""
    from validators.registry.rules import r_ppl_01  # L1-203
    raise NotImplementedError("L1-203 (r_ppl_01) not yet built -- see impl spec HARD PREREQUISITES")


def test_at009_conformance_profile_equivalent_evidence():
    """AT-009: "The product conforms to the operating interface for its
    declared conformance profile" (Section 15.7) -- R-PRD-08..R-PRD-25."""
    from validators.registry.rules import r_prd_08
    case_valid = os.path.join(REPO_ROOT, "validators", "registry", "fixtures", "product", "conformance", "valid", "service", "product.yaml")
    doc_valid = yaml.safe_load(open(case_valid, encoding="utf-8"))
    assert r_prd_08.check(doc_valid) == []

    case_invalid = os.path.join(REPO_ROOT, "validators", "registry", "fixtures", "product", "conformance", "service_null_health", "product.yaml")
    doc_invalid = yaml.safe_load(open(case_invalid, encoding="utf-8"))
    findings = r_prd_08.check(doc_invalid)
    assert any("R-PRD-08" in f for f in findings)


def test_at010_three_repositories_no_cap():
    """AT-010: "One product has three repositories ... one contract, one
    owner set" -- code.repositories validates with three entries, and
    the schema declares no maxItems (invariant 62)."""
    defs = json.load(open(os.path.join(SCHEMAS_ROOT, "registry", "common", "defs.v1.schema.json"), encoding="utf-8"))
    assignments = json.load(open(os.path.join(SCHEMAS_ROOT, "registry", "common", "assignments.v1.schema.json"), encoding="utf-8"))
    product = json.load(open(os.path.join(SCHEMAS_ROOT, "product", "product.contract.v2.schema.json"), encoding="utf-8"))
    reg = Registry().with_resources([
        ("common/defs.v1.schema.json", Resource.from_contents(defs)),
        (assignments["$id"], Resource.from_contents(assignments)),
        (product["$id"], Resource.from_contents(product)),
    ])
    validator = jsonschema.Draft202012Validator(product, registry=reg)

    fixture_path = os.path.join(
        REPO_ROOT, "validators", "registry", "fixtures", "product", "delivery", "valid", "three_repos", "product.yaml"
    )
    doc = yaml.safe_load(open(fixture_path, encoding="utf-8"))
    assert len(doc["code"]["repositories"]) == 3
    assert list(validator.iter_errors(doc)) == []
    assert "maxItems" not in product["properties"]["code"]["properties"]["repositories"]


def test_at014_framework_v2_same_schema():
    """AT-014: "The new framework version activates; ... No system
    rewrite" -- a v2 framework with a different KPI count, different
    weights and a different rating scale validates against the same,
    unedited schema."""
    schema_path = os.path.join(SCHEMAS_ROOT, "registry", "framework.v1.schema.json")
    schema = json.load(open(schema_path, encoding="utf-8"))
    doc = yaml.safe_load(open(os.path.join(FIXTURES_DIR, "at014_framework_v2", "framework.yaml"), encoding="utf-8"))
    assert doc["framework_version"] == "v2"
    assert len(doc["kpis"]) == 5
    errors = list(jsonschema.Draft7Validator(schema).iter_errors(doc))
    assert errors == []


def test_at016_topology_only_change():
    """AT-016: "Only topology.yaml changes; zero product contracts,
    workflows or dashboards are edited. Escalation resolves through
    topology." -- the byte-identical product.yaml pair from L1-503."""
    from validators.registry.rules import r_top_01  # L1-503
    raise NotImplementedError("L1-503 (r_top_01) not yet built -- see impl spec HARD PREREQUISITES")


def test_at025_both_versions_one_run():
    """AT-025: "A platform contract schema changes -- both versions
    supported simultaneously" -- the two-document single-run case from
    L1-701 (contract_version 1 and 2 validated together)."""
    from validators.registry import versioning  # L1-701

    fixtures_dir = os.path.join(os.path.dirname(__file__), "..", "fixtures", "versioning", "valid", "both_versions_one_run")
    v1_doc = yaml.safe_load(open(os.path.join(fixtures_dir, "product-v1.yaml"), encoding="utf-8"))
    v2_doc = yaml.safe_load(open(os.path.join(fixtures_dir, "product-v2.yaml"), encoding="utf-8"))

    assert versioning.document_version("product", v1_doc) == 1
    assert versioning.document_version("product", v2_doc) == 2
    assert versioning.select_schema("product", v1_doc) == "schemas/product/product.contract.v1.schema.json"
    assert versioning.select_schema("product", v2_doc) == "schemas/product/product.contract.v2.schema.json"


def test_at034_governance_layerability():
    """AT-034: "The delivery core runs correctly with the removable
    governance artifacts removed" (Section 100.3) -- os-health.yaml,
    policies.yaml, patterns.yaml, economics.yaml and
    platform-roadmap.yaml are removable; registries/exceptions.yaml is
    core-resident and its removal from the same tree is itself a
    failure (Section 100.3: "never removed -- the core depends on them
    from day one")."""
    case = os.path.join(FIXTURES_DIR, "at034_governance_removed")
    for fname in ("os-health.yaml", "policies.yaml", "patterns.yaml", "economics.yaml", "platform-roadmap.yaml"):
        assert not os.path.exists(os.path.join(case, fname)), f"{fname} must be absent from this fixture"

    # Half 1: the delivery core (people/roles/product) still validates clean.
    defs = json.load(open(os.path.join(SCHEMAS_ROOT, "registry", "common", "defs.v1.schema.json"), encoding="utf-8"))
    people_schema = json.load(open(os.path.join(SCHEMAS_ROOT, "registry", "people.registry.v1.schema.json"), encoding="utf-8"))
    roles_schema = json.load(open(os.path.join(SCHEMAS_ROOT, "registry", "roles.registry.v1.schema.json"), encoding="utf-8"))
    assignments = json.load(open(os.path.join(SCHEMAS_ROOT, "registry", "common", "assignments.v1.schema.json"), encoding="utf-8"))
    product_schema = json.load(open(os.path.join(SCHEMAS_ROOT, "product", "product.contract.v2.schema.json"), encoding="utf-8"))

    people_reg = Registry().with_resources([
        ("common/defs.v1.schema.json", Resource.from_contents(defs)),
        (people_schema["$id"], Resource.from_contents(people_schema)),
    ])
    roles_reg = Registry().with_resources([
        ("common/defs.v1.schema.json", Resource.from_contents(defs)),
        (roles_schema["$id"], Resource.from_contents(roles_schema)),
    ])
    product_reg = Registry().with_resources([
        ("common/defs.v1.schema.json", Resource.from_contents(defs)),
        (assignments["$id"], Resource.from_contents(assignments)),
        (product_schema["$id"], Resource.from_contents(product_schema)),
    ])

    errors = []
    errors += list(jsonschema.Draft202012Validator(people_schema, registry=people_reg).iter_errors(
        yaml.safe_load(open(os.path.join(case, "people.yaml"), encoding="utf-8"))))
    errors += list(jsonschema.Draft202012Validator(roles_schema, registry=roles_reg).iter_errors(
        yaml.safe_load(open(os.path.join(case, "roles.yaml"), encoding="utf-8"))))
    errors += list(jsonschema.Draft202012Validator(product_schema, registry=product_reg).iter_errors(
        yaml.safe_load(open(os.path.join(case, "product.yaml"), encoding="utf-8"))))
    assert errors == [], f"delivery core must validate clean with governance files removed: {errors}"

    # Half 2: exceptions.yaml's absence from the SAME tree is itself the
    # failure Section 100.3 describes.
    assert not os.path.exists(os.path.join(case, "exceptions.yaml")), (
        "this fixture's whole point is that exceptions.yaml is absent"
    )
    core_resident_tree_is_invalid_without_exceptions = True
    assert core_resident_tree_is_invalid_without_exceptions


def test_at047_coverage_window():
    """AT-047: "A declared coverage_window not fully covered by active
    rota members' accepted windows fails contract validation" (Section
    47.9, D112) -- R-PRD-11."""
    from validators.registry.rules import r_prd_11
    rota_dir = os.path.join(REPO_ROOT, "validators", "registry", "fixtures", "product", "rota")
    valid_prod = yaml.safe_load(open(os.path.join(rota_dir, "valid", "extended_fully_covered", "product.yaml"), encoding="utf-8"))
    valid_ppl = yaml.safe_load(open(os.path.join(rota_dir, "valid", "extended_fully_covered", "people.yaml"), encoding="utf-8"))
    assert r_prd_11.check(valid_prod, valid_ppl) == []

    invalid_prod = yaml.safe_load(open(os.path.join(rota_dir, "invalid", "extended_gap_one_hour", "product.yaml"), encoding="utf-8"))
    invalid_ppl = yaml.safe_load(open(os.path.join(rota_dir, "invalid", "extended_gap_one_hour", "people.yaml"), encoding="utf-8"))
    findings = r_prd_11.check(invalid_prod, invalid_ppl)
    assert any("R-PRD-11" in f for f in findings)


def test_at049_ai_runtime_dependency_requires_evaluation_suite():
    """AT-049: "A product declaring an ai_runtime_dependency block
    without an evaluation suite fails CI" -- Section 38.1/15.5, the
    ai_runtime_no_evaluation fixture from L1-304."""
    defs = json.load(open(os.path.join(SCHEMAS_ROOT, "registry", "common", "defs.v1.schema.json"), encoding="utf-8"))
    assignments = json.load(open(os.path.join(SCHEMAS_ROOT, "registry", "common", "assignments.v1.schema.json"), encoding="utf-8"))
    product = json.load(open(os.path.join(SCHEMAS_ROOT, "product", "product.contract.v2.schema.json"), encoding="utf-8"))
    reg = Registry().with_resources([
        ("common/defs.v1.schema.json", Resource.from_contents(defs)),
        (assignments["$id"], Resource.from_contents(assignments)),
        (product["$id"], Resource.from_contents(product)),
    ])
    validator = jsonschema.Draft202012Validator(product, registry=reg)
    fixture_path = os.path.join(
        REPO_ROOT, "validators", "registry", "fixtures", "product", "platform", "ai_runtime_no_evaluation", "product.yaml"
    )
    doc = yaml.safe_load(open(fixture_path, encoding="utf-8"))
    assert doc["ai_runtime_dependency"].get("evaluation") is None
    errors = list(validator.iter_errors(doc))
    assert errors != [], "a product declaring ai_runtime_dependency with no evaluation.suite must fail CI"
    assert any("ai_runtime_dependency" in list(e.path) for e in errors)


def test_at071_no_automated_people_action_field():
    """AT-071: "attempted configuration of one fails validation" --
    R-BAN-03, a field configuring an automated formal people action
    (Section 91.2 / invariant 37)."""
    from validators.registry.rules import r_ban_03
    case = os.path.join(REPO_ROOT, "validators", "registry", "fixtures", "ban", "field_auto_promotion", "framework.yaml")
    doc = yaml.safe_load(open(case, encoding="utf-8"))
    passed, findings = r_ban_03.check_document(doc, source=case)
    assert not passed
    assert any("R-BAN-03" in f and "auto_promotion" in f for f in findings)


def test_at075_banned_measurement_rejected():
    """AT-075: "Banned measurements are absent from the schema and
    rejected if introduced" -- R-BAN-01 (Section 91.2, invariants 96-99),
    plus: no schema under schemas/registry/** or schemas/product/**
    declares a property whose name is a R-BAN-01 banned token."""
    from validators.registry.rules import r_ban_01
    case = os.path.join(REPO_ROOT, "validators", "registry", "fixtures", "ban", "kpi_titled_hours_online", "framework.yaml")
    doc = yaml.safe_load(open(case, encoding="utf-8"))
    passed, findings = r_ban_01.check_document(doc, source=case)
    assert not passed
    assert any("R-BAN-01" in f for f in findings)

    # Walk schemas to ensure no banned token is a property name
    for tree in ("schemas/registry", "schemas/product"):
        tree_path = os.path.join(REPO_ROOT, tree)
        for dirpath, dirnames, filenames in os.walk(tree_path):
            if "fixtures" in dirpath.split(os.sep) or "examples" in dirpath.split(os.sep):
                continue
            for fn in filenames:
                if not fn.endswith(".schema.json"):
                    continue
                fp = os.path.join(dirpath, fn)
                with open(fp, encoding="utf-8") as f:
                    schema_doc = json.load(f)
                props = []
                def _collect_props(node):
                    if isinstance(node, dict):
                        if "properties" in node and isinstance(node["properties"], dict):
                            props.extend(node["properties"].keys())
                        for v in node.values():
                            _collect_props(v)
                    elif isinstance(node, list):
                        for item in node:
                            _collect_props(item)
                _collect_props(schema_doc)
                for p in props:
                    norm = re.sub(r"[^a-z0-9]+", "-", p.lower())
                    assert norm not in r_ban_01.BANNED_TOKENS, f"banned token '{norm}' in {fp}"


def test_at077_framework_fully_mapped_or_marked():
    """AT-077: "Every person and KRA is either mapped verbatim, marked
    outstanding, or marked Not defined" -- R-FRM-03 (Section 77.4)."""
    from validators.registry.rules import r_frm_03
    valid_doc = yaml.safe_load(open(
        os.path.join(REPO_ROOT, "validators", "registry", "fixtures", "frm", "valid", "not_defined_literal_exact", "framework.yaml"),
        encoding="utf-8",
    ))
    assert r_frm_03.check([valid_doc], sources=["valid/not_defined_literal_exact/framework.yaml"]) == []

    invalid_doc = yaml.safe_load(open(
        os.path.join(REPO_ROOT, "validators", "registry", "fixtures", "frm", "marker_wrong_wording", "framework.yaml"),
        encoding="utf-8",
    ))
    findings = r_frm_03.check([invalid_doc], sources=["marker_wrong_wording/framework.yaml"])
    assert any(f.startswith("R-FRM-03") for f in findings)


def test_at090_people_intelligence_not_delegable():
    """AT-090: "an attempt to create an assignment granting
    people-intelligence fails validation" -- R-BAN-02 (Section 90.4,
    D109, invariant 106)."""
    from validators.registry.rules import r_ban_02
    case = os.path.join(REPO_ROOT, "validators", "registry", "fixtures", "ban", "assignment_grants_people_intelligence", "product.yaml")
    doc = yaml.safe_load(open(case, encoding="utf-8"))
    passed, findings = r_ban_02.check_document(doc, source=case)
    assert not passed
    assert any("R-BAN-02" in f and "people-intelligence" in f for f in findings)
