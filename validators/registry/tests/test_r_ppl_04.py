"""Tests for R-PPL-04 (L1-206, Section 99.2 subsystem B, invariant 50).

Exercised by calling ``validators.registry.rules.r_ppl_04`` directly against
parsed ``people.yaml`` / ``roles.yaml`` fixtures, rather than through
``validators/registry/cli.py`` -- see the module docstring of ``r_ppl_04.py``
and, for precedent, ``r_svc_01.py`` / ``r_svc_03.py`` / ``r_ppl_05.py``'s own
notes that FD-094 (DECIDED) supersedes the CLI grammar and
``echo "EXIT=$?"`` acceptance commands written into ``lanes/L1-05-tasks.md``.

5 test functions, matching the task's own fixture-case list exactly: 2 valid,
3 invalid.
"""
import os

import yaml

from validators.registry.rules import r_ppl_04

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "ppl04")


def _load(case, filename):
    path = os.path.join(FIXTURES_DIR, case, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _people(case):
    return _load(case, "people.yaml")


def _known_role_ids(case):
    doc = _load(case, "roles.yaml")
    if doc is None:
        return None
    return {r["id"] for r in doc.get("roles", [])}


def test_valid_resolves():
    case = os.path.join("valid", "resolves")
    assert r_ppl_04.check(_people(case), _known_role_ids(case)) == []


def test_no_roles_file_is_silent():
    case = os.path.join("valid", "people_only_no_roles_file")
    assert _known_role_ids(case) is None
    assert r_ppl_04.check(_people(case), _known_role_ids(case)) == []


def test_unknown_role():
    case = "unknown_role"
    findings = r_ppl_04.check(_people(case), _known_role_ids(case))
    assert len(findings) == 1
    assert "dev-a" in findings[0]
    assert "architect" in findings[0]
    assert "does not exist in roles.yaml" in findings[0]


def test_role_empty_string():
    case = "role_empty_string"
    findings = r_ppl_04.check(_people(case), _known_role_ids(case))
    assert len(findings) == 1
    assert "''" in findings[0] or "role ''" in findings[0]


def test_two_unknown_roles():
    case = "two_unknown_roles"
    findings = r_ppl_04.check(_people(case), _known_role_ids(case))
    assert len(findings) == 2
