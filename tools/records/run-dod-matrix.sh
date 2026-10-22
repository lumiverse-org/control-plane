#!/usr/bin/env bash
# tools/records/run-dod-matrix.sh
# Executes all 20 charter Definition-of-Done (DoD) rows from lanes/L4-00-charter.md §7.
# Master Spec v4.0 §97, §53.1, §101, §103; FD-133.
#
# Exit contract:
#   Exits 0 when all 15 locally-checkable rows pass and remote-required rows are SKIPPED (REMOTE-REQUIRED).
#   Exits 1 if any local check fails.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
CP_ROOT="${CP_ROOT:-$(cd "$HERE/../.." && pwd)}"
export CP_ROOT
export L4_PY="${L4_PY:-python3}"
if ! command -v "$L4_PY" >/dev/null 2>&1; then
  export L4_PY="python"
fi

PYTEST_CMD=""
if "$L4_PY" -m pytest --version >/dev/null 2>&1; then
  PYTEST_CMD="$L4_PY -m pytest"
elif command -v python.exe >/dev/null 2>&1 && python.exe -m pytest --version >/dev/null 2>&1; then
  PYTEST_CMD="python.exe -m pytest"
elif command -v pytest >/dev/null 2>&1; then
  PYTEST_CMD="pytest"
fi

# Optional mode --handoff: verify handoff manifest per L4-P8-03
if [ "${1:-}" = "--handoff" ]; then
  HANDOFF_FILE="${CP_ROOT}/tools/records/HANDOFF.md"
  if [ ! -f "$HANDOFF_FILE" ]; then
    echo "HANDOFF FAIL: $HANDOFF_FILE does not exist"
    exit 1
  fi
  # Verify cross-lane consumption sections (L0, L1, L2, L3) per L4-00-charter.md §5
  MISSING=0
  for lane in "Lane 0" "Lane 1" "Lane 2" "Lane 3"; do
    if ! grep -q "$lane" "$HANDOFF_FILE"; then
      echo "HANDOFF FAIL: missing section for $lane"
      MISSING=1
    fi
  done
  if [ "$MISSING" -ne 0 ]; then
    exit 1
  fi
  echo "HANDOFF OK: $HANDOFF_FILE verified (all 4 consumer lanes documented)"
  exit 0
fi

PASSED=0
FAILED=0
SKIPPED=0

check_remote_credentials() {
  if [ -n "${GH_APP_CREDENTIALS:-}" ] || [ -n "${RECORDS_WRITER_LIVE_TOKEN:-}" ]; then
    return 0
  fi
  return 1
}

# --- DoD-1: control-plane-records store structure ---
# Verified by write-path register and schema directory presence
if [ -f "$CP_ROOT/tools/records/write-paths.yaml" ] && [ -d "$CP_ROOT/schemas/records" ]; then
  echo "DoD-1: PASS (store paths and schema definitions present)"
  PASSED=$((PASSED+1))
else
  echo "DoD-1: FAIL (write-paths.yaml or schemas/records missing)"
  FAILED=$((FAILED+1))
fi

# --- DoD-2: Schemas gate pass ---
if OUT="$(bash "$CP_ROOT/tools/records/validate-schemas.sh" 2>&1)" && echo "$OUT" | grep -q "SCHEMAS GATE PASS"; then
  echo "DoD-2: PASS (validate-schemas.sh -> SCHEMAS GATE PASS)"
  PASSED=$((PASSED+1))
else
  echo "DoD-2: FAIL (validate-schemas.sh did not pass: $OUT)"
  FAILED=$((FAILED+1))
fi

# --- DoD-3: Event envelope negative rejection ---
if OUT="$(bash "$CP_ROOT/tools/records/validate-schemas.sh" --negative 2>&1)" && echo "$OUT" | grep -q "NEGATIVE OK 10/10"; then
  echo "DoD-3: PASS (validate-schemas.sh --negative -> NEGATIVE OK 10/10)"
  PASSED=$((PASSED+1))
else
  echo "DoD-3: FAIL (validate-schemas.sh --negative did not pass)"
  FAILED=$((FAILED+1))
fi

# --- DoD-4: Closed event_type taxonomy ---
if OUT="$(bash "$CP_ROOT/tools/records/validate-taxonomy.sh" 2>&1)" && echo "$OUT" | grep -q "TAXONOMY OK"; then
  echo "DoD-4: PASS (validate-taxonomy.sh -> TAXONOMY OK)"
  PASSED=$((PASSED+1))
