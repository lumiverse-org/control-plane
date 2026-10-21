"""Tests for the `recovery` block added to
schemas/product/product.contract.v2.schema.json, plus R-PRD-07,
R-PRD-18, and R-PRD-19 (L1-307, Section 15.1; Section 15.4; Section 15.5;
Section 44.1; Section 44.3; invariant 3; invariant 4; SIG-17).
"""
import datetime
import json
import os

import jsonschema
import yaml
from referencing import Registry, Resource

from validators.registry.rules import r_prd_07

SCHEMAS_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "schemas")
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "product", "recovery")
TODAY = datetime.date(2026, 8, 27)


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
    return r_prd_07.check(_load_fixture(case), TODAY)


def test_valid_fresh_high():
    case = os.path.join("valid", "fresh_high")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


def test_valid_fresh_critical():
    case = os.path.join("valid", "fresh_critical")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


def test_valid_static_site_null_recovery():
    case = os.path.join("valid", "static_site_null_recovery")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


def test_valid_high_exactly_90():
    case = os.path.join("valid", "high_exactly_90")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


def test_valid_critical_exactly_30():
    case = os.path.join("valid", "critical_exactly_30")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


def test_high_91_days_triggers_r_prd_07():
    case = "high_91_days"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-07" in findings[0]
    assert "91 days old" in findings[0]
    assert "is 90 days" in findings[0]


def test_high_exactly_91_triggers_r_prd_07():
    case = "high_exactly_91"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-07" in findings[0]
    assert "91 days old" in findings[0]
    assert "is 90 days" in findings[0]


def test_critical_31_days_triggers_r_prd_07():
    case = "critical_31_days"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-07" in findings[0]
    assert "31 days old" in findings[0]
    assert "is 30 days" in findings[0]


def test_critical_exactly_31_triggers_r_prd_07():
    case = "critical_exactly_31"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-07" in findings[0]
    assert "31 days old" in findings[0]
    assert "is 30 days" in findings[0]


def test_unencrypted_triggers_r_prd_18():
    case = "unencrypted"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-18" in findings[0]
    assert "unencrypted backups" in findings[0]


def test_missing_integrity_check_fails_schema():
    case = "missing_integrity_check"
    assert len(_errors_for(case)) > 0


def test_missing_restore_environment_fails_schema():
    case = "missing_restore_environment"
    assert len(_errors_for(case)) > 0


def test_missing_storage_location_fails_schema():
    case = "missing_storage_location"
    assert len(_errors_for(case)) > 0


def test_restore_tested_not_date_fails_schema():
    case = "restore_tested_not_date"
    assert len(_errors_for(case)) > 0


def test_retention_zero_fails_schema():
    case = "retention_zero"
    assert len(_errors_for(case)) > 0


def test_recovery_extra_field_fails_schema():
    case = "recovery_extra_field"
    assert len(_errors_for(case)) > 0
