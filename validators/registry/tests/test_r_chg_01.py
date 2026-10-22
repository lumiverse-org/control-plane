"""Tests for R-CHG-01, R-CHG-02, R-CHG-03 and diffcheck.py (task L1-504,
Section 26.4; Section 11.2).

Directly tests check_document() against loaded fixture pairs -- see
test_r_inv_01.py and test_exceptions_minimal.py for the FD-094 Option B
precedent.

15 test functions: 7 valid, 8 invalid, matching the task table exactly.
"""
import os

import yaml

from validators.registry import diffcheck
from validators.registry.rules import r_chg_01, r_chg_02, r_chg_03

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "chg01")


def _case_dir(*parts):
    return os.path.join(FIXTURES_DIR, *parts)


def _load_yaml(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _pair(case_dir, filename):
    """(base_doc_or_None, head_doc_or_None) for one filename in a case dir."""
    return (
        _load_yaml(os.path.join(case_dir, "base", filename)),
        _load_yaml(os.path.join(case_dir, filename)),
    )


def _commit_message(case_dir):
    path = os.path.join(case_dir, "commit.txt")
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# valid cases (7)
# ---------------------------------------------------------------------------


def test_valid_no_delta():
    case = _case_dir("valid", "no_delta")
    base, head = _pair(case, "people.yaml")
    msg = _commit_message(case)
    assert r_chg_01.check_document(base, head, msg) == (True, [])
    assert r_chg_03.check_document(base, head, msg) == (True, [])


def test_valid_capability_added_with_trailer():
    case = _case_dir("valid", "capability_added_with_trailer")
    base, head = _pair(case, "people.yaml")
    msg = _commit_message(case)
    assert r_chg_01.check_document(base, head, msg) == (True, [])


def test_valid_access_status_changed_with_trailer():
    case = _case_dir("valid", "access_status_changed_with_trailer")
    base, head = _pair(case, "people.yaml")
    msg = _commit_message(case)
    assert r_chg_03.check_document(base, head, msg) == (True, [])


def test_valid_assignment_added_with_trailer():
    case = _case_dir("valid", "assignment_added_with_trailer")
    base, head = _pair(case, "product.yaml")
    msg = _commit_message(case)
    assert r_chg_02.check_document(base, head, msg) == (True, [])


def test_valid_capability_removed_no_trailer():
    case = _case_dir("valid", "capability_removed_no_trailer")
    base, head = _pair(case, "people.yaml")
    msg = _commit_message(case)
    assert r_chg_01.check_document(base, head, msg) == (True, [])


def test_valid_no_base_is_silent():
    case = _case_dir("valid", "no_base_is_silent")
    assert not os.path.isdir(os.path.join(case, "base"))
    head = _load_yaml(os.path.join(case, "people.yaml"))
    msg = _commit_message(case)
    assert r_chg_01.check_document(None, head, msg) == (True, [])


def test_valid_non_write_assignment_added():
    case = _case_dir("valid", "non_write_assignment_added")
    base, head = _pair(case, "product.yaml")
    msg = _commit_message(case)
    assert r_chg_02.check_document(base, head, msg) == (True, [])


# ---------------------------------------------------------------------------
# invalid cases (8)
# ---------------------------------------------------------------------------


def test_capability_added_role_no_trailer():
    case = _case_dir("capability_added_role_no_trailer")
    base, head = _pair(case, "roles.yaml")
    msg = _commit_message(case)
    passed, findings = r_chg_01.check_document(base, head, msg)
    assert passed is False
    assert len(findings) == 1
    assert "R-CHG-01" in findings[0]


def test_capability_added_person_no_trailer():
    case = _case_dir("capability_added_person_no_trailer")
    base, head = _pair(case, "people.yaml")
    msg = _commit_message(case)
    passed, findings = r_chg_01.check_document(base, head, msg)
    assert passed is False
    assert len(findings) == 1
    assert "R-CHG-01" in findings[0]


def test_assignment_write_added_no_trailer():
    case = _case_dir("assignment_write_added_no_trailer")
    base, head = _pair(case, "product.yaml")
    msg = _commit_message(case)
    passed, findings = r_chg_02.check_document(base, head, msg)
    assert passed is False
    assert len(findings) == 1
    assert "R-CHG-02" in findings[0]


def test_access_status_changed_no_trailer():
    case = _case_dir("access_status_changed_no_trailer")
    base, head = _pair(case, "people.yaml")
    msg = _commit_message(case)
    passed, findings = r_chg_03.check_document(base, head, msg)
    assert passed is False
    assert len(findings) == 1
    assert "R-CHG-03" in findings[0]


def test_malformed_trailer():
    case = _case_dir("malformed_trailer")
    base, head = _pair(case, "people.yaml")
    msg = _commit_message(case)
    assert diffcheck.linked_decision_records(msg) == []
    passed, findings = r_chg_01.check_document(base, head, msg)
    assert passed is False
    assert len(findings) == 1


def test_trailer_wrong_id_format():
    case = _case_dir("trailer_wrong_id_format")
    base, head = _pair(case, "people.yaml")
    msg = _commit_message(case)
    assert diffcheck.linked_decision_records(msg) == []
    passed, findings = r_chg_01.check_document(base, head, msg)
    assert passed is False
    assert len(findings) == 1


def test_three_deltas_no_trailer():
    case = _case_dir("three_deltas_no_trailer")
    base_p, head_p = _pair(case, "people.yaml")
    base_prod, head_prod = _pair(case, "product.yaml")
    msg = _commit_message(case)

    p1, f1 = r_chg_01.check_document(base_p, head_p, msg)
    p2, f2 = r_chg_02.check_document(base_prod, head_prod, msg)
    p3, f3 = r_chg_03.check_document(base_p, head_p, msg)

    assert p1 is False
    assert p2 is False
    assert p3 is False

    all_findings = f1 + f2 + f3
    assert any("R-CHG-01" in f for f in all_findings)
    assert any("R-CHG-02" in f for f in all_findings)
    assert any("R-CHG-03" in f for f in all_findings)


def test_bootstrap_mode_still_binding():
    case = _case_dir("bootstrap_mode_still_binding")
    base, head = _pair(case, "people.yaml")
    msg = _commit_message(case)
    passed, findings = r_chg_01.check_document(base, head, msg)
    assert passed is False
    assert len(findings) == 1
    assert "R-CHG-01" in findings[0]
