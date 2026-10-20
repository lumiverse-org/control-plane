"""Tests for the `operations` block added to
schemas/product/product.contract.v2.schema.json, plus R-PRD-05,
R-PRD-13, R-PRD-14 and R-PRD-15 (L1-305, Section 15.1; Section 42.2;
Section 47.9; Section 22; Section 15.5).

Adapted to validate fixtures directly with `jsonschema` for the schema
half and to call `validators.registry.rules.r_prd_05.check` directly for
the rule half, rather than through `validators/registry/cli.py` --
FD-094 (DECIDED) supersedes the L1-005 harness and the CLI-based
`echo "EXIT=$?"` acceptance grammar in favour of Option B, the same
adaptation `test_product_platform_blocks.py`, `test_product_delivery_blocks.py`
and `test_r_prd_11.py` already document.

Each fixture case is a *complete*, otherwise-minimal `product.yaml` --
every top-level block required since L1-304 is present -- so a single
`_errors_for`/`_findings_for` pair per case covers both the schema
constraint and the semantic rule at once, matching how a real document
would actually fail.

Fixture layout follows `test_product_platform_blocks.py`'s convention:
valid cases live under `valid/<case>/`, invalid cases are flat directly
under `FIXTURES_DIR/<case>/` (no `invalid/` prefix) -- this also matches
the literal fixture path named in the task's own CORRECT OUTPUT block,
`validators/registry/fixtures/product/operations/mismatch_24x7_next_morning/product.yaml`.

12 test functions: 3 valid, 9 invalid, matching the task's own
fixture-case table exactly.
"""
import json
import os

import jsonschema
import yaml
from referencing import Registry, Resource

from validators.registry.rules import r_prd_05

SCHEMAS_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "schemas")
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "product", "operations")


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
    return r_prd_05.check(_load_fixture(case))


# ---------------------------------------------------------------------------
# valid (3) -- schema-valid AND no rule findings
# ---------------------------------------------------------------------------


def test_valid_business_hours():
    case = os.path.join("valid", "business_hours")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


def test_valid_extended_with_window():
    case = os.path.join("valid", "extended_with_window")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


def test_valid_24x7_with_window():
    """Also exercises R-PRD-15's positive path: primary_responder and
    backup_responder both match an incident_responder assignment."""
    case = os.path.join("valid", "24x7_with_window")
    assert _errors_for(case) == []
    assert _findings_for(case) == []


# ---------------------------------------------------------------------------
# invalid (9)
# ---------------------------------------------------------------------------


def test_mismatch_business_continuous_triggers_r_prd_05():
    case = "mismatch_business_continuous"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-05" in findings[0]
    assert "differs from the value derived from support_model 'business-hours'" in findings[0]


def test_mismatch_24x7_next_morning_triggers_r_prd_05():
    """The exact case named in the task's own CORRECT OUTPUT block."""
    case = "mismatch_24x7_next_morning"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert findings == [
        "R-PRD-05 ops-mismatch-24x7-next-morning: detection_expectation "
        "'next-business-morning' differs from the value derived from support_model "
        "'24x7'; Section 15.1 fails a declared value differing from the derived value"
    ]


def test_extended_no_window_triggers_r_prd_13():
    case = "extended_no_window"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-13" in findings[0]
    assert "requires a coverage_window; Section 15.5" in findings[0]


def test_24x7_no_window_triggers_r_prd_13():
    case = "24x7_no_window"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-13" in findings[0]
    assert "support_model '24x7' requires a coverage_window" in findings[0]


def test_launched_no_intake_triggers_r_prd_14():
    case = "launched_no_intake"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-14" in findings[0]
    assert "declares no intake_channel" in findings[0]


def test_launched_no_triager_triggers_r_prd_14():
    case = "launched_no_triager"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-14" in findings[0]
    assert "declares no triager" in findings[0]


def test_responder_not_assigned_triggers_r_prd_15():
    case = "responder_not_assigned"
    assert _errors_for(case) == []
    findings = _findings_for(case)
    assert len(findings) == 1
    assert "R-PRD-15" in findings[0]
    assert "primary_responder 'resp-ghost'" in findings[0]
    assert "does not match one; Section 15.1" in findings[0]


def test_coverage_window_extra_field_fails_schema():
    case = "coverage_window_extra_field"
    assert len(_errors_for(case)) > 0


def test_coverage_window_utc_offset_fails_schema():
    """timezone must be an IANA name (Section 47.9's `ianaTimezone`
    $def), never a bare UTC offset."""
    case = "coverage_window_utc_offset"
    assert len(_errors_for(case)) > 0
