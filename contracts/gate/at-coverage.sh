#!/usr/bin/env sh
# =============================================================================
# at-coverage.sh - L0-owned (contracts/gate/**, L0D-IG-1). IG-07.
#   --phase <Ph1|Ph2|...|COND>   defaults to gate-state/PHASE
# Reads results from $CPR_ROOT/records/acceptance-runs/<cycle>/ and twin results
# from $CPR_ROOT/records/acceptance-twins/<cycle>/. One file per run, never an
# index (PARTITION rule 3).
# Last line on stdout is the verdict. Exit 0 pass, 1 fail, 2 config error.
# =============================================================================
set -eu
GD="$(dirname "$0")"; PHASE=""; CYCLE="${CYCLE:-}"
while [ $# -gt 0 ]; do case "$1" in
  --phase) PHASE="$2"; shift 2 ;;
  --cycle) CYCLE="$2"; shift 2 ;;
  *) echo "AT-COVERAGE FAIL: unknown argument '$1'"; exit 2 ;;
esac; done
PHASE="${PHASE:-$(cat "${CP_ROOT:-.}/gate-state/PHASE" 2>/dev/null || cat "$GD/PHASE" 2>/dev/null || true)}"
[ -n "$PHASE" ] || { echo "AT-COVERAGE FAIL: no phase given and gate-state/PHASE is empty"; exit 2; }
grep -q "	$PHASE	" "$GD/phase-order.tsv" || { echo "AT-COVERAGE FAIL: '$PHASE' is not a declared phase token"; exit 2; }
[ -n "$CYCLE" ] || { echo "AT-COVERAGE FAIL: CYCLE not set"; exit 2; }
CPR="${CPR_ROOT:-$(cd "$GD/../../.." && pwd)/control-plane-records}"
OUT="${GATE_OUT:-.gate}"; mkdir -p "$OUT"; DET="$OUT/at-coverage.tsv"; : > "$DET"

ORD=$(awk -F'\t' -v p="$PHASE" '$2==p{print $1}' "$GD/phase-order.tsv")
RUNS="$CPR/records/acceptance-runs/$CYCLE"
TWINS="$CPR/records/acceptance-twins/$CYCLE"
HARNESS="tools/at/run-at.sh"

SCHED=0; EXEC=0; NOTRUN=0; ASSERTED=0

HARNESS_PRESENT=1; [ -x "$HARNESS" ] || HARNESS_PRESENT=0

while IFS='	' read -r ph at owner twin; do
  case "$ph" in ''|\#*) continue ;; esac
  o=$(awk -F'\t' -v p="$ph" '$2==p{print $1}' "$GD/phase-order.tsv")
  [ "$o" -le "$ORD" ] || continue
  SCHED=$((SCHED+1))
  R="$RUNS/$at.yaml"
  if [ "$HARNESS_PRESENT" -eq 0 ] || [ ! -f "$R" ]; then
    NOTRUN=$((NOTRUN+1)); printf '%s\t%s\tNOT_RUN\t-\t%s\n' "$at" "$owner" "$twin" >> "$DET"; continue
  fi
  MODE=$(awk -F': *' '/^ *evidence:/{print $2}' "$R"); MODE=${MODE:-none}
  RESULT=$(awk -F': *' '/^ *result:/{print $2}' "$R"); RESULT=${RESULT:-none}
  HAS_CMD=$(grep -c '^ *command:' "$R" || true)
  HAS_RC=$(grep -c '^ *exit_code:' "$R" || true)
  TWIN_OK=1
  if [ "$twin" != "-" ]; then [ -f "$TWINS/$twin.yaml" ] || TWIN_OK=0; fi
  if [ "$MODE" = "asserted" ] || [ "$HAS_CMD" -eq 0 ] || [ "$HAS_RC" -eq 0 ] || [ "$TWIN_OK" -eq 0 ]; then
    ASSERTED=$((ASSERTED+1))
    printf '%s\t%s\tASSERTED_ONLY\t%s\t%s twin_result=%s\n' "$at" "$owner" "$RESULT" "$twin" "$TWIN_OK" >> "$DET"
  elif [ "$RESULT" = "pass" ]; then
    EXEC=$((EXEC+1)); printf '%s\t%s\tEXECUTED\tpass\t%s\n' "$at" "$owner" "$twin" >> "$DET"
  else
    NOTRUN=$((NOTRUN+1)); printf '%s\t%s\tFAILED\t%s\t%s\n' "$at" "$owner" "$RESULT" "$twin" >> "$DET"
  fi
done < "$GD/at-activation.tsv"

TOTAL=$(awk -F'\t' '!/^#/{n++} END{print n+0}' "$GD/at-activation.tsv")
printf '# phase=%s cycle=%s harness=%s denominator=%s/110 (protocol/02 section 9.1)\n' \
  "$PHASE" "$CYCLE" "$HARNESS_PRESENT" "$TOTAL" >> "$DET"

if [ "$NOTRUN" -eq 0 ] && [ "$ASSERTED" -eq 0 ] && [ "$SCHED" -eq "$EXEC" ]; then
  printf 'AT-COVERAGE PASS scheduled=%s executed=%s not_run=0 asserted_only=0\n' "$SCHED" "$EXEC"
  exit 0 # exit 0 = gate ARMED (FD-035)
fi
printf 'AT-COVERAGE FAIL scheduled=%s executed=%s not_run=%s asserted_only=%s\n' "$SCHED" "$EXEC" "$NOTRUN" "$ASSERTED"
exit 1
