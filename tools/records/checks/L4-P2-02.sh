#!/usr/bin/env bash
set -euo pipefail
# Check: L4-P2-02 — schema toolchain, pinned deps, validate-schemas.sh --selftest
HERE="$(cd "$(dirname "$0")" && pwd)"
CP_DIR="$(cd "$HERE/../../.." && pwd)"
export CP_ROOT="$CP_DIR"
export L4_PY="${L4_PY:-C:/D_Drive/PS/MultiProduct/Code/.l4-venv/Scripts/python.exe}"
[ -x "$L4_PY" ] || L4_PY="python"

REQ="$CP_DIR/tools/records/requirements.txt"
LOADER="$CP_DIR/tools/records/lib/schemaload.py"
VS="$CP_DIR/tools/records/validate-schemas.sh"
[[ -f "$REQ" ]] || { echo "ABSENT: $REQ" >&2; exit 1; }
[[ -f "$LOADER" ]] || { echo "ABSENT: $LOADER" >&2; exit 1; }
[[ -f "$VS" ]] || { echo "ABSENT: $VS" >&2; exit 1; }

# Assertion 1: every requirements.txt line is pinned with an exact '=='.
while IFS= read -r LINE; do
  [[ -z "$LINE" || "$LINE" == \#* ]] && continue
  if [[ "$LINE" != *"=="* ]]; then
    echo "requirements.txt line not pinned with ==: $LINE" >&2
    exit 1
  fi
done < "$REQ"

# Positive: the real validate-schemas.sh --selftest passes against real fixtures.
bash "$VS" --selftest || { echo "--selftest failed" >&2; exit 1; }

# Assertion 2: the --selftest branch exists in validate-schemas.sh.
grep -q -- '--selftest' "$VS" || { echo "--selftest branch missing from validate-schemas.sh" >&2; exit 1; }

# Negative fixture (neg): the loader must reject the syntactically invalid
# schema fixture directly, independent of the --selftest wrapper above.
BAD="$CP_DIR/tools/records/fixtures/invalid/schemas/malformed.schema.json"
[[ -f "$BAD" ]] || { echo "ABSENT negative fixture: $BAD" >&2; exit 1; }
if "$L4_PY" "$LOADER" "$BAD" >/dev/null 2>&1; then
  echo "neg-fixture: loader unexpectedly accepted a syntactically invalid schema" >&2
  exit 1
fi

echo "CHECK L4-P2-02 PASS"
