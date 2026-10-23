"""R-PPL-01 -- a non-employee person record with no end_date (Section 7.1,
invariant 58).

Section 7.1: "A CI check fails if a contractor, intern, temporary
specialist or consultant has a null end date." Those four tokens are
exactly the four non-"employee" values of the closed `employmentType`
enum in schemas/registry/common/defs.v1.schema.json
(["employee", "contractor", "intern", "temporary_specialist",
"consultant"]) -- so the check below tests `employment_type != "employee"`
directly rather than enumerating the four, and needs no change if the
enum is ever extended.

Standalone, directly-tested rule function -- see the module docstring of
r_svc_01.py (validators/registry/rules/r_svc_01.py, L1-404) for why this
is not wired into the frozen Option B (FD-094) R01-R18 dispatch table in
validators/registry/rules/registry.py. This mirrors the same adaptation
already made for r_ppl_05.py (L1-207): lanes/L1-05-tasks.md's own
SELF-VERIFY block for L1-203 runs this rule through
validators/registry/cli.py with the old "ERROR <rule> <file>:<pointer>
<message>" grammar -- that CLI invocation predates FD-094 and is
superseded by it. Fixtures still live exactly where the task says
(validators/registry/fixtures/ppl01/<case>/people.yaml), but
test_r_ppl_01.py exercises check() directly against a parsed people.yaml
document, exactly as test_r_ppl_05.py does for r_ppl_05.check.
"""
from __future__ import annotations

RULE_ID = "R-PPL-01"
SPEC = "Section 7.1"
APPLIES_TO = ["people"]


def _person_id(person: dict) -> str:
    return person.get("id", "<unknown-person>")


def check(people_doc: dict, as_of: str | None = None) -> list[str]:
    """Return one finding per non-employee person with a null or absent
    end_date. A person whose employment_type is the literal string
    "employee" is always exempt, regardless of end_date."""
    findings = []
    if not isinstance(people_doc, dict):
        return []

    people_list = people_doc.get("people")
    if isinstance(people_list, list):
        records = people_list
    else:
        records = [people_doc]

    for person in records:
        if not isinstance(person, dict):
            continue
        employment_type = person.get("employment_type")
        if employment_type is None and "id" not in person:
            continue
        if employment_type == "employee":
            continue
        if person.get("end_date") is None:
            findings.append(
                f"R-PPL-01 non-employee '{_person_id(person)}' "
                f"({employment_type}) has no end_date; Section 7.1"
            )
    return findings
