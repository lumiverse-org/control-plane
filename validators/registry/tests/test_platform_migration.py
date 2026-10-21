"""Tests for the `platform_migration` block added to both
schemas/product/product.contract.v2.schema.json and
schemas/product/product.contract.v1.schema.json (L1-703, Section 60.3,
invariant 74).

Adapted to validate fixtures directly with `jsonschema` rather than the
L1-005 fixture-case harness -- FD-094 (DECIDED) supersedes that harness in
favour of Option B, the same adaptation test_product_envelope.py and
test_product_platform_blocks.py already document. The task doc's
ACCEPTANCE rows that invoke `validators.registry.cli --records-root ...`
and expect an `OK: N file(s) validated` grammar describe a CLI mode that
was never built against Option B (validators/registry/cli.py is the
frozen R01-R18 dispatch table) -- see validators/registry/rules/
r_inv_01.py and test_verification_schema.py for the same, already
established adaptation.

10 test functions: 3 valid + 7 invalid, matching the task's own
fixture-case table exactly.
"""
import json
import os

import jsonschema
import yaml
from referencing import Registry, Resource

SCHEMAS_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "schemas")
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "product", "migration")


def _registry(version="v2"):
    defs_path = os.path.join(SCHEMAS_ROOT, "registry", "common", "defs.v1.schema.json")
    assignments_path = os.path.join(SCHEMAS_ROOT, "registry", "common", "assignments.v1.schema.json")
    product_path = os.path.join(SCHEMAS_ROOT, "product", f"product.contract.{version}.schema.json")
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


def _errors_for(case, version="v2"):
    schema, reg = _registry(version)
    validator = jsonschema.Draft202012Validator(schema, registry=reg)
    doc = _load_fixture(case)
    return list(validator.iter_errors(doc))


# ---- valid cases (3) -------------------------------------------------


def test_valid_transitional_with_block():
    assert _errors_for(os.path.join("valid", "transitional_with_block")) == []


def test_valid_supported_null_block():
    assert _errors_for(os.path.join("valid", "supported_null_block")) == []


def test_valid_v1_transitional_with_block():
    assert _errors_for(os.path.join("valid", "v1_transitional_with_block"), version="v1") == []


# ---- invalid cases (7) ------------------------------------------------


def test_transitional_null_block():
    assert len(_errors_for("transitional_null_block")) > 0


def test_block_missing_owner():
    assert len(_errors_for("block_missing_owner")) > 0


def test_block_missing_deadline():
    assert len(_errors_for("block_missing_deadline")) > 0


def test_block_missing_target():
    assert len(_errors_for("block_missing_target")) > 0


def test_block_extra_field():
    assert len(_errors_for("block_extra_field")) > 0


def test_deadline_not_date():
    assert len(_errors_for("deadline_not_date")) > 0


def test_target_version_zero():
    assert len(_errors_for("target_version_zero")) > 0
