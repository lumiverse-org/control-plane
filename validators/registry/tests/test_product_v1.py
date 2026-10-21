"""Tests for schemas/product/product.contract.v1.schema.json (L1-309,
Section 15 / §60.2; AT-025; invariant 73).

Adapted to validate fixtures directly with `jsonschema` rather than through
`validators/registry/cli.py` -- FD-094 (DECIDED) supersedes the CLI-based
acceptance grammar in favour of Option B, the same adaptation
`test_product_platform_blocks.py` and `test_product_envelope.py` already
document.

9 test functions: 3 valid, 6 invalid, matching the task's own fixture-case
table (lanes/L1-05-tasks.md:1918) exactly.
"""
import json
import os

import jsonschema
import yaml
from referencing import Registry, Resource

SCHEMAS_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "schemas")
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "product", "v1")


def _registry():
    defs_path = os.path.join(SCHEMAS_ROOT, "registry", "common", "defs.v1.schema.json")
    assignments_path = os.path.join(SCHEMAS_ROOT, "registry", "common", "assignments.v1.schema.json")
    product_path = os.path.join(SCHEMAS_ROOT, "product", "product.contract.v1.schema.json")
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


# ---- valid cases (3) ------------------------------------------------------


def test_valid_v1_minimal():
    assert _errors_for(os.path.join("valid", "v1_minimal")) == []


def test_valid_v1_without_commitments():
    assert _errors_for(os.path.join("valid", "v1_without_commitments")) == []


def test_valid_v1_without_data():
    assert _errors_for(os.path.join("valid", "v1_without_data")) == []


# ---- invalid cases (6) -----------------------------------------------------


def test_v1_declares_version_2():
    assert len(_errors_for("v1_declares_version_2")) > 0


def test_v1_extra_field():
    assert len(_errors_for("v1_extra_field")) > 0


def test_v1_missing_identity():
    assert len(_errors_for("v1_missing_identity")) > 0


def test_v1_bad_conformance():
    assert len(_errors_for("v1_bad_conformance")) > 0


def test_v1_missing_business():
    assert len(_errors_for("v1_missing_business")) > 0


def test_v1_missing_recovery():
    assert len(_errors_for("v1_missing_recovery")) > 0
