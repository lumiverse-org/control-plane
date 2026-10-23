"""R-PPL-03, R-PPL-08 -- duplicate person id and github_login (L1-205, Section 7.1 / Section 99.5).

Standalone, directly-tested rule functions -- see the module docstrings of
r_ppl_05.py and r_svc_01.py for why these are not wired into the frozen
Option B (FD-094) R01-R18 dispatch table in validators/registry/rules/registry.py.
The CLI grammar and per-fixture echo "EXIT=$?" acceptance commands written into
lanes/L1-05-tasks.md predate FD-094 and are superseded by it.

Rules covered:
* R-PPL-03 -- duplicate person id (Section 7.1).
* R-PPL-08 -- duplicate github_login, case-insensitive (Section 99.5).
"""
from __future__ import annotations

RULE_ID_DUPLICATE_ID = "R-PPL-03"
RULE_ID_DUPLICATE_LOGIN = "R-PPL-08"
SPEC = "Section 7.1; Section 99.5"
APPLIES_TO = ["people"]


def _person_id(person: dict) -> str:
    return person.get("id", "<unknown-person>")


def _get_records(people_doc: dict) -> list[dict]:
    if not isinstance(people_doc, dict):
        return []
    people_list = people_doc.get("people")
    if isinstance(people_list, list):
        return [p for p in people_list if isinstance(p, dict)]
    if "id" in people_doc or "github_login" in people_doc:
        return [people_doc]
    return []


def check_r_ppl_03(people_doc: dict) -> list[str]:
    """R-PPL-03 -- a duplicate person id. Every repeat occurrence beyond the
    first is reported (so a three-way collision on one id yields two
    findings, not one), mirroring check_r_ppl_08's per-collision reporting
    below. Availability/departure status is irrelevant here -- a departed
    record's id colliding with an active record's id is exactly the "id
    reused after departure" case Section 7.1 forbids, and is reported
    identically to two active records colliding."""
    findings = []
    seen_ids = set()
    for person in _get_records(people_doc):
        person_id = person.get("id")
        if person_id is None:
            continue
        if person_id in seen_ids:
            findings.append(
                f"R-PPL-03 duplicate person id '{person_id}'; identifiers "
                f"are never reused (Section 7.1)"
            )
        else:
            seen_ids.add(person_id)
    return findings


def check_r_ppl_08(people_doc: dict) -> list[str]:
    """R-PPL-08 -- two people claiming the same github_login. Comparison is
    casefolded (GitHub logins are case-insensitive; Section 99.5:
    "people.yaml keys on the GitHub login", so a collision breaks the
    identity bridge even when the two spellings differ only in case). The
    message reports the casefolded form of the login, and the first id to
    claim it before the id that collided with it."""
    findings = []
    seen_logins = {}  # casefolded login -> first person id that claimed it
    for person in _get_records(people_doc):
        login = person.get("github_login")
        if not isinstance(login, str):
            continue
        key = login.casefold()
        person_id = _person_id(person)
        if key in seen_logins:
            findings.append(
                f"R-PPL-08 github_login '{key}' claimed by both "
                f"'{seen_logins[key]}' and '{person_id}'"
            )
        else:
            seen_logins[key] = person_id
    return findings


def check(people_doc: dict) -> list[str]:
    """Run both rules and return the combined findings, in the order the
    task's own table names them: R-PPL-03, then R-PPL-08."""
    findings = []
    findings.extend(check_r_ppl_03(people_doc))
    findings.extend(check_r_ppl_08(people_doc))
    return findings
