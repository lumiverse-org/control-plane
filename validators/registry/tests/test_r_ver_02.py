"""Tests for R-VER-02, R-VER-04, R-VER-05, R-VER-06 (L1-402, Section 31.2,
SIG-18).

Exercised by calling ``validators.registry.rules.r_ver_02`` /
``r_ver_04`` / ``r_ver_05`` / ``r_ver_06`` directly against parsed
``verification-contract.yaml`` fixtures, rather than through
``validators/registry/cli.py`` -- see those modules' docstrings, and
``test_service_schema.py`` / ``test_r_prd_11.py`` for precedent: FD-094
(contracts/validator-contract.md) freezes the Option B R01..R18 dispatch
engine and its CLI grammar; the L1-005 discover()/RULE_ID/APPLIES_TO
harness never landed in this tree (``validators/registry/rules/
__init__.py`` is empty), and extending the frozen catalogue for the
R-VER-* ids is not this task's call to make.

8 test functions: 3 valid, 5 invalid, matching the task's own fixture-case
table exactly.
"""
import os

import yaml

from validators.registry.rules import r_ver_02, r_ver_04, r_ver_05, r_ver_06

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "ver02")


def _load(case):
    path = os.path.join(FIXTURES_DIR, case, "verification-contract.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _all_findings(doc):
    findings = []
    findings.extend(r_ver_02.check(doc))
    findings.extend(r_ver_04.check(doc))
    findings.extend(r_ver_05.check(doc))
    findings.extend(r_ver_06.check(doc))
    return findings


# ---------------------------------------------------------------------------
# valid (3)
# ---------------------------------------------------------------------------


def test_valid_failed_as_expected():
    doc = _load(os.path.join("valid", "failed_as_expected"))
    assert _all_findings(doc) == []


def test_valid_never_run():
    doc = _load(os.path.join("valid", "never_run"))
    assert _all_findings(doc) == []


def test_valid_all_mapped_to_active():
    doc = _load(os.path.join("valid", "all_mapped_to_active"))
    assert _all_findings(doc) == []


# ---------------------------------------------------------------------------
# invalid (5)
# ---------------------------------------------------------------------------


def test_passed_unexpectedly_triggers_r_ver_02():
    doc = _load("passed_unexpectedly")
    findings = r_ver_02.check(doc)
    assert len(findings) == 1
    assert "SDC-001" in findings[0]
    assert "passed on its last run" in findings[0]
    assert "Section 31.2, SIG-18" in findings[0]
    assert r_ver_04.check(doc) == []
    assert r_ver_05.check(doc) == []
    assert r_ver_06.check(doc) == []


def test_not_run_with_date_triggers_r_ver_04():
    doc = _load("not_run_with_date")
    findings = r_ver_04.check(doc)
    assert len(findings) == 1
    assert "SDC-001" in findings[0]
    assert "records a run date of 2026-08-20" in findings[0]
    assert "not-run" in findings[0]
    assert r_ver_02.check(doc) == []
    assert r_ver_05.check(doc) == []
    assert r_ver_06.check(doc) == []


def test_result_without_date_triggers_r_ver_05():
    doc = _load("result_without_date")
    findings = r_ver_05.check(doc)
    assert len(findings) == 1
    assert "SDC-001" in findings[0]
    assert "claims result 'failed-as-expected'" in findings[0]
    assert "no run date" in findings[0]
    assert r_ver_02.check(doc) == []
    assert r_ver_04.check(doc) == []
    assert r_ver_06.check(doc) == []


def test_passed_and_missing_date_triggers_r_ver_02_and_r_ver_05():
    doc = _load("passed_and_missing_date")
    findings = _all_findings(doc)
    assert len(findings) == 2
    assert any("passed on its last run" in f for f in findings)
    assert any("no run date" in f for f in findings)
    assert r_ver_04.check(doc) == []
    assert r_ver_06.check(doc) == []


def test_mapped_to_not_applicable_triggers_r_ver_06():
    doc = _load("mapped_to_not_applicable")
    findings = r_ver_06.check(doc)
    assert len(findings) == 1
    assert "REQ-004" in findings[0]
    assert "performance" in findings[0]
    assert "not-applicable" in findings[0]
    assert "SIG-18" in findings[0]
    assert r_ver_02.check(doc) == []
    assert r_ver_04.check(doc) == []
    assert r_ver_05.check(doc) == []
