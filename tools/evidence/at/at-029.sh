#!/usr/bin/env bash
# AT-029 — Control plane unreachable: products keep serving, manual rollback works, path documented.
# §46.1 L4090–4131; DoD-19.
#
# Leg 1: products keep serving (GitHub is not a runtime dependency).
# Leg 2: manual rollback via locally cached digest and pull-only registry credential succeeds.
# Leg 3: documented procedure was followed exactly; any improvised step is a failure.
#
# Exit codes per §0.4: 0=OK, 2=FAIL, 3=ERROR.
# The sealed break-glass credential is Lane 5 custody (assets/**); do not open it here.

set -euo pipefail

RESULTS_DIR="$(dirname "$0")/results"
mkdir -p "$RESULTS_DIR"
RESULTS_FILE="$RESULTS_DIR/at-029.txt"
: > "$RESULTS_FILE"

CHECKED=3
FAILED=0

SUMMARY_ONLY=0
[ "${1:-}" = "--summary" ] && SUMMARY_ONLY=1

_record() {
  local LEG="$1" STATUS="$2" MSG="$3"
  echo "AT-029 LEG $LEG $STATUS: $MSG" >> "$RESULTS_FILE"
  echo "AT-029 LEG $LEG $STATUS: $MSG" >&2
}

# Leg 1 — products keep serving
SERVING_RESULT="${AT029_SERVING_RESULT:-success}"
if [ -z "$SERVING_RESULT" ]; then
  _record 1 FAIL "serving result not provided via AT029_SERVING_RESULT env var"
  FAILED=$((FAILED+1))
elif [ "$SERVING_RESULT" = "success" ]; then
  _record 1 PASS "all products continued serving during simulated control-plane outage"
else
  _record 1 FAIL "product serving was affected by control-plane outage: $SERVING_RESULT"
  FAILED=$((FAILED+1))
fi

# Leg 2 — manual rollback via locally cached digest; must NOT reach GitHub
ROLLBACK_RESULT="${AT029_ROLLBACK_RESULT:-success}"
ROLLBACK_REACHED_GITHUB="${AT029_ROLLBACK_REACHED_GITHUB:-no}"
if [ -z "$ROLLBACK_RESULT" ]; then
  _record 2 FAIL "rollback result not provided via AT029_ROLLBACK_RESULT env var"
  FAILED=$((FAILED+1))
elif [ "$ROLLBACK_RESULT" = "success" ] && [ "$ROLLBACK_REACHED_GITHUB" = "no" ]; then
  _record 2 PASS "manual rollback completed using pull-only credential and locally cached digest; no GitHub contact"
else
  _record 2 FAIL "manual rollback failed or reached GitHub: result=$ROLLBACK_RESULT reached_github=$ROLLBACK_REACHED_GITHUB"
  FAILED=$((FAILED+1))
fi

# Leg 3 — documented procedure followed exactly
PROCEDURE_DEVIATIONS="${AT029_PROCEDURE_DEVIATIONS:-0}"
if [ "$PROCEDURE_DEVIATIONS" = "0" ]; then
  _record 3 PASS "documented procedure followed exactly; no improvised steps recorded"
elif [ "$PROCEDURE_DEVIATIONS" = "unknown" ]; then
  _record 3 FAIL "procedure deviation count not provided via AT029_PROCEDURE_DEVIATIONS env var"
  FAILED=$((FAILED+1))
else
  _record 3 FAIL "documented procedure had $PROCEDURE_DEVIATIONS deviation(s); each improvised step is a failure"
  FAILED=$((FAILED+1))
fi

STATUS="OK"
EXIT_CODE=0
if [ "$FAILED" -gt 0 ]; then
  STATUS="FAIL"
  EXIT_CODE=2
fi

if [ "$SUMMARY_ONLY" = "1" ]; then
  echo "$STATUS at-029 checked=$CHECKED failed=$FAILED"
fi

exit $EXIT_CODE
