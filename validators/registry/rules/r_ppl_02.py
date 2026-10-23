"""R-PPL-02, R-PPL-06, R-PPL-07 -- `availability` x `access_status` pair legality
(L1-204, Section 7.1).

Standalone, directly-tested rule functions -- see the module docstring of
``r_svc_01.py`` and ``r_ppl_05.py`` for why these are not wired into the
frozen Option B (FD-094) ``R01``..``R18`` dispatch table in
``validators/registry/rules/registry.py``. The CLI grammar and per-fixture
``echo "EXIT=$?"`` acceptance commands written into ``lanes/L1-05-tasks.md``
predate FD-094 and are superseded by it, exactly as already documented for
R-PPL-05/09/10/11/12 and R-SVC-01..03.

Rules covered:
* R-PPL-02 -- departed implies revoked (Section 7.1).
* R-PPL-06 -- revoked implies departed, or a non-employee past end_date (Section 7.1).
* R-PPL-07 -- suspended is valid only with active or on_leave (Section 7.1).
"""
from __future__ import annotations

from datetime import date

RULE_ID_PAIR_LEGALITY = "R-PPL-02"
RULE_ID_REVOKED_WITHOUT_DEPARTED = "R-PPL-06"
RULE_ID_SUSPENDED_OUTSIDE_ACTIVE = "R-PPL-07"
SPEC = "Section 7.1"
APPLIES_TO = ["people"]


def _person_id(person: dict) -> str:
    return person.get("id", "<unknown-person>")


def _parse_today(today) -> date | None:
    """Return a date, or None if `today` cannot be parsed. Callers must
    fail closed on None (see check_r_ppl_06)."""
    if isinstance(today, date):
        return today
    try:
        return date.fromisoformat(str(today))
    except (TypeError, ValueError):
        return None


def _get_records(people_doc: dict) -> list[dict]:
    if not isinstance(people_doc, dict):
        return []
    people_list = people_doc.get("people")
    if isinstance(people_list, list):
        return [p for p in people_list if isinstance(p, dict)]
    if "availability" in people_doc or "access_status" in people_doc:
        return [people_doc]
    return []


def check_r_ppl_02(people_doc: dict) -> list[str]:
    """R-PPL-02 -- departed implies revoked."""
    findings = []
    for person in _get_records(people_doc):
        if person.get("availability") != "departed":
            continue
        if person.get("access_status") != "revoked":
            findings.append(
                f"R-PPL-02 departed person '{_person_id(person)}' must have "
                f"access_status revoked; Section 7.1"
            )
    return findings


def check_r_ppl_06(people_doc: dict, today) -> list[str]:
    """R-PPL-06 -- revoked implies departed, or a non-employee past end_date."""
    today_date = _parse_today(today)
    findings = []
    for person in _get_records(people_doc):
        if person.get("access_status") != "revoked":
            continue
        if person.get("availability") == "departed":
            continue  # satisfied directly
        employment_type = person.get("employment_type")
        end_date = person.get("end_date")
        non_employee_past_end_date = False
        if employment_type != "employee" and end_date is not None and today_date is not None:
            try:
                non_employee_past_end_date = date.fromisoformat(str(end_date)) < today_date
            except ValueError:
                non_employee_past_end_date = False
        # Fail closed: an unparseable `today`, or a non-employee with no
        # end_date, never satisfies the carve-out -- the rule still fires.
        if not non_employee_past_end_date:
            findings.append(
                f"R-PPL-06 revoked person '{_person_id(person)}' is neither "
                f"departed nor a non-employee past end_date; Section 7.1"
            )
    return findings


def check_r_ppl_07(people_doc: dict) -> list[str]:
    """R-PPL-07 -- suspended is valid only with active or on_leave."""
    findings = []
    for person in _get_records(people_doc):
        if person.get("access_status") != "suspended":
            continue
        if person.get("availability") not in ("active", "on_leave"):
            findings.append(
                f"R-PPL-07 suspended person '{_person_id(person)}' must be "
                f"active or on_leave; Section 7.1"
            )
    return findings


def check(people_doc: dict, today) -> list[str]:
    """Run all three rules in the task's own table order and return the
    combined findings: R-PPL-02, R-PPL-06, R-PPL-07."""
    findings = []
    findings.extend(check_r_ppl_02(people_doc))
    findings.extend(check_r_ppl_06(people_doc, today))
    findings.extend(check_r_ppl_07(people_doc))
    return findings
