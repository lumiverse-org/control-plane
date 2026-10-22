"""Tests for R-INV-02: Invariant classification register and its CI rule.

Spec: Section 101 preamble; Section 55; Section 52.6; Section 0.7.
Task: lanes/L1-05-tasks.md, L1-902.

12 test cases:
- 5 valid:
  1. empty_register (invariants: [], declared_count: 111)
  2. one_mechanical_naming_rule (enforced_by: "R-EXC-00", present in known rules)
  3. one_mechanical_naming_at (enforced_by: "AT-039")
  4. one_policy_naming_live_policy (policy_id: "POL-001" present in policies.yaml)
  5. one_review_held (review and chair both non-null)
- 7 invalid:
  6. no_classification (classification absent/null -> limb a error)
  7. mechanical_names_nothing (classification == mechanical, enforced_by: null -> limb b error)
  8. mechanical_names_dead_rule (classification == mechanical, enforced_by: "R-XYZ-99" -> limb b error)
  9. policy_names_missing_policy (classification == policy, policy_id: "POL-NOT-REAL" -> limb c error)
  10. review_held_no_chair (classification == review-held, chair: null -> limb d error)
  11. bad_classification_token (classification: "automatic" -> schema enum validation error)
  12. count_mismatch_when_populated (two entries, declared_count: 111 -> limb e error)
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest
import jsonschema

from validators.registry.rules import r_inv_02

SCHEMAS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "schemas" / "registry"
SCHEMA_PATH = SCHEMAS_DIR / "invariants.v1.schema.json"


@pytest.fixture(scope="module")
def invariant_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---- Valid cases (5) --------------------------------------------------------


def test_valid_empty_register(invariant_schema):
    """Limb e does not fire on empty register; schema validates empty list."""
    doc = {
        "registry_version": 1,
        "declared_count": 111,
        "invariants": [],
    }
    jsonschema.validate(instance=doc, schema=invariant_schema)
    passed, findings = r_inv_02.check_document(doc)
    assert passed is True
    assert findings == []


def test_valid_one_mechanical_naming_rule(invariant_schema):
    """Mechanical invariant naming a known rule ID succeeds."""
    doc = {
        "registry_version": 1,
        "declared_count": 1,
        "invariants": [
            {
                "number": 1,
                "text": "Exceptions require valid expiry date.",
                "classification": "mechanical",
                "enforced_by": "R-EXC-00",
                "policy_id": None,
                "review": None,
                "chair": None,
            }
        ],
    }
    jsonschema.validate(instance=doc, schema=invariant_schema)
    passed, findings = r_inv_02.check_document(doc, known_rules={"R-EXC-00"})
    assert passed is True
    assert findings == []


def test_valid_one_mechanical_naming_at(invariant_schema):
    """Mechanical invariant naming an AT-nnn identifier succeeds."""
    doc = {
        "registry_version": 1,
        "declared_count": 1,
        "invariants": [
            {
                "number": 2,
                "text": "Canary intact check.",
                "classification": "mechanical",
                "enforced_by": "AT-039",
                "policy_id": None,
                "review": None,
                "chair": None,
            }
        ],
    }
    jsonschema.validate(instance=doc, schema=invariant_schema)
    passed, findings = r_inv_02.check_document(doc)
    assert passed is True
    assert findings == []


def test_valid_one_policy_naming_live_policy(invariant_schema):
    """Policy invariant naming a policy present in policies.yaml succeeds."""
    doc = {
        "registry_version": 1,
        "declared_count": 1,
        "invariants": [
            {
                "number": 3,
                "text": "Code ownership review policy.",
                "classification": "policy",
                "enforced_by": None,
                "policy_id": "POL-ARCH-01",
                "review": None,
                "chair": None,
            }
        ],
    }
    policies_doc = {
        "policies": [
            {"id": "POL-ARCH-01", "name": "Architecture Review Policy"}
        ]
    }
    jsonschema.validate(instance=doc, schema=invariant_schema)
    passed, findings = r_inv_02.check_document(doc, policies_doc=policies_doc)
    assert passed is True
    assert findings == []


def test_valid_one_review_held(invariant_schema):
    """Review-held invariant naming both review and chair succeeds."""
    doc = {
        "registry_version": 1,
        "declared_count": 1,
        "invariants": [
            {
                "number": 4,
                "text": "Quarterly architecture review.",
                "classification": "review-held",
                "enforced_by": None,
                "policy_id": None,
                "review": "quarterly-architecture",
                "chair": "chief-architect",
            }
        ],
    }
    jsonschema.validate(instance=doc, schema=invariant_schema)
    passed, findings = r_inv_02.check_document(doc)
    assert passed is True
    assert findings == []


# ---- Invalid cases (7) ------------------------------------------------------


def test_invalid_no_classification():
    """Limb a: invariant carries no classification (absent/null)."""
    doc = {
        "registry_version": 1,
        "declared_count": 1,
        "invariants": [
            {
                "number": 10,
                "text": "Invariant missing classification.",
                "classification": None,
                "enforced_by": None,
                "policy_id": None,
                "review": None,
                "chair": None,
            }
        ],
    }
    passed, findings = r_inv_02.check_document(doc)
    assert passed is False
    assert len(findings) == 1
    assert "invariant 10 carries no enforcement classification; Section 101" in findings[0]


def test_invalid_mechanical_names_nothing():
    """Limb b: classification == mechanical and enforced_by is null."""
    doc = {
        "registry_version": 1,
        "declared_count": 1,
        "invariants": [
            {
                "number": 11,
                "text": "Mechanical invariant without check.",
                "classification": "mechanical",
                "enforced_by": None,
                "policy_id": None,
                "review": None,
                "chair": None,
            }
        ],
    }
    passed, findings = r_inv_02.check_document(doc)
    assert passed is False
    assert len(findings) == 1
    assert "invariant 11 is classified mechanical and names no live check or AT- identifier; Section 101" in findings[0]


def test_invalid_mechanical_names_dead_rule():
    """Limb b: classification == mechanical and enforced_by names dead/unknown rule."""
    doc = {
        "registry_version": 1,
        "declared_count": 1,
        "invariants": [
            {
                "number": 12,
                "text": "Mechanical invariant with nonexistent rule.",
                "classification": "mechanical",
                "enforced_by": "R-XYZ-99",
                "policy_id": None,
                "review": None,
                "chair": None,
            }
        ],
    }
    passed, findings = r_inv_02.check_document(doc, known_rules={"R-EXC-00", "R01"})
    assert passed is False
    assert len(findings) == 1
    assert "invariant 12 is classified mechanical and names no live check or AT- identifier; Section 101" in findings[0]


def test_invalid_policy_names_missing_policy():
    """Limb c: classification == policy and policy_id is missing from policies.yaml."""
    doc = {
        "registry_version": 1,
        "declared_count": 1,
        "invariants": [
            {
                "number": 13,
                "text": "Policy invariant with unknown policy id.",
                "classification": "policy",
                "enforced_by": None,
                "policy_id": "POL-NOT-REAL",
                "review": None,
                "chair": None,
            }
        ],
    }
    policies_doc = {
        "policies": [
            {"id": "POL-KNOWN-01"}
        ]
    }
    passed, findings = r_inv_02.check_document(doc, policies_doc=policies_doc)
    assert passed is False
    assert len(findings) == 1
    assert "invariant 13 is classified policy and names no live policies.yaml entry; Section 101" in findings[0]


def test_invalid_review_held_no_chair():
    """Limb d: classification == review-held and chair is null."""
    doc = {
        "registry_version": 1,
        "declared_count": 1,
        "invariants": [
            {
                "number": 14,
                "text": "Review-held invariant without chair.",
                "classification": "review-held",
                "enforced_by": None,
                "policy_id": None,
                "review": "standing-review",
                "chair": None,
            }
        ],
    }
    passed, findings = r_inv_02.check_document(doc)
    assert passed is False
    assert len(findings) == 1
    assert "invariant 14 is classified review-held and names no standing review or chairing role; Section 101" in findings[0]


def test_invalid_bad_classification_token(invariant_schema):
    """Schema rejects invalid classification enum value ('automatic')."""
    doc = {
        "registry_version": 1,
        "declared_count": 1,
        "invariants": [
            {
                "number": 15,
                "text": "Invariant with invalid classification token.",
                "classification": "automatic",
                "enforced_by": None,
                "policy_id": None,
                "review": None,
                "chair": None,
            }
        ],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=doc, schema=invariant_schema)


def test_invalid_count_mismatch_when_populated():
    """Limb e: invariants register is non-empty and len(invariants) != declared_count."""
    doc = {
        "registry_version": 1,
        "declared_count": 111,
        "invariants": [
            {
                "number": 1,
                "text": "Invariant 1",
                "classification": "mechanical",
                "enforced_by": "AT-001",
                "policy_id": None,
                "review": None,
                "chair": None,
            },
            {
                "number": 2,
                "text": "Invariant 2",
                "classification": "mechanical",
                "enforced_by": "AT-002",
                "policy_id": None,
                "review": None,
                "chair": None,
            },
        ],
    }
    passed, findings = r_inv_02.check_document(doc)
    assert passed is False
    assert len(findings) == 1
    assert "the invariant register holds 2 entries; declared_count is 111; Section 101 states 111" in findings[0]
