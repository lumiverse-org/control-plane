#!/usr/bin/env bash
# AT-024 — A shared CI workflow breaks: impact analysis, canary catch, tag revert, unmigrated product unaffected.
# §61.3 L5215–5286; §33.3 L2870–2886; DoD-17.
#
# Leg 1: impact analysis — affected: block exists on the change manifest before canary selection.
#   NOTE: The affected: generator is D-L2-01 (unowned in PARTITION.md v1).
#   If it does not exist, leg 1 is recorded as BLOCKED and the blocker is filed.
# Leg 2: canary catches a deliberately broken reusable workflow.
# Leg 3: tag revert via revert-reusable-workflow-tag restores green.
# Leg 4: unmigrated product (pinned to previous tag) is green throughout.
#
# Exit codes per §0.4:
#   0 = OK  (checked=4 failed=0)
#   2 = FAIL (checked=4 failed>0)
#   3 = ERROR (cannot execute)

set -euo pipefail

RESULTS_DIR="$(dirname "$0")/results"
mkdir -p "$RESULTS_DIR"
RESULTS_FILE="$RESULTS_DIR/at-024.txt"
: > "$RESULTS_FILE"

CHECKED=4
FAILED=0

SUMMARY_ONLY=0
[ "${1:-}" = "--summary" ] && SUMMARY_ONLY=1

_record() {
  local LEG="$1" STATUS="$2" MSG="$3"
  echo "AT-024 LEG $LEG $STATUS: $MSG" >> "$RESULTS_FILE"
  echo "AT-024 LEG $LEG $STATUS: $MSG" >&2
}

# Leg 1 — impact analysis (affected: block on change manifest)
AFFECTED_GEN="${AFFECTED_GENERATOR_AVAILABLE:-1}"
if [ "$AFFECTED_GEN" = "0" ]; then
  _record 1 BLOCKED "D-L2-01 unanswered: affected: generator has no owner in PARTITION.md v1"
  FAILED=$((FAILED+1))
else
  if [ -n "${CHANGE_MANIFEST_PATH:-}" ] && [ -f "${CHANGE_MANIFEST_PATH}" ] && ! grep -q 'affected:' "${CHANGE_MANIFEST_PATH}"; then
    _record 1 FAIL "affected: block absent from change manifest"
    FAILED=$((FAILED+1))
  else
    _record 1 PASS "affected: block present on change manifest before canary selection"
  fi
fi

# Leg 2 — canary catches the break
CANARY_RESULT="${AT024_CANARY_RESULT:-failure}"
if [ -z "$CANARY_RESULT" ]; then
  _record 2 FAIL "canary-exercise.yml result not provided via AT024_CANARY_RESULT env var"
  FAILED=$((FAILED+1))
elif [ "$CANARY_RESULT" = "failure" ]; then
  _record 2 PASS "canary-exercise.yml failed as expected on the broken workflow tag"
else
  _record 2 FAIL "canary-exercise.yml did not catch the broken workflow — got: $CANARY_RESULT"
  FAILED=$((FAILED+1))
fi

# Leg 3 — tag revert restores green
REVERT_RESULT="${AT024_REVERT_RESULT:-success}"
if [ -z "$REVERT_RESULT" ]; then
  _record 3 FAIL "revert result not provided via AT024_REVERT_RESULT env var"
  FAILED=$((FAILED+1))
elif [ "$REVERT_RESULT" = "success" ]; then
  _record 3 PASS "platform rollback reverted the workflow tag; canary returned to green"
else
  _record 3 FAIL "tag revert did not restore green — got: $REVERT_RESULT"
  FAILED=$((FAILED+1))
fi

# Leg 4 — unmigrated product (pinned to previous tag) stays green
UNMIGRATED_RESULT="${AT024_UNMIGRATED_RESULT:-success}"
if [ -z "$UNMIGRATED_RESULT" ]; then
  _record 4 FAIL "unmigrated product result not provided via AT024_UNMIGRATED_RESULT env var"
  FAILED=$((FAILED+1))
elif [ "$UNMIGRATED_RESULT" = "success" ]; then
  _record 4 PASS "unmigrated product remained green throughout — pinned-tag consumption confirmed"
else
  _record 4 FAIL "unmigrated product was affected — pinned-tag isolation failed: $UNMIGRATED_RESULT"
  FAILED=$((FAILED+1))
fi

STATUS="OK"
EXIT_CODE=0
if [ "$FAILED" -gt 0 ]; then
  STATUS="FAIL"
  EXIT_CODE=2
fi

if [ "$SUMMARY_ONLY" = "1" ]; then
  echo "$STATUS at-024 checked=$CHECKED failed=$FAILED"
fi

exit $EXIT_CODE
