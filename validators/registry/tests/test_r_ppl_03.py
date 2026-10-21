"""Tests for R-PPL-03 and R-PPL-08 (L1-205, Section 7.1 / Section 99.5).

Exercised by calling ``validators.registry.rules.r_ppl_03`` directly
against a parsed ``people.yaml`` fixture, rather than through
``validators/registry/cli.py`` -- see the module docstring of
``r_ppl_03.py`` and, for precedent, ``test_r_ppl_05.py`` / the module
docstrings of ``r_svc_01.py`` and ``r_prd_11.py``: FD-094 (DECIDED)
supersedes the CLI grammar and ``echo "EXIT=$?"`` acceptance commands
written into ``lanes/L1-05-tasks.md``.

6 test functions: 2 valid, 4 invalid, matching the task's own fixture-case
list exactly.
"""
import os

import yaml

from validators.registry.rules import r_ppl_03

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "ppl03")


def _load(case):
    path = os.path.join(FIXTURES_DIR, case, "people.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _findings(case):
    return r_ppl_03.check(_load(case))


# ---------------------------------------------------------------------------
# valid (2)
# ---------------------------------------------------------------------------


def test_valid_distinct_no_findings():
    case = os.path.join("valid", "distinct")
    assert _findings(case) == []


def test_valid_departed_retained_no_findings():
    # Section 7.1: "Departure is a state, not a deletion" -- a departed
    # record kept alongside a new, distinctly-id'd person is not a
    # collision.
    case = os.path.join("valid", "departed_retained")
    assert _findings(case) == []


# ---------------------------------------------------------------------------
# invalid (4)
# ---------------------------------------------------------------------------


def test_duplicate_id_triggers_r_ppl_03():
    findings = _findings("duplicate_id")
    assert len(findings) == 1
    assert "R-PPL-03" in findings[0]
    assert "'dev-a'" in findings[0]
    assert "identifiers are never reused (Section 7.1)" in findings[0]


def test_duplicate_login_triggers_r_ppl_08():
    findings = _findings("duplicate_login")
    assert len(findings) == 1
    assert "R-PPL-08" in findings[0]
    assert "exampledev-a" in findings[0]
    assert "'dev-a'" in findings[0]
    assert "'dev-b'" in findings[0]
    assert "claimed by both" in findings[0]


def test_duplicate_login_case_differs_triggers_r_ppl_08():
    # GitHub logins are case-insensitive; compare casefolded (Section 99.5).
    findings = _findings("duplicate_login_case_differs")
    assert len(findings) == 1
    assert "R-PPL-08" in findings[0]
    assert "claimed by both 'dev-a' and 'dev-b'" in findings[0]
    assert "exampledev-a" in findings[0]


def test_id_reused_after_departure_triggers_r_ppl_03():
    # Section 7.1: a departed person's id must never be reused, even by a
    # brand-new hire -- the same duplicate-id check as
    # test_duplicate_id_triggers_r_ppl_03, just with one of the two records
    # marked departed instead of both active.
    findings = _findings("id_reused_after_departure")
    assert len(findings) == 1
    assert "R-PPL-03" in findings[0]
    assert "'dev-a'" in findings[0]
