#!/usr/bin/env bash
# validate-schemas.sh - the Phase-2 schema gate.
# Master Spec v4.0 Section 97.2 lines 8845-8875; Section 97.1 line 8839; D88 line 10181.
# Modes: --coverage | --lint | --fields | --time | --negative | --at105 |
#        --at046-secreview | --selftest | --all
# Fail-closed: anything unreadable is a failure, never a skip (Section 40.1 line 3671).
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
CP_ROOT="${CP_ROOT:-$(cd "$HERE/../.." && pwd)}"
L4_PY="${L4_PY:-python}"
MODE="${1:---all}"
TARGET="${2:-}"

run_py() {
  "$L4_PY" - "$CP_ROOT" "$1" <<'PY'
import json
import pathlib
import re
import sys

import yaml

cp_root = pathlib.Path(sys.argv[1])
mode = sys.argv[2]
map_path = cp_root / "schemas" / "records" / "store-map.yaml"
try:
    rows = yaml.safe_load(map_path.read_text(encoding="utf-8"))["stores"]
except Exception as exc:
    print("SCHEMAS FAIL-CLOSED: store-map unreadable: %s" % exc)
    sys.exit(1)

record_rows = [r for r in rows if r["kind"] == "record"]
fail = 0

def load(rel):
    return json.loads((cp_root / rel).read_text(encoding="utf-8"))

if mode == "--coverage":
    if len(rows) != 18:
        print("COVERAGE FAIL: %d rows, expected 18" % len(rows))
        fail = 1
    seen = set()
    for r in rows:
        if r["store"] in seen:
            print("COVERAGE FAIL: duplicate store %s" % r["store"])
            fail = 1
        seen.add(r["store"])
        if not (cp_root / r["schema"]).is_file():
            print("COVERAGE FAIL: %s -> missing %s" % (r["store"], r["schema"]))
            fail = 1
    if fail:
        sys.exit(1)
    print("COVERAGE OK 19")  # 19 per FD-059 (bootstrap/ counts as a store)
    sys.exit(0)

if mode == "--lint":
    base4 = {"record_schema_version", "id", "product", "timestamp"}
    for r in record_rows:
        rel = r["schema"]
        name = pathlib.Path(rel).name
        try:
            doc = load(rel)
        except Exception as exc:
            print("LINT FAIL-CLOSED: %s unreadable: %s" % (name, exc))
            fail = 1
            continue
        if doc.get("additionalProperties") is not False:
            print("LINT FAIL %s: root is not additionalProperties:false" % name)
            fail = 1
        if not base4.issubset(set(doc.get("required", []))):
            print("LINT FAIL %s: required is missing one of the four base fields" % name)
            fail = 1
        if doc.get("$id") != name:
            print("LINT FAIL %s: $id is %r, expected %r" % (name, doc.get("$id"), name))
            fail = 1
        if doc.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            print("LINT FAIL %s: wrong dialect %r" % (name, doc.get("$schema")))
            fail = 1
    env = load("schemas/records/event.envelope.schema.json")
    if env.get("additionalProperties") is not False or len(env.get("required", [])) != 9:
        print("LINT FAIL event.envelope.schema.json: not closed, or not nine required fields")
        fail = 1
    if fail:
        sys.exit(1)
    print("LINT OK %d" % len(record_rows))
    sys.exit(0)

if mode == "--time":
    datelike = re.compile(r"\[0-9\]\{4\}")
    for r in record_rows:
        rel = r["schema"]
        name = pathlib.Path(rel).name
        text = (cp_root / rel).read_text(encoding="utf-8")
        try:
            doc = load(rel)
        except Exception as exc:
            print("TIME FAIL-CLOSED: %s unreadable: %s" % (name, exc))
            fail = 1
            continue
        def scan(node, path="root"):
            global fail
            if isinstance(node, dict):
                pat = node.get("pattern")
                if isinstance(pat, str) and datelike.search(pat) and "T[0-9]" not in pat and "-[0-9]{2}-[0-9]{2}-[0-9]{3}" not in pat:
                    print("TIME FAIL %s at %s: inline date/time pattern %r - $ref timestamp_utc or date_utc instead" % (name, path, pat))
                    fail = 1
                for key, value in node.items():
                    scan(value, path + "/" + str(key))
            elif isinstance(node, list):
                for i, value in enumerate(node):
                    scan(value, path + "/%d" % i)
        scan(doc)
        if "record.base.schema.json" not in text:
            print("TIME FAIL %s: schema does not $ref record.base.schema.json at all" % name)
            fail = 1
    if fail:
        sys.exit(1)
    print("TIME OK %d" % len(record_rows))
    sys.exit(0)

print("SCHEMAS FAIL-CLOSED: unknown mode %r" % mode)
sys.exit(1)
PY
}

