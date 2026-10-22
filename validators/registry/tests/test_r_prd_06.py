"""Tests for the `commitments` block added to
schemas/product/product.contract.v2.schema.json, plus R-PRD-06,
R-PRD-16, and R-PRD-17 (L1-306, Section 21.1; Section 21.4; Section 15.5;
invariant 111).
"""
import json
import os

import jsonschema
import yaml
from referencing import Registry, Resource

from validators.registry.rules import r_prd_06

SCHEMAS_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "schemas")
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "product", "commitments")


def _registry():
    defs_path = os.path.join(SCHEMAS_ROOT, "registry", "common", "defs.v1.schema.json")
    assignments_path = os.path.join(SCHEMAS_ROOT, "registry", "common", "assignments.v1.schema.json")
    product_path = os.path.join(SCHEMAS_ROOT, "product", "product.contract.v2.schema.json")
    with open(defs_path, encoding="utf-8") as f:
        defs_schema = json.load(f)
    with open(assignments_path, encoding="utf-8") as f:
        assignments_schema = json.load(f)
    with open(product_path, encoding="utf-8") as f:
        product_schema = json.load(f)
    reg = Registry().with_resources(
        [
            ("common/defs.v1.schema.json", Resource.from_contents(defs_schema)),
            (assignments_schema["$id"], Resource.from_contents(assignments_schema)),
            (product_schema["$id"], Resource.from_contents(product_schema)),
        ]
    )
    return product_schema, reg


def _load_fixture(case):
    path = os.path.join(FIXTURES_DIR, case, "product.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _errors_for(case):
    schema, reg = _registry()
    validator = jsonschema.Draft202012Validator(schema, registry=reg)
    doc = _load_fixture(case)
    return list(validator.iter_errors(doc))


def _findings_for(case):
    return r_prd_06.check(_load_fixture(case))


def test_valid_empty_commitments():
    case = os.path.join("valid", "empty_commitments")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


def test_valid_passed():
    case = os.path.join("valid", "passed")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


def test_valid_waived():
    case = os.path.join("valid", "waived")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


def test_conflict_check_absent_triggers_r_prd_06():
    case = "conflict_check_absent"
    assert len(_errors_for(case)) > 0
    findings = r_prd_06.check_r_prd_06(_load_fixture(case))
    assert len(findings) == 1
    assert "R-PRD-06" in findings[0]
    assert "records neither passed nor waived-with-decision; Section 15.5" in findings[0]


def test_conflict_check_bad_token_triggers_r_prd_06():
    case = "conflict_check_bad_token"
    assert len(_errors_for(case)) > 0
    findings = r_prd_06.check_r_prd_06(_load_fixture(case))
    assert len(findings) == 1
    assert "R-PRD-06" in findings[0]
    assert "records neither passed nor waived-with-decision; Section 15.5" in findings[0]


def test_customer_legal_name_fails_schema():
    case = "customer_legal_name"
    assert len(_errors_for(case)) > 0


def test_promise_24x7_on_business_hours_triggers_r_prd_16():
    case = "promise_24x7_on_business_hours"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-16" in findings[0]
    assert "promises '24x7'" in findings[0]
    assert "operates 'business-hours'" in findings[0]


def test_residency_conflict_triggers_r_prd_17():
    case = "residency_conflict"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-17" in findings[0]
    assert "Section 21.4" in findings[0]


def test_contract_end_not_date_fails_schema():
    case = "contract_end_not_date"
    assert len(_errors_for(case)) > 0


def test_service_credit_bad_enum_fails_schema():
    case = "service_credit_bad_enum"
    assert len(_errors_for(case)) > 0


def test_commitment_extra_field_fails_schema():
    case = "commitment_extra_field"
    assert len(_errors_for(case)) > 0
