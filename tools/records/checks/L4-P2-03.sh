#!/usr/bin/env bash
set -euo pipefail
# Check: L4-P2-03 -- UTC-with-offset timestamp definition and its negative case.
# Master Spec v4.0 Section 97.1 line 8839: "Every record and event timestamp is
# stored in UTC with its offset." Concordance body: L4-T202 in
# L4-02-record-schemas.md, which ships $defs.timestamp_utc in
# schemas/records/record.base.schema.json and proves the negative case
# (a naive local time is rejected) in that task's own SELF-VERIFY (NEGTIME).
CP_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
export CP_ROOT="$CP_DIR"
export L4_PY="${L4_PY:-python}"

BASE="$CP_DIR/schemas/records/record.base.schema.json"
PROBE_SCHEMA="$CP_DIR/schemas/records/record.probe.schema.json"
VALIDATOR="$CP_DIR/tools/records/lib/validate.py"
[[ -f "$BASE" ]] || { echo "ABSENT: $BASE" >&2; exit 1; }
[[ -f "$PROBE_SCHEMA" ]] || { echo "ABSENT: $PROBE_SCHEMA" >&2; exit 1; }
[[ -f "$VALIDATOR" ]] || { echo "ABSENT: $VALIDATOR" >&2; exit 1; }

# Positive: timestamp_utc def exists and carries the UTC-with-offset pattern.
grep -q '"timestamp_utc"' "$BASE" || { echo "timestamp_utc def missing from record.base.schema.json" >&2; exit 1; }
grep -qF '(Z|\\+00:00)' "$BASE" || { echo "timestamp_utc pattern is not UTC-with-offset" >&2; exit 1; }

# Positive: the lane's own schema gate agrees every store schema resolves
# through the shared timestamp_utc/date_utc defs rather than an inline pattern.
bash "$CP_DIR/tools/records/validate-schemas.sh" --time | grep -Eq '^TIME OK [0-9]+$' \
  || { echo "validate-schemas.sh --time did not report TIME OK" >&2; exit 1; }

# Negative fixture (neg_fixture): a naive local time -- no Z, no numeric offset --
# must be rejected by the validator against the timestamp_utc-backed probe schema.
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
NEG_FIXTURE="$TMP/neg_fixture-naive-local-time.yaml"
cat > "$NEG_FIXTURE" <<'YAML'
record_schema_version: 1
id: INC-2026-09-14-001
product: solvox
timestamp: 2026-09-14 02:11:00 IST
YAML
if "$L4_PY" "$VALIDATOR" "$PROBE_SCHEMA" "$NEG_FIXTURE" >/dev/null 2>&1; then
  echo "neg-fixture: naive local timestamp was accepted, expected rejection" >&2
  exit 1
fi

echo "CHECK L4-P2-03 PASS"
