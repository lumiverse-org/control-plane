#!/usr/bin/env python3
"""AT-105 conformance assertion -- deletion-request completion evidence.

Master Spec v4.0 AT-105 (line 9375): "...the four timestamps, the named
executor and the subprocessor propagation checklist ... recorded in
records/deletion-requests/ ... within the declared deletion_sla_days".
schemas/records/deletion-request.schema.json (Section 97.2 line 8869)
additionally requires the backup carve-out policy statement.

L4-06-tasks.md Section 3, task L4-P2-24: "A deletion-request record
missing any one of the four timestamps, the executor, the checklist, or
the carve-out statement is rejected."

This module proves, against the golden valid fixture
tools/records/fixtures/valid/deletion-request.yaml and
schemas/records/deletion-request.schema.json:

  1. The fixture as written (every field present) validates cleanly --
     the positive case.
  2. A copy of that fixture with any ONE of the seven fields the
     criterion names removed -- requested, verified, executed, confirmed
     (the four timestamps), executor, subprocessor_checklist,
     backup_carve_out_statement -- is rejected by the schema. Seven
     negative cases, one per named field.

Usage: at105.py <CP_ROOT>

Deterministic output contract (L4-06-tasks.md Section 0.5): exactly one
final line on stdout, nothing else on a pass.
  AT-105 OK <n>      exit 0   the fixture validates and all n negative
                              cases were rejected
  AT-105 FAIL <n>    exit 1   at least one case did not behave as the
                              criterion requires (n = cases actually
                              exercised before the failure list)
  AT-105 ERROR <msg> exit 3   the module could not execute (missing
                              input, unreadable schema or fixture)
"""
import copy
import json
import pathlib
import sys

# Reuse the shared record validator's UTC-safe YAML loader (tools/records/
# lib/validate.py) instead of re-deriving it: plain yaml.safe_load would
# auto-convert the ISO8601 timestamp scalars in the fixture into datetime
# objects, which would make every field -- not just the seven under test --
# fail the schema's "type": "string" constraint.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "lib"))

try:
    from jsonschema import Draft202012Validator, RefResolver
    from validate import load_yaml  # noqa: E402  (tools/records/lib/validate.py)
except Exception as exc:  # pragma: no cover - fail-closed on a broken toolchain
    print("AT-105 ERROR import failed: %s" % exc)
    sys.exit(3)

# The seven fields AT-105 / L4-P2-24 name: the four timestamps, the named
# executor, the subprocessor propagation checklist, and the backup
# carve-out policy statement.
REQUIRED_FIELDS = [
    "requested",
    "verified",
    "executed",
    "confirmed",
    "executor",
    "subprocessor_checklist",
    "backup_carve_out_statement",
]


def _build_validator(cp_root):
    schema_dir = cp_root / "schemas" / "records"
    schema_path = schema_dir / "deletion-request.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    base = schema_dir.as_uri() + "/"
    store = {}
    for sibling in schema_dir.glob("*.json"):
        doc = json.loads(sibling.read_text(encoding="utf-8"))
        store[sibling.as_uri()] = doc
        store[sibling.name] = doc
    resolver = RefResolver(base_uri=base, referrer=schema, store=store)
    return Draft202012Validator(schema, resolver=resolver)


def main(argv):
    if len(argv) != 2:
        print("AT-105 ERROR usage: at105.py <CP_ROOT>")
        return 3
    cp_root = pathlib.Path(argv[1]).resolve()
    fixture_path = (
        cp_root / "tools" / "records" / "fixtures" / "valid" / "deletion-request.yaml"
    )
    try:
        validator = _build_validator(cp_root)
        golden = load_yaml(fixture_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print("AT-105 ERROR %s" % exc)
        return 3

    problems = []

    if list(validator.iter_errors(golden)):
        problems.append("golden fixture (every field present) was rejected")

    checked = 0
    for field in REQUIRED_FIELDS:
        if field not in golden:
            problems.append("golden fixture has no %r field to remove" % field)
            continue
        candidate = copy.deepcopy(golden)
        del candidate[field]
        checked += 1
        if not list(validator.iter_errors(candidate)):
            problems.append("missing %r was accepted, not rejected" % field)

    if problems:
        for p in problems:
            print("AT-105 DETAIL: %s" % p, file=sys.stderr)
        print("AT-105 FAIL %d" % checked)
        return 1

    print("AT-105 OK %d" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