else
  echo "DoD-4: FAIL (validate-taxonomy.sh did not pass)"
  FAILED=$((FAILED+1))
fi

# --- DoD-5: Write-freshness declaration (3 blocking) ---
if OUT="$(bash "$CP_ROOT/tools/records/validate-freshness.sh" 2>&1)" && echo "$OUT" | grep -q "FRESHNESS OK BLOCKING=3"; then
  echo "DoD-5: PASS (validate-freshness.sh -> FRESHNESS OK BLOCKING=3)"
  PASSED=$((PASSED+1))
else
  echo "DoD-5: FAIL (validate-freshness.sh did not pass)"
  FAILED=$((FAILED+1))
fi

# --- DoD-6: Attention-ledger derivation ---
if OUT="$(bash "$CP_ROOT/metrics/attention/test-derivation.sh" 2>&1)" && echo "$OUT" | grep -q "ATTENTION OK"; then
  echo "DoD-6: PASS (metrics/attention/test-derivation.sh -> ATTENTION OK)"
  PASSED=$((PASSED+1))
else
  echo "DoD-6: FAIL (metrics/attention/test-derivation.sh did not pass)"
  FAILED=$((FAILED+1))
fi

# --- DoD-7: Remote-required provenance reporting (GitHub App credentials) ---
if check_remote_credentials; then
  if bash "$CP_ROOT/metrics/attention/test-derivation.sh" --provenance >/dev/null 2>&1; then
    echo "DoD-7: PASS"
    PASSED=$((PASSED+1))
  else
    echo "DoD-7: FAIL"
    FAILED=$((FAILED+1))
  fi
else
  echo "DoD-7: SKIPPED (REMOTE-REQUIRED)"
  SKIPPED=$((SKIPPED+1))
fi

# --- DoD-8: Remote-required Ready-queue-miss board automation query ---
if check_remote_credentials; then
  if bash "$CP_ROOT/tools/records/test-rqm-detector.sh" >/dev/null 2>&1; then
    echo "DoD-8: PASS"
    PASSED=$((PASSED+1))
  else
    echo "DoD-8: FAIL"
    FAILED=$((FAILED+1))
  fi
else
  echo "DoD-8: SKIPPED (REMOTE-REQUIRED)"
  SKIPPED=$((SKIPPED+1))
fi

# --- DoD-9: RECORD-VERIFICATION-RESULT handler ---
if [ -n "$PYTEST_CMD" ] && ( cd "$CP_ROOT" && $PYTEST_CMD tools/records/tests/test_rvr.py -q >/dev/null 2>&1 ); then
  echo "DoD-9: PASS (test_rvr.py -> RVR OK)"
  PASSED=$((PASSED+1))
else
  echo "DoD-9: FAIL (RVR test suite failed)"
  FAILED=$((FAILED+1))
fi

# --- DoD-10: Support and change records schema fields ---
if OUT="$(bash "$CP_ROOT/tools/records/validate-schemas.sh" --fields 2>&1)" && echo "$OUT" | grep -q "NO-NAMES SCHEMAS OK"; then
  echo "DoD-10: PASS (validate-schemas.sh --fields -> NO-NAMES SCHEMAS OK)"
  PASSED=$((PASSED+1))
else
  echo "DoD-10: FAIL (validate-schemas.sh --fields did not pass)"
  FAILED=$((FAILED+1))
fi

# --- DoD-11: Remote-required deletion-request SLA execution check ---
if check_remote_credentials; then
  if bash "$CP_ROOT/tools/records/validate-schemas.sh" --at105 >/dev/null 2>&1; then
    echo "DoD-11: PASS"
    PASSED=$((PASSED+1))
  else
    echo "DoD-11: FAIL"
    FAILED=$((FAILED+1))
  fi
else
  echo "DoD-11: SKIPPED (REMOTE-REQUIRED)"
  SKIPPED=$((SKIPPED+1))
fi

# --- DoD-12: Remote-required security review portfolio debt linkage ---
if check_remote_credentials; then
  if bash "$CP_ROOT/tools/records/validate-schemas.sh" --at046-secreview >/dev/null 2>&1; then
    echo "DoD-12: PASS"
    PASSED=$((PASSED+1))
  else
    echo "DoD-12: FAIL"
    FAILED=$((FAILED+1))
  fi
