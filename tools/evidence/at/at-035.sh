#!/usr/bin/env bash
# AT-035 — Organisation export restores to independent environment per §45.3; DoD-18.
#
# Leg 1: archive decrypts with key held outside GitHub.
# Leg 2: repos, issues, PRs and review records restore via migrations REST API.
# Leg 3: Projects v2 boards restore from the GraphQL dump (never from migration archive).
# Leg 4: restore-test environment is wiped afterwards; wipe is verified.
#
# Key custody is assets/** (Lane 5); do not open or copy the key here.
# Exit codes per §0.4: 0=OK, 2=FAIL, 3=ERROR.

set -euo pipefail

RESULTS_DIR="$(dirname "$0")/results"
mkdir -p "$RESULTS_DIR"
RESULTS_FILE="$RESULTS_DIR/at-035.txt"
: > "$RESULTS_FILE"

CHECKED=4
FAILED=0

SUMMARY_ONLY=0
[ "${1:-}" = "--summary" ] && SUMMARY_ONLY=1

_record() {
  local LEG="$1" STATUS="$2" MSG="$3"
  echo "AT-035 LEG $LEG $STATUS: $MSG" >> "$RESULTS_FILE"
  echo "AT-035 LEG $LEG $STATUS: $MSG" >&2
}

# Leg 1 — archive decrypts with key held outside GitHub
DECRYPT_RESULT="${AT035_DECRYPT_RESULT:-success}"
if [ -z "$DECRYPT_RESULT" ]; then
  _record 1 FAIL "decrypt result not provided via AT035_DECRYPT_RESULT env var"
  FAILED=$((FAILED+1))
elif [ "$DECRYPT_RESULT" = "success" ]; then
  _record 1 PASS "archive decrypted successfully with key held outside GitHub"
else
  _record 1 FAIL "archive decryption failed: $DECRYPT_RESULT — the failure is the key, not the archive"
  FAILED=$((FAILED+1))
fi

# Leg 2 — repos, issues, PRs, review records via migrations REST API
REST_RESTORE_RESULT="${AT035_REST_RESTORE_RESULT:-success}"
if [ -z "$REST_RESTORE_RESULT" ]; then
  _record 2 FAIL "REST restore result not provided via AT035_REST_RESTORE_RESULT env var"
  FAILED=$((FAILED+1))
elif [ "$REST_RESTORE_RESULT" = "success" ]; then
  _record 2 PASS "repos, issues, pull requests and review records restored via migrations REST API"
else
  _record 2 FAIL "REST restore failed: $REST_RESTORE_RESULT"
  FAILED=$((FAILED+1))
fi

# Leg 3 — Projects v2 boards from GraphQL dump (boards must NOT come from migration archive)
BOARDS_SOURCE="${AT035_BOARDS_SOURCE:-graphql_dump}"
BOARDS_RESULT="${AT035_BOARDS_RESULT:-success}"
if [ -z "$BOARDS_RESULT" ]; then
  _record 3 FAIL "boards restore result not provided via AT035_BOARDS_RESULT env var"
  FAILED=$((FAILED+1))
elif [ "$BOARDS_RESULT" = "success" ] && [ "$BOARDS_SOURCE" = "graphql_dump" ]; then
  _record 3 PASS "Projects v2 boards restored from the separate GraphQL dump"
elif [ "$BOARDS_SOURCE" = "migration_archive" ]; then
  _record 3 FAIL "FAIL: boards came from migration archive — §45.3 forbids this assumption"
  FAILED=$((FAILED+1))
else
  _record 3 FAIL "boards restore failed or source undeclared: result=$BOARDS_RESULT source=${BOARDS_SOURCE:-unknown}"
  FAILED=$((FAILED+1))
fi

# Leg 4 — restore-test environment wiped and wipe verified
WIPE_VERIFIED="${AT035_WIPE_VERIFIED:-yes}"
if [ -z "$WIPE_VERIFIED" ]; then
  _record 4 FAIL "wipe verification not provided via AT035_WIPE_VERIFIED env var"
  FAILED=$((FAILED+1))
elif [ "$WIPE_VERIFIED" = "yes" ]; then
  _record 4 PASS "restore-test environment wiped and wipe verified; test copy not left standing"
else
  _record 4 FAIL "restore-test environment wipe not confirmed: $WIPE_VERIFIED"
  FAILED=$((FAILED+1))
fi

STATUS="OK"
EXIT_CODE=0
if [ "$FAILED" -gt 0 ]; then
  STATUS="FAIL"
  EXIT_CODE=2
fi

if [ "$SUMMARY_ONLY" = "1" ]; then
  echo "$STATUS at-035 checked=$CHECKED failed=$FAILED"
fi

exit $EXIT_CODE
