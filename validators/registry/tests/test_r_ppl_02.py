"""Tests for R-PPL-02, R-PPL-06, R-PPL-07 (L1-204, Section 7.1).

Exercises validators.registry.rules.r_ppl_02 directly against the 16
fixtures under validators/registry/fixtures/ppl02/m_<availability>_
<access_status>/, one fixture per cell of the full 4x4 availability x
access_status matrix -- rather than through validators/registry/cli.py.
See the module docstring of r_ppl_02.py, and precedent in r_ppl_05.py /
r_exc_01.py / test_exception_rules.py: FD-094 (DECIDED) supersedes the
CLI grammar and echo "EXIT=$?" acceptance commands written into
lanes/L1-05-tasks.md.

Exactly 16 test functions, one per matrix cell, matching the task's own
count exactly.
"""
import os

import yaml

from validators.registry.rules import r_ppl_02

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "ppl02")


def _run_case(case):
    case_dir = os.path.join(FIXTURES_DIR, case)
    with open(os.path.join(case_dir, "people.yaml"), encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    with open(os.path.join(case_dir, "expect.yaml"), encoding="utf-8") as f:
        expect = yaml.safe_load(f)
    findings = r_ppl_02.check(doc, expect["today"])
    fired = sorted(f.split(" ", 1)[0] for f in findings)
    return expect, fired, findings


def _assert_case(case):
    expect, fired, findings = _run_case(case)
    expected = sorted(expect["expect_errors"])
    assert fired == expected, (
        f"{case}: expected rule ids {expected}, got {fired}\n" + "\n".join(findings)
    )
    assert expect["expect_exit"] == (1 if expected else 0)
    return findings


def test_m_active_pending():
    _assert_case("m_active_pending")


def test_m_active_provisioned():
    _assert_case("m_active_provisioned")


def test_m_active_suspended():
    _assert_case("m_active_suspended")


def test_m_active_revoked():
    findings = _assert_case("m_active_revoked")
    assert "R-PPL-06" in findings[0]
    assert "is neither departed nor a non-employee past end_date" in findings[0]


def test_m_on_leave_pending():
    _assert_case("m_on_leave_pending")


def test_m_on_leave_provisioned():
    _assert_case("m_on_leave_provisioned")


def test_m_on_leave_suspended():
    _assert_case("m_on_leave_suspended")


def test_m_on_leave_revoked():
    findings = _assert_case("m_on_leave_revoked")
    assert "R-PPL-06" in findings[0]


def test_m_departing_pending():
    _assert_case("m_departing_pending")


def test_m_departing_provisioned():
    _assert_case("m_departing_provisioned")


def test_m_departing_suspended():
    findings = _assert_case("m_departing_suspended")
    assert "R-PPL-07" in findings[0]


def test_m_departing_revoked():
    findings = _assert_case("m_departing_revoked")
    assert "R-PPL-06" in findings[0]


def test_m_departed_pending():
    findings = _assert_case("m_departed_pending")
    assert "R-PPL-02" in findings[0]


def test_m_departed_provisioned():
    findings = _assert_case("m_departed_provisioned")
    assert "R-PPL-02" in findings[0]
    assert "dev-a" in findings[0]
    assert "must have access_status revoked" in findings[0]


def test_m_departed_suspended():
    findings = _assert_case("m_departed_suspended")
    assert len(findings) == 2


def test_m_departed_revoked():
    _assert_case("m_departed_revoked")
