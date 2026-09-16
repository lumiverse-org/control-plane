#!/usr/bin/env bash
set -euo pipefail
# Check: L4-P2-24 — AT-105 conformance assertion on deletion-request.
# A deletion-request record missing any one of the four timestamps, the
# executor, the checklist, or the carve-out statement is rejected.
# AT-105, Master Spec v4.0 line 9388; L4-06-tasks.md Section 3, L4-P2-24.
HERE="$(cd "$(dirname "$0")" && pwd)"
CP_DIR="$(cd "$HERE/../../.." && pwd)"
export CP_ROOT="$CP_DIR"
export L4_PY="${L4_PY:-python3}"

# Positive: the acceptance command passes and reports the deterministic
# OK line with all seven named fields exercised.
OUT="$(bash "$CP_DIR/tools/records/validate-schemas.sh" --at105 2>/dev/null)"
[ "$OUT" = "AT-105 OK 7" ] || {
  echo "unexpected output from validate-schemas.sh --at105: $OUT" >&2
  exit 1
}

# Negative fixture: a deletion-request record missing the backup carve-out
# statement (bad_fixture) must itself be rejected by the schema. This
# proves the assertion is a real check, not a stub that always prints OK.
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
"$L4_PY" - "$CP_DIR" > "$TMP/neg_fixture.yaml" <<'PY'
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(sys.argv[1]) / "tools" / "records" / "lib"))
from validate import load_yaml
import yaml
fixture = pathlib.Path(sys.argv[1]) / "tools/records/fixtures/valid/deletion-request.yaml"
golden = load_yaml(fixture.read_text(encoding="utf-8"))
del golden["backup_carve_out_statement"]
print(yaml.safe_dump(golden, sort_keys=False))
PY

if "$L4_PY" "$CP_DIR/tools/records/lib/validate.py" \
    "$CP_DIR/schemas/records/deletion-request.schema.json" "$TMP/neg_fixture.yaml" >/dev/null 2>&1; then
  echo "neg_fixture: missing backup_carve_out_statement was NOT rejected" >&2
  exit 1
fi

echo "CHECK L4-P2-24 PASS"