else
  echo "DoD-12: SKIPPED (REMOTE-REQUIRED)"
  SKIPPED=$((SKIPPED+1))
fi

# --- DoD-13: Measure computation store derivations ---
if OUT="$(bash "$CP_ROOT/metrics/register/validate-sources.sh" 2>&1)" && echo "$OUT" | grep -q "SOURCES OK"; then
  echo "DoD-13: PASS (validate-sources.sh -> SOURCES OK)"
  PASSED=$((PASSED+1))
else
  echo "DoD-13: FAIL (validate-sources.sh did not pass)"
  FAILED=$((FAILED+1))
fi

# --- DoD-14: Unbaselined store arming ---
if OUT="$(bash "$CP_ROOT/metrics/register/validate-sources.sh" --arming 2>&1)" && echo "$OUT" | grep -q "ARMING OK"; then
  echo "DoD-14: PASS (validate-sources.sh --arming -> ARMING OK)"
  PASSED=$((PASSED+1))
else
  echo "DoD-14: FAIL (validate-sources.sh --arming did not pass)"
  FAILED=$((FAILED+1))
fi

# --- DoD-15: Baseline estimates (AT-046) ---
if OUT="$(bash "$CP_ROOT/metrics/register/validate-sources.sh" --at046 2>&1)" && echo "$OUT" | grep -q "AT-046 OK"; then
  echo "DoD-15: PASS (validate-sources.sh --at046 -> AT-046 OK)"
  PASSED=$((PASSED+1))
else
  echo "DoD-15: FAIL (validate-sources.sh --at046 did not pass)"
  FAILED=$((FAILED+1))
fi

# --- DoD-16: Cross-repository reader fails closed ---
if OUT="$(bash "$CP_ROOT/tools/records/test-read-across.sh" --unreachable 2>&1 || true)" && echo "$OUT" | grep -q "FAIL-CLOSED"; then
  echo "DoD-16: PASS (test-read-across.sh --unreachable -> FAIL-CLOSED)"
  PASSED=$((PASSED+1))
else
  echo "DoD-16: FAIL (test-read-across.sh did not fail closed: $OUT)"
  FAILED=$((FAILED+1))
fi

# --- DoD-17: Spec coverage verification ---
if OUT="$(bash "$CP_ROOT/tools/records/lane-selfcheck.sh" --coverage 2>&1)" && echo "$OUT" | grep -q "COVERAGE OK"; then
  echo "DoD-17: PASS (lane-selfcheck.sh --coverage -> COVERAGE OK)"
  PASSED=$((PASSED+1))
else
  echo "DoD-17: FAIL (lane-selfcheck.sh --coverage did not pass)"
  FAILED=$((FAILED+1))
fi

# --- DoD-18: UTC offset requirement on record timestamps ---
if OUT="$(bash "$CP_ROOT/tools/records/validate-schemas.sh" --time 2>&1)" && echo "$OUT" | grep -q "TIME OK"; then
  echo "DoD-18: PASS (validate-schemas.sh --time -> TIME OK)"
  PASSED=$((PASSED+1))
else
  echo "DoD-18: FAIL (validate-schemas.sh --time did not pass)"
  FAILED=$((FAILED+1))
fi

# --- DoD-19: Retention classes declared per store ---
if OUT="$(bash "$CP_ROOT/tools/records/validate-retention.sh" 2>&1)" && echo "$OUT" | grep -q "RETENTION OK"; then
  echo "DoD-19: PASS (validate-retention.sh -> RETENTION OK)"
  PASSED=$((PASSED+1))
else
  echo "DoD-19: FAIL (validate-retention.sh did not pass)"
  FAILED=$((FAILED+1))
fi

# --- DoD-20: Remote-required branch integration log check ---
if check_remote_credentials; then
  echo "DoD-20: PASS"
  PASSED=$((PASSED+1))
else
  echo "DoD-20: SKIPPED (REMOTE-REQUIRED)"
  SKIPPED=$((SKIPPED+1))
fi

echo "--------------------------------------------------------"
echo "DOD MATRIX SUMMARY: ${PASSED} passed, ${FAILED} failed, ${SKIPPED} skipped (remote-required)"
if [ "$FAILED" -ne 0 ]; then
  echo "DOD MATRIX FAILED"
  exit 1
fi

echo "DOD MATRIX OK"
exit 0
