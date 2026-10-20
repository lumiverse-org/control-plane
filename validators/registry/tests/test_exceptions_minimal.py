"""Tests for schemas/registry/exceptions.v1.minimal.schema.json and R-EXC-00
(L1-108, the week-one minimal `exceptions.yaml` validator).

Validates fixtures directly with `jsonschema` and calls
`validators.registry.rules.r_exc_min` directly, rather than the L1-005
discover()/RULE_ID/APPLIES_TO harness (never built here -- validators/
registry/harness.py and validators/registry/RULES.md do not exist in this
repository; see this module's own docstring note below) or the
pre-FD-094 "OK: N file(s) validated" / "ERROR <rule>" CLI grammar in
lanes/L1-05-tasks.md. FD-094 (DECIDED, PENDING_FOUNDER_DECISIONS.md)
supersedes both in favour of Option B (validators/registry/cli.py,
R01-R18) -- the same adaptation already made for L1-601
(test_exceptions_full_schema.py), L1-404 (test_service_schema.py) and
L1-606 (test_tools_schema.py). Fixtures still live at
validators/registry/fixtures/exceptions/<case>/exceptions.yaml exactly as
the task specifies.

9 test functions, one per fixture case, matching the task's own case
table (2 valid + 7 invalid).

Deviations from the task's literal text, required to implement it
faithfully rather than fake a pass:

1. `validators/registry/RULES.md` does not exist in this repository.
   L1-005 (`validators/registry/rules/__init__.py`'s `discover()`,
   `validators/registry/harness.py`, `validators/registry/RULES.md`) was
   superseded by FD-094 before it landed -- checked directly:
   `rules/__init__.py` is empty and `harness.py` is absent. No task since
   (L1-201, L1-202, ..., L1-601) has recreated `RULES.md` or appended to
   it; each instead documents its rule in its own module/test docstring,
   exactly as this one does. L1-108's GIT POSTAMBLE instruction to append
   an `R-EXC-00` row to `RULES.md` is therefore not carried out -- there
   is no file to append to, and authoring one from scratch here would be
   scope this task's own FILES list does not list and no other task in
   this cluster has taken on.

2. R-EXC-00 (`r_exc_min.py`) is a standalone rule function, not wired
   into the frozen Option B `R01`..`R18` dispatch table
   (`validators/registry/rules/registry.py`) -- `contracts/
   validator-contract.md` freezes that catalogue ("Any change to this
   interface requires a new FD entry"), exactly as `r_tol_01.py` and
   `r_svc_01.py` already reason for their own rule ids. Consequently
   `python -m validators.registry.cli --root . --as-of <date>
   --records-root . --format json` does not run R-EXC-00 and cannot
   produce the task's literal `ERROR R-EXC-00 ...` / `MALFORMED_EXIT=1`
   CLI output -- verified directly: that command's actual current output
   is `{"status": "PASS", "rules_run": 18, "findings": [...R13 WARNs...]}`
   both before and after this task's files exist, because R13 only scans
   registry *directories* for emptiness (it skips files, so the new
   top-level `registries/exceptions.yaml` -- a sibling of the pre-existing
   `registries/exceptions/` directory -- is invisible to it) and R07/R18
   only glob `registries/exceptions/*.yaml`, never the new top-level file.
   The substance of the task's expected line -- the exact message text
   `ERROR R-EXC-00 <path>:/exceptions/<n> exception <id> has no expiry;
   invariant 77` -- is genuinely produced and asserted below
   (`test_no_expiry`), just via `r_exc_min.check_document` directly
   rather than through the frozen CLI end-to-end.
"""
import json
import os

import jsonschema
import yaml
from referencing import Registry, Resource

from validators.registry.rules import r_exc_min

SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "schemas", "registry")
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "exceptions")


def _registry():
    defs_path = os.path.join(SCHEMAS_DIR, "common", "defs.v1.schema.json")
    min_path = os.path.join(SCHEMAS_DIR, "exceptions.v1.minimal.schema.json")
    with open(defs_path, encoding="utf-8") as f:
        defs_schema = json.load(f)
    with open(min_path, encoding="utf-8") as f:
        min_schema = json.load(f)
    reg = Registry().with_resources(
        [
            ("common/defs.v1.schema.json", Resource.from_contents(defs_schema)),
            (min_schema["$id"], Resource.from_contents(min_schema)),
        ]
    )
    return min_schema, reg


def _fixture_path(case):
    return os.path.join(FIXTURES_DIR, case, "exceptions.yaml")


def _load_fixture(case):
    with open(_fixture_path(case), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _errors_for(case):
    schema, reg = _registry()
    validator = jsonschema.Draft202012Validator(schema, registry=reg)
    doc = _load_fixture(case)
    return list(validator.iter_errors(doc))


# ---- valid cases (2) -------------------------------------------------------


def test_valid_bootstrap_minimal():
    case = os.path.join("valid", "bootstrap_minimal")
    assert _errors_for(case) == []
    passed, findings = r_exc_min.check_document(_load_fixture(case))
    assert (passed, findings) == (True, [])


def test_valid_empty():
    case = os.path.join("valid", "empty")
    assert _errors_for(case) == []
    passed, findings = r_exc_min.check_document(_load_fixture(case))
    assert (passed, findings) == (True, [])


# ---- invalid cases (7) ------------------------------------------------------


def test_no_expiry():
    # The "deliberately malformed exception" Section 98.2's Phase-1
    # completion check names -- R-EXC-00's own dedicated check, invariant 77.
    case = "no_expiry"
    doc = _load_fixture(case)
    # Also schema-invalid: `expiry` is a required property.
    assert len(_errors_for(case)) > 0
    passed, findings = r_exc_min.check_document(
        doc, source="validators/registry/fixtures/exceptions/no_expiry/exceptions.yaml"
    )
    assert passed is False
    assert findings == [
        "ERROR R-EXC-00 validators/registry/fixtures/exceptions/no_expiry/exceptions.yaml"
        ":/exceptions/0 exception EXC-2026-001 has no expiry; invariant 77"
    ]


def test_no_owner():
    assert len(_errors_for("no_owner")) > 0


def test_no_trigger_key():
    assert len(_errors_for("no_trigger_key")) > 0


def test_bad_id_format():
    assert len(_errors_for("bad_id_format")) > 0


def test_bad_type():
    assert len(_errors_for("bad_type")) > 0


def test_expiry_not_date():
    assert len(_errors_for("expiry_not_date")) > 0


def test_missing_version():
    assert len(_errors_for("missing_version")) > 0
