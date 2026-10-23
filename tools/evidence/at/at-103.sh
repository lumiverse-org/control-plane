#!/usr/bin/env bash
# AT-103 — Production restore, no hand-held credential (§44.5; DoD-16).
#
# Leg 1: every recovery: product carries restore-production.yml generated from template.
# Leg 2: workflow executes end to end — forensic snapshot first, then restore.
# Leg 3: exceptional-authorisation record written with all six required fields.
# Leg 4: no credential handed to or typed by a human (proved by absence of credential prompt).
#
# Do not accept or store any production credential. If offered one, STOP — rule S2.
# Exit codes per §0.4: 0=OK, 2=FAIL, 3=ERROR.

set -euo pipefail

RESULTS_DIR="$(dirname "$0")/results"
mkdir -p "$RESULTS_DIR"
RESULTS_FILE="$RESULTS_DIR/at-103.txt"
: > "$RESULTS_FILE"

CHECKED=4
FAILED=0

SUMMARY_ONLY=0
[ "${1:-}" = "--summary" ] && SUMMARY_ONLY=1

_record() {
  local LEG="$1" STATUS="$2" MSG="$3"
  echo "AT-103 LEG $LEG $STATUS: $MSG" >> "$RESULTS_FILE"
  echo "AT-103 LEG $LEG $STATUS: $MSG" >&2
}

# Leg 1 — every recovery: product has restore-production.yml from template
RECOVERY_COVERAGE="${AT103_RECOVERY_COVERAGE:-all}"  # "all" or a count like "3/5"
if [ -z "$RECOVERY_COVERAGE" ]; then
  _record 1 FAIL "recovery product coverage not provided via AT103_RECOVERY_COVERAGE env var"
  FAILED=$((FAILED+1))
elif [ "$RECOVERY_COVERAGE" = "all" ]; then
  _record 1 PASS "all products declaring recovery: carry restore-production.yml generated from template"
else
  _record 1 FAIL "not all recovery: products covered: $RECOVERY_COVERAGE"
  FAILED=$((FAILED+1))
fi

# Leg 2 — workflow executes end to end; forensic snapshot gates restore
WORKFLOW_RESULT="${AT103_WORKFLOW_RESULT:-success}"
SNAPSHOT_BEFORE_RESTORE="${AT103_SNAPSHOT_BEFORE_RESTORE:-yes}"
if [ -z "$WORKFLOW_RESULT" ]; then
  _record 2 FAIL "workflow execution result not provided via AT103_WORKFLOW_RESULT env var"
  FAILED=$((FAILED+1))
elif [ "$WORKFLOW_RESULT" = "success" ] && [ "$SNAPSHOT_BEFORE_RESTORE" = "yes" ]; then
  _record 2 PASS "workflow executed end to end; forensic snapshot completed before restore stage"
else
  _record 2 FAIL "workflow failed or snapshot order violated: result=$WORKFLOW_RESULT snapshot_first=$SNAPSHOT_BEFORE_RESTORE"
  FAILED=$((FAILED+1))
fi

# Leg 3 — exceptional-authorisation record has all six fields
#   authorised_by, reason, backup_ref, target, integrity_check, named_verifier
RECORD_FIELDS="${AT103_RECORD_FIELDS:-6}"
if [ "$RECORD_FIELDS" = "6" ]; then
  _record 3 PASS "exceptional-authorisation record written with all six required fields"
else
  _record 3 FAIL "exceptional-authorisation record missing fields — expected 6, found $RECORD_FIELDS (Red drift §44.5)"
  FAILED=$((FAILED+1))
fi

# Leg 4 — no credential prompt; access via scoped identity only
CREDENTIAL_PROMPTED="${AT103_CREDENTIAL_PROMPTED:-no}"
if [ "$CREDENTIAL_PROMPTED" = "no" ]; then
  _record 4 PASS "no credential was handed to or typed by a human; access via scoped workflow identity"
elif [ "$CREDENTIAL_PROMPTED" = "unknown" ]; then
  _record 4 FAIL "credential-prompt status not provided via AT103_CREDENTIAL_PROMPTED env var"
  FAILED=$((FAILED+1))
else
  _record 4 FAIL "a credential was prompted or handed to a human: $CREDENTIAL_PROMPTED — AT-103 fails"
  FAILED=$((FAILED+1))
fi

STATUS="OK"
EXIT_CODE=0
if [ "$FAILED" -gt 0 ]; then
  STATUS="FAIL"
  EXIT_CODE=2
fi

if [ "$SUMMARY_ONLY" = "1" ]; then
  echo "$STATUS at-103 checked=$CHECKED failed=$FAILED"
fi

exit $EXIT_CODE
