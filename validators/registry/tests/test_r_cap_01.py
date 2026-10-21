"""Tests for R-CAP-01 (L1-201, Section 9.1, Invariant 11).

Direct unit tests against synthetic fixtures under
validators/registry/fixtures/cap01/<case>/ per the task doc's fixture-case table.
"""
import os
import yaml

from validators.registry.rules import r_cap_01

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "cap01")


def _load(case, filename):
    path = os.path.join(FIXTURES_DIR, case, filename)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_valid_all_known():
    roles_doc = _load("valid/all_known", "roles.yaml")
    people_doc = _load("valid/all_known", "people.yaml")
    assert r_cap_01.check_roles_document(roles_doc) == (True, [])
    assert r_cap_01.check_people_document(people_doc) == (True, [])


def test_role_default_unknown():
    roles_doc = _load("role_default_unknown", "roles.yaml")
    passed, findings = r_cap_01.check_roles_document(roles_doc)
    assert passed is False
    assert len(findings) == 1
    assert "telepathy" in findings[0]
    assert "/roles/0/default_capabilities/1" in findings[0]
    assert "Section 9 is the complete vocabulary" in findings[0]


def test_person_grant_unknown():
    people_doc = _load("person_grant_unknown", "people.yaml")
    passed, findings = r_cap_01.check_people_document(people_doc, source="people.yaml")
    assert passed is False
    assert len(findings) == 1
    assert findings[0] == (
        "R-CAP-01 people.yaml:/people/0/capabilities/1 undefined capability 'wizardry'; "
        "Section 9 is the complete vocabulary"
    )


def test_typo_case_mismatch():
    roles_doc = _load("typo_case_mismatch", "roles.yaml")
    passed, findings = r_cap_01.check_roles_document(roles_doc)
    assert passed is False
    assert len(findings) == 1
    assert "'Code-Review'" in findings[0]
    assert "/roles/0/default_capabilities/0" in findings[0]


def test_typo_underscore():
    people_doc = _load("typo_underscore", "people.yaml")
    passed, findings = r_cap_01.check_people_document(people_doc)
    assert passed is False
    assert len(findings) == 1
    assert "'code_review'" in findings[0]
    assert "/people/0/capabilities/0" in findings[0]


def test_empty_string_capability():
    roles_doc = _load("empty_string_capability", "roles.yaml")
    passed, findings = r_cap_01.check_roles_document(roles_doc)
    assert passed is False
    assert len(findings) == 1
    assert "undefined capability ''" in findings[0]
    assert "/roles/0/default_capabilities/0" in findings[0]


def test_both_files_unknown():
    roles_doc = _load("both_files_unknown", "roles.yaml")
    people_doc = _load("both_files_unknown", "people.yaml")
    _, role_findings = r_cap_01.check_roles_document(roles_doc)
    _, people_findings = r_cap_01.check_people_document(people_doc)
    assert len(role_findings) + len(people_findings) == 2