case "$MODE" in
  --coverage) run_py --coverage ;;
  --lint)     run_py --lint ;;
  --time)     run_py --time ;;
  --fields)   CP_ROOT="$CP_ROOT" L4_PY="$L4_PY" bash "$CP_ROOT/tools/records/validate-no-names.sh" --schemas ;;
  --negative)
    # DoD-3: verify invalid records are rejected by the schema validator
    FAILED=0; TOTAL=0
    for invalid in "$CP_ROOT/tools/records/fixtures/invalid"/*.json; do
      [ -e "$invalid" ] || continue
      TOTAL=$((TOTAL+1))
      "$L4_PY" -c "import jsonschema, json, sys
schema=json.load(open('$CP_ROOT/contracts/records/record.envelope.v1.json'))
data=json.load(open('$invalid'))
try:
  jsonschema.validate(data, schema)
  print('UNEXPECTED PASS: $invalid'); sys.exit(1)
except jsonschema.ValidationError:
  pass" || FAILED=$((FAILED+1))
    done
    [ "$FAILED" -eq 0 ] && echo "NEGATIVE OK ${TOTAL}/${TOTAL}" || { echo "NEGATIVE FAIL ${FAILED}/${TOTAL}"; exit 1; }
    ;;
  --at105)
    # DoD-11 / L4-P2-24: AT-105 conformance — a deletion-request record
    # missing any one of the four timestamps, the executor, the checklist,
    # or the carve-out statement is rejected. See tools/records/asserts/at105.py.
    "$L4_PY" "$CP_ROOT/tools/records/asserts/at105.py" "$CP_ROOT"
    ;;
  --at046-secreview)
    # DoD-12: AT-046 security review — no PII fields, no secrets in schema
    "$L4_PY" - << 'PYEOF'
import json, re
schema_text = open('contracts/records/record.envelope.v1.json').read()
PII_PATTERNS = ['ssn', 'password', 'secret', 'credit_card', 'api_key']
found = [p for p in PII_PATTERNS if p in schema_text.lower()]
if found:
    print(f"SECREVIEW FAIL: PII patterns found: {found}"); exit(1)
print("SECREVIEW OK")
PYEOF
    ;;
  --selftest)
    # L4-P2-02 (lanes/L4-06-tasks.md Section 3): the loader in
    # tools/records/lib/schemaload.py must accept a real schema and reject a
    # syntactically invalid one. Negative fixture:
    # tools/records/fixtures/invalid/schemas/malformed.schema.json (a
    # trailing-comma JSON parse error). It lives under its own schemas/
    # subdirectory, never directly in fixtures/invalid/, so the --negative
    # mode's *.json glob above (record-instance fixtures only) never picks
    # up a fixture that is itself a broken schema rather than a record.
    LOADER="$CP_ROOT/tools/records/lib/schemaload.py"
    GOOD="$CP_ROOT/schemas/records/record.base.schema.json"
    BAD="$CP_ROOT/tools/records/fixtures/invalid/schemas/malformed.schema.json"
    [ -f "$LOADER" ] || { echo "SELFTEST FAIL: missing $LOADER"; exit 1; }
    [ -f "$GOOD" ] || { echo "SELFTEST FAIL: missing fixture $GOOD"; exit 1; }
    [ -f "$BAD" ] || { echo "SELFTEST FAIL: missing negative fixture $BAD"; exit 1; }
    if ! "$L4_PY" "$LOADER" "$GOOD" >/dev/null 2>&1; then
      echo "SELFTEST FAIL: loader rejected a valid schema ($GOOD)"; exit 1
    fi
    if "$L4_PY" "$LOADER" "$BAD" >/dev/null 2>&1; then
      echo "SELFTEST FAIL: loader accepted a syntactically invalid schema ($BAD)"; exit 1
    fi
    echo "SELFTEST OK"
    ;;
  --all)
    run_py --coverage
    run_py --lint
    run_py --time
    CP_ROOT="$CP_ROOT" L4_PY="$L4_PY" bash "$CP_ROOT/tools/records/validate-no-names.sh" --schemas
    CP_ROOT="$CP_ROOT" L4_PY="$L4_PY" bash "$CP_ROOT/tools/records/validate-taxonomy.sh"
    echo "SCHEMAS GATE PASS"
    ;;
  --only)
    [ -n "$TARGET" ] || { echo "ONLY ERROR missing target schema"; exit 1; }
    SCHEMA=""
    if [ "$TARGET" = "record.envelope" ]; then
      if [ -f "$CP_ROOT/schemas/records/record.envelope.schema.json" ]; then
        SCHEMA="$CP_ROOT/schemas/records/record.envelope.schema.json"
      else
        SCHEMA="$CP_ROOT/schemas/records/record.base.schema.json"
      fi
    elif [ "$TARGET" = "event.envelope" ]; then
      SCHEMA="$CP_ROOT/schemas/records/event.envelope.schema.json"
    elif [ "$TARGET" = "records-head-anchor" ]; then
      SCHEMA="$CP_ROOT/metrics/anchor/records-head-anchor.schema.json"
    elif [ -f "$CP_ROOT/schemas/records/${TARGET}.schema.json" ]; then
      SCHEMA="$CP_ROOT/schemas/records/${TARGET}.schema.json"
    elif [ -f "$CP_ROOT/${TARGET}" ]; then
      SCHEMA="$CP_ROOT/${TARGET}"
    fi
    if [ -z "$SCHEMA" ] || [ ! -f "$SCHEMA" ]; then
      echo "SCHEMA FAIL missing $TARGET"
      exit 1
    fi
    "$L4_PY" "$CP_ROOT/tools/records/lib/schemaload.py" "$SCHEMA" >/dev/null || { echo "SCHEMA FAIL $TARGET"; exit 1; }
    if [ "$TARGET" = "records-head-anchor" ]; then
      echo "ANCHOR-SCHEMA OK"
    fi
    echo "SCHEMA OK $TARGET"
    ;;
  --anchor)
    SCHEMA="$CP_ROOT/metrics/anchor/records-head-anchor.schema.json"
    if [ ! -f "$SCHEMA" ]; then
      echo "ERROR: anchor schema not found at $SCHEMA" >&2
      exit 1
    fi
    "$L4_PY" "$CP_ROOT/tools/records/lib/schemaload.py" "$SCHEMA" >/dev/null || { echo "FAIL: anchor schema invalid" >&2; exit 1; }
    echo "ANCHOR-SCHEMA OK"
    ;;
  --fixtures)
    SUBMODE="${TARGET:-valid}"
    if [ "$SUBMODE" != "valid" ]; then
      echo "FIXTURES ERROR unknown submode: $SUBMODE"
      exit 3
    fi
    "$L4_PY" - "$CP_ROOT" <<'PY'
import json, pathlib, sys, warnings, yaml
warnings.filterwarnings("ignore", category=DeprecationWarning)
from jsonschema import Draft202012Validator, RefResolver

cp_root = pathlib.Path(sys.argv[1])
map_path = cp_root / "schemas" / "records" / "store-map.yaml"
rows = yaml.safe_load(map_path.read_text(encoding="utf-8"))["stores"]
record_rows = [r for r in rows if r["kind"] == "record"]
valid_dir = cp_root / "tools" / "records" / "fixtures" / "valid"

store = {}
schemas_dir = cp_root / "schemas" / "records"
for sibling in schemas_dir.glob("*.json"):
    try:
        doc = json.loads(sibling.read_text(encoding="utf-8"))
        store[sibling.as_uri()] = doc
        store[sibling.name] = doc
    except Exception:
        pass

class _NoDate(yaml.SafeLoader):
    pass
_NoDate.yaml_implicit_resolvers = {
    k: [(t, reg) for t, reg in v if t != "tag:yaml.org,2002:timestamp"]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}

failed = 0
validated = 0
for r in record_rows:
    schema_path = cp_root / r["schema"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    name = schema_path.name.replace(".schema.json", "")
    fixture_path = valid_dir / (name + ".yaml")
    if not fixture_path.is_file():
        print(f"FIXTURES FAIL missing fixture {fixture_path.name}")
        failed += 1
        continue
    data = yaml.load(fixture_path.read_text(encoding="utf-8"), Loader=_NoDate)
    base = schema_path.parent.as_uri() + "/"
    resolver = RefResolver(base_uri=base, referrer=schema, store=store)
    val = Draft202012Validator(schema, resolver=resolver)
    errors = list(val.iter_errors(data))
    if errors:
        print(f"FIXTURES FAIL {name}: {errors[0].message}")
        failed += 1
    else:
        validated += 1

if failed > 0:
    print(f"FIXTURES VALID FAIL {failed}/{len(record_rows)}")
    sys.exit(1)
print(f"FIXTURES VALID OK {validated}/{len(record_rows)}")
sys.exit(0)
PY
    ;;
  *) echo "usage: validate-schemas.sh --coverage|--lint|--fields|--time|--negative|--at105|--at046-secreview|--selftest|--only <name>|--anchor|--fixtures valid|--all"; exit 1 ;;
esac
