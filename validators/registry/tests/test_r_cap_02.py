"""Tests for R-CAP-02, R-CAP-03, R-CAP-04 (L1-202, Section 8 (D106) /
invariant 79; Section 7.1).

Exercises validators.registry.rules.r_cap_02 directly against the fixtures
under validators/registry/fixtures/cap02/, rather than through
validators/registry/cli.py -- see the module docstring of r_cap_02.py and
precedent in r_inv_01.py / r_ppl_05.py / test_exceptions_minimal.py: FD-094
(DECIDED) supersedes the CLI grammar and discover()/RULE_ID/expect.yaml
harness written into lanes/L1-05-tasks.md.

11 test functions, matching the task's own fixture-case list exactly.
test_spec_founder_row_matches_d106 verifies that the founder role row
complies with D106 (CCR-003 resolved 2026-10-24 by Founder decision).
Expected pytest summary: 11 passed, 0 xfailed.
"""
import os

import pytest
import yaml

from validators.registry.rules import r_cap_02

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "cap02")


def _load(case, filename):
    path = os.path.join(FIXTURES_DIR, case, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _roles(case):
    return _load(case, "roles.yaml")


def _people(case):
    return _load(case, "people.yaml")


# ---- valid (2) --------------------------------------------------------


def test_valid_clean_defaults_no_errors():
    case = os.path.join("valid", "clean_defaults")
    assert r_cap_02.check_r_cap_02(_roles(case)) == []
    assert r_cap_02.check_r_cap_03(_roles(case)) == []


def test_valid_dangerous_capability_in_people_only_no_errors():
    # D106's sanctioned alternative: an explicit people.yaml grant of a
    # dangerous capability is not a violation -- R-CAP-02 never reads
    # people.yaml at all, and R-CAP-04 only cares about duplicates.
    case = os.path.join("valid", "dangerous_in_people_only")
    assert r_cap_02.check_r_cap_02(_roles(case)) == []
    assert r_cap_02.check_r_cap_04(_people(case)) == []


# ---- founder row complies with D106 (CCR-003, resolved) -----------------


def test_spec_founder_row_matches_d106():
    findings = r_cap_02.check_r_cap_02(_roles("spec_founder_row"))
    assert findings == []


# ---- R-CAP-02 single-token cases (4) ------------------------------------


def test_production_approval_default_fires_r_cap_02():
    findings = r_cap_02.check_r_cap_02(_roles("production_approval_default"))
    assert len(findings) == 1
    assert "R-CAP-02" in findings[0]
    assert "production-approval" in findings[0]
    assert "test_role" in findings[0]
    assert "D106 grants these only by explicit people.yaml entry" in findings[0]


def test_platform_admin_default_fires_r_cap_02():
    findings = r_cap_02.check_r_cap_02(_roles("platform_admin_default"))
    assert len(findings) == 1
    assert "R-CAP-02" in findings[0]
    assert "platform-admin" in findings[0]


def test_security_review_default_fires_r_cap_02():
    findings = r_cap_02.check_r_cap_02(_roles("security_review_default"))
    assert len(findings) == 1
    assert "R-CAP-02" in findings[0]
    assert "security-review" in findings[0]


def test_people_intelligence_default_fires_r_cap_02():
    findings = r_cap_02.check_r_cap_02(_roles("people_intelligence_default"))
    assert len(findings) == 1
    assert "R-CAP-02" in findings[0]
    assert "people-intelligence" in findings[0]


# ---- multi-token / duplicate cases (3) ----------------------------------


def test_two_dangerous_one_role_fires_r_cap_02_twice():
    findings = r_cap_02.check_r_cap_02(_roles("two_dangerous_one_role"))
    assert len(findings) == 2
    assert all("R-CAP-02" in f for f in findings)
    assert any("production-approval" in f for f in findings)
    assert any("platform-admin" in f for f in findings)


def test_duplicate_role_id_fires_r_cap_03():
    case = "duplicate_role_id"
    findings = r_cap_02.check_r_cap_03(_roles(case))
    assert len(findings) == 1
    assert "R-CAP-03" in findings[0]
    assert "duplicate role id 'test_role'" in findings[0]
    # clean default_capabilities on both entries -- R-CAP-02 silent here
    assert r_cap_02.check_r_cap_02(_roles(case)) == []


def test_duplicate_capability_on_person_fires_r_cap_04():
    findings = r_cap_02.check_r_cap_04(_people("duplicate_capability_on_person"))
    assert len(findings) == 1
    assert "R-CAP-04" in findings[0]
    assert "duplicate capability 'code-review' on person 'p-1'" in findings[0]


# ---- all eight (1) -------------------------------------------------------


def test_all_eight_dangerous_fires_r_cap_02_eight_times():
    findings = r_cap_02.check_r_cap_02(_roles("all_eight_dangerous"))
    assert len(findings) == 8
    assert all("R-CAP-02" in f for f in findings)
    for token in r_cap_02.DANGEROUS_CAPABILITIES:
        assert any(f"'{token}'" in f for f in findings)
