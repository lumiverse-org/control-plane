"""Tests for validators.registry.versioning (L1-701, Section 60.2, AT-025).

Exercised by calling ``validators.registry.versioning`` functions directly
against parsed fixture documents, rather than through ``cli.py`` -- see
precedent in ``r_prd_11.py`` and ``test_r_ver_02.py``: FD-094
(contracts/validator-contract.md) freezes the Option B R01..R18 dispatch
engine and its CLI grammar.

Exactly 17 test functions: 6 valid, 11 invalid, matching the task's own
fixture-case table.
"""
from __future__ import annotations

import os
import pytest
import yaml

from validators.registry.versioning import (
    VERSION_FIELD,
    UnknownKind,
    UnknownVersion,
    document_version,
    select_schema,
    supported_versions,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "versioning")


def _load(case: str, filename: str) -> dict:
    path = os.path.join(FIXTURES_DIR, case, filename)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Valid (6)
# ---------------------------------------------------------------------------


def test_valid_both_versions_one_run():
    v1_doc = _load(os.path.join("valid", "both_versions_one_run"), "product-v1.yaml")
    v2_doc = _load(os.path.join("valid", "both_versions_one_run"), "product-v2.yaml")

    assert document_version("product", v1_doc) == 1
    assert document_version("product", v2_doc) == 2
    assert (
        select_schema("product", v2_doc)
        == "schemas/product/product.contract.v2.schema.json"
    )
    assert (
        select_schema("product", v1_doc)
        == "schemas/product/product.contract.v1.schema.json"
    )


def test_valid_product_v1():
    doc = _load(os.path.join("valid", "product_v1"), "product.yaml")
    assert document_version("product", doc) == 1
    assert (
        select_schema("product", doc)
        == "schemas/product/product.contract.v1.schema.json"
    )


def test_valid_product_v2():
    doc = _load(os.path.join("valid", "product_v2"), "product.yaml")
    assert document_version("product", doc) == 2
    assert (
        select_schema("product", doc)
        == "schemas/product/product.contract.v2.schema.json"
    )


def test_valid_service_v1():
    doc = _load(os.path.join("valid", "service_v1"), "service.yaml")
    assert document_version("service", doc) == 1
    assert (
        select_schema("service", doc)
        == "schemas/registry/service.v1.schema.json"
    )


def test_valid_verification_v1():
    doc = _load(os.path.join("valid", "verification_v1"), "verification-contract.yaml")
    assert document_version("verification-contract", doc) == 1
    assert (
        select_schema("verification-contract", doc)
        == "schemas/product/verification.contract.v1.schema.json"
    )


def test_valid_people_v1():
    doc = _load(os.path.join("valid", "people_v1"), "people.yaml")
    assert document_version("people", doc) == 1
    assert (
        select_schema("people", doc)
        == "schemas/registry/people.registry.v1.schema.json"
    )


# ---------------------------------------------------------------------------
# Invalid (11)
# ---------------------------------------------------------------------------


def test_product_version_3_has_no_schema():
    doc = _load("product_version_3", "product.yaml")
    with pytest.raises(UnknownVersion) as exc:
        select_schema("product", doc)
    assert "no schema for kind 'product' version 3" in str(exc.value)


def test_product_version_0_rejected():
    doc = _load("product_version_0", "product.yaml")
    with pytest.raises(UnknownVersion):
        document_version("product", doc)


def test_product_version_string_rejected():
    doc = _load("product_version_string", "product.yaml")
    with pytest.raises(UnknownVersion):
        document_version("product", doc)


def test_version_field_absent_rejected():
    doc = _load("version_field_absent", "product.yaml")
    with pytest.raises(UnknownVersion):
        document_version("product", doc)


def test_wrong_version_field_name_rejected():
    doc = _load("wrong_version_field_name", "product.yaml")
    with pytest.raises(UnknownVersion):
        document_version("product", doc)


def test_two_version_fields_rejected():
    doc = _load("two_version_fields", "product.yaml")
    with pytest.raises(UnknownVersion):
        document_version("product", doc)


def test_service_version_2_has_no_schema():
    doc = _load("service_version_2", "service.yaml")
    with pytest.raises(UnknownVersion):
        select_schema("service", doc)


def test_verification_version_2_has_no_schema():
    doc = _load("verification_version_2", "verification-contract.yaml")
    with pytest.raises(UnknownVersion):
        select_schema("verification-contract", doc)


def test_people_registry_version_2_has_no_schema():
    doc = _load("people_registry_version_2", "people.yaml")
    with pytest.raises(UnknownVersion):
        select_schema("people", doc)


def test_platform_version_not_semver_rejected():
    doc = _load("platform_version_not_semver", "platform.yaml")
    with pytest.raises(UnknownVersion):
        document_version("platform", doc)


def test_unknown_kind_records_rejected():
    doc = _load("unknown_kind_records", "record.yaml")
    with pytest.raises(UnknownKind):
        select_schema("records", doc)
    with pytest.raises(UnknownKind):
        document_version("records", doc)
