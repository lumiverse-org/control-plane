"""Tests for R-PPL-01 (L1-203, Section 7.1, invariant 58).

Exercised by calling validators.registry.rules.r_ppl_01 directly against
a parsed people.yaml fixture, rather than through
validators/registry/cli.py -- see the module docstring of r_ppl_01.py
and, for precedent, test_r_ppl_05.py's own note that FD-094 (DECIDED)
supersedes the CLI grammar and `echo "EXIT=$?"` acceptance commands
written into lanes/L1-05-tasks.md.

8 test functions: 2 valid, 6 invalid, matching the task's own fixture-case
list exactly.
"""
import os

import yaml

from validators.registry.rules import r_ppl_01

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "ppl01")


def _load(case):
    path = os.path.join(FIXTURES_DIR, case, "people.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _findings(case):
    return r_ppl_01.check(_load(case))


# ---------------------------------------------------------------------------
# valid (2)
# ---------------------------------------------------------------------------


def test_valid_employee_null_end_date():
    case = os.path.join("valid", "employee_null_end_date")
    assert _findings(case) == []


def test_valid_contractor_with_end_date():
    case = os.path.join("valid", "contractor_with_end_date")
    assert _findings(case) == []


# ---------------------------------------------------------------------------
# invalid (6)
# ---------------------------------------------------------------------------


def test_contractor_null_triggers_r_ppl_01():
    findings = _findings("contractor_null")
    assert len(findings) == 1
    assert "R-PPL-01" in findings[0]
    assert "'con-1'" in findings[0]
    assert "(contractor)" in findings[0]
    assert "has no end_date" in findings[0]
    assert "Section 7.1" in findings[0]


def test_intern_null_triggers_r_ppl_01():
    findings = _findings("intern_null")
    assert len(findings) == 1
    assert "R-PPL-01" in findings[0]
    assert "(intern)" in findings[0]


def test_temporary_specialist_null_triggers_r_ppl_01():
    findings = _findings("temporary_specialist_null")
    assert len(findings) == 1
    assert "R-PPL-01" in findings[0]
    assert "(temporary_specialist)" in findings[0]


def test_consultant_null_triggers_r_ppl_01():
    findings = _findings("consultant_null")
    assert len(findings) == 1
    assert "R-PPL-01" in findings[0]
    assert "(consultant)" in findings[0]


def test_end_date_key_absent_triggers_r_ppl_01():
    findings = _findings("end_date_key_absent")
    assert len(findings) == 1
    assert "R-PPL-01" in findings[0]
    assert "has no end_date" in findings[0]


def test_two_offenders_triggers_r_ppl_01_twice():
    findings = _findings("two_offenders")
    assert len(findings) == 2
    assert all("R-PPL-01" in f for f in findings)
