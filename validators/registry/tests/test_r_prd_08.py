"""Tests for R-PRD-08, R-PRD-20..R-PRD-26 (L1-308, Section 15.7; AT-009).

Adapted to validate fixtures directly with `jsonschema` for the schema
half and to call `validators.registry.rules.r_prd_08.check` directly for
the rule half, rather than through `validators/registry/cli.py` --
FD-094 (DECIDED) supersedes the CLI-based `echo "AT009_EXIT=$?"`/
`echo "MISDECLARE_EXIT=$?"` acceptance grammar in favour of Option B,
the same adaptation `test_r_prd_05.py` and `test_r_prd_11.py` already
document.

Fixture layout follows `test_r_prd_05.py`'s convention: valid cases live
under `valid/<case>/`, invalid cases are flat directly under
`FIXTURES_DIR/<case>/` (no `invalid/` prefix).

19 test functions: 7 valid, 10 invalid (passing), 2 invalid (xfail),
matching the task's own fixture-case table and xfail count
(lanes/L1-05-tasks.md:1873, 1891, 6018) exactly.
"""
import json
import os

import jsonschema
import pytest
import yaml
from referencing import Registry, Resource

from validators.registry.rules import r_prd_08

SCHEMAS_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "schemas")
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "product", "conformance")


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
    return r_prd_08.check(_load_fixture(case))


# ---------------------------------------------------------------------------
# valid (7)
# ---------------------------------------------------------------------------


def test_valid_service():
    case = os.path.join("valid", "service")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


def test_valid_client_app():
    case = os.path.join("valid", "client_app")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


def test_valid_library():
    case = os.path.join("valid", "library")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


def test_valid_batch():
    case = os.path.join("valid", "batch")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


def test_valid_customer_hosted():
    case = os.path.join("valid", "customer_hosted")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


def test_valid_white_label():
    case = os.path.join("valid", "white_label")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


def test_valid_static_site():
    case = os.path.join("valid", "static_site")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


# ---------------------------------------------------------------------------
# invalid, passing (10)
# ---------------------------------------------------------------------------


def test_service_missing_recovery_triggers_r_prd_08():
    case = "service_missing_recovery"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-08" in findings[0]
    assert "recovery" in findings[0]


def test_service_null_health_triggers_r_prd_08():
    case = "service_null_health"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-08" in findings[0]
    assert "health_endpoint" in findings[0]


def test_client_app_progressive_delivery_not_staged_rollout_triggers_r_prd_20():
    case = "client_app_progressive_delivery_not_staged_rollout"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-20" in findings[0]
    assert "progressive_delivery" in findings[0]


def test_client_app_no_staged_rollout_triggers_r_prd_20():
    case = "client_app_no_staged_rollout"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-20" in findings[0]
    assert "staged_rollout is null" in findings[0]


def test_client_app_null_rollback_method_triggers_r_prd_20():
    case = "client_app_null_rollback_method"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-20" in findings[0]
    assert "rollback_method" in findings[0]


def test_batch_missing_metrics_triggers_r_prd_22():
    case = "batch_missing_metrics"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-22" in findings[0]
    assert "metrics" in findings[0]


def test_white_label_missing_production_triggers_r_prd_24():
    case = "white_label_missing_production"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-24" in findings[0]
    assert "production" in findings[0]


def test_static_site_staged_rollout_not_monotonic_triggers_r_prd_26():
    case = "static_site_staged_rollout_not_monotonic"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-26" in findings[0]
    assert "not strictly increasing" in findings[0]


def test_stages_not_increasing_triggers_r_prd_26():
    case = "stages_not_increasing"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-26" in findings[0]
    assert "not strictly increasing" in findings[0]


def test_stages_not_ending_100_triggers_r_prd_26():
    case = "stages_not_ending_100"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-26" in findings[0]
    assert "does not end at 100" in findings[0]


# ---------------------------------------------------------------------------
# invalid, xfail (2)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "BLOCKER L1 L1-308: the library conformance profile needs "
        "consumer_contract_tests evidence that product.yaml has no field "
        "for. Section 15.7 requires 'Registry version plus consumer "
        "contract tests' for library; product.yaml has no field to carry "
        "that evidence (Section 20.1's service.yaml has "
        "verification.consumer_contract_tests, product.yaml does not), so "
        "R-PRD-21 cannot check it yet. Not resolved here -- pending an L0 "
        "decision between (a) adding the field to the v2 product schema "
        "(Section 60.2) or (b) requiring a library product to also carry "
        "a service.yaml."
    ),
)
def test_library_missing_consumer_contract_tests_triggers_r_prd_21():
    case = "library_missing_consumer_contract_tests"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-21" in findings[0]
    assert "consumer_contract_tests" in findings[0] or "consumer contract" in findings[0]


@pytest.mark.xfail(
    strict=True,
    reason=(
        "BLOCKER L1 L1-308: customer-hosted recovery exemption requires "
        "cross-file resolution into exceptions.yaml. Section 15.7 permits "
        "customer-hosted to satisfy recovery with 'a recorded exemption "
        "with a compensating control', which is an exceptions.yaml entry "
        "(Section 54.1) in a different repository path. R-PRD-23 as "
        "shipped requires recovery non-null unconditionally and does not "
        "consult exceptions.yaml. Not resolved here -- pending an L0 "
        "decision on how Lane 1 is meant to read exceptions.yaml."
    ),
)
def test_customer_hosted_recovery_exempted_is_not_flagged():
    case = "customer_hosted_recovery_exempted"
    assert _errors_for(case) == []
    assert _findings_for(case) == []
