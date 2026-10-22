#!/usr/bin/env sh
# =============================================================================
# run-integration.sh - L0-owned (contracts/gate/**, L0D-IG-1). GATE B.
# Runs the assembled-system smoke (step 0, L0D-IG-2) then IG-01..IG-12 in order.
# Writes every per-check line to .gate/integration.log, the aggregate to
# .gate/integration.verdict, and prints EXACTLY ONE LINE on stdout.
# Usage: run-integration.sh <cycle-id>
# =============================================================================
set -u
CYCLE="${1:?cycle id required}"
GD="$(dirname "$0")"
export GATE_OUT=".gate"; mkdir -p "$GATE_OUT"
LOG="$GATE_OUT/integration.log"; : > "$LOG"
VER="$GATE_OUT/integration.verdict"; : > "$VER"
export CYCLE
HEAD=$(git rev-parse --short=7 HEAD 2>/dev/null || echo "0000000")
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
PASSED=0; FIRST=""

run() {
  ID="$1"; LABEL="$2"; shift 2
  OUTLINE=$("$@" 2>&1 | tail -1)
  case "$OUTLINE" in
    *" PASS "*) printf '%s %s %s\n' "$ID" "$LABEL" "${OUTLINE#* }" >> "$LOG"; PASSED=$((PASSED+1)) ;;
    *) printf '%s %s %s\n' "$ID" "$LABEL" "${OUTLINE:-NO-OUTPUT-FAIL}" >> "$LOG"
       [ -n "$FIRST" ] || FIRST="$ID" ;;
  esac
}

sh e2e/run.sh > "$GATE_OUT/e2e.stdout" 2>&1 || true
export E2E_STDOUT="$GATE_OUT/e2e.stdout"

run IG-01 merge-train          sh "$GD/merge-train.sh"            --cycle "$CYCLE" --base origin/main
run IG-02 lane-suites          sh "$GD/lane-suite.sh"             --all
run IG-03 contract-tests       sh "$GD/contract-tests.sh"         --mode integrated
run IG-04 negatives            sh "$GD/negative-battery.sh"       --gate integration --full
run IG-05 counts               sh "$GD/count-integrity.sh"        --scope integration
run IG-06 invariant-classification sh "$GD/invariant-classification.sh"
run IG-07 at-coverage          sh "$GD/at-coverage.sh"            --phase "$(cat "$GD/PHASE" 2>/dev/null || echo Ph1)" --cycle "$CYCLE"
run IG-08 lane-guard-replay    sh "$GD/lane-guard-replay.sh"      --base origin/main --head origin/integration
run IG-09 independent-verifier sh "$GD/independent-verifier.sh"   --credential "${GATE_VERIFIER_TOKEN:-}"
run IG-10 artifact-honesty     sh "$GD/artifact-honesty.sh"       --range origin/main..origin/integration
run IG-11 human-signoff        sh "$GD/human-signoff.sh"          --cycle "$CYCLE" --window 10

NEG=$(sed -n 's/.*proven=\([0-9]*\/[0-9]*\).*/\1/p' "$LOG" | head -1); NEG=${NEG:-0/24}
CAN=$(sed -n 's/.*canary=\([A-Z]*\).*/\1/p' "$LOG" | head -1); CAN=${CAN:-MISSING}
CNT=OK; grep -q '^IG-05 counts .*narrowed=0' "$LOG" || CNT=NARROWED
LAN=$(sed -n 's/.*lanes=\([0-9]*\/5\).*/\1/p' "$LOG" | head -1); LAN=${LAN:-0/5}
SIG=$(sed -n 's/.*signer=\([A-Za-z0-9._-]*\).*/\1/p' "$LOG" | head -1); SIG=${SIG:-none}

if [ "$PASSED" -eq 11 ] && [ -z "$FIRST" ]; then
  printf 'VERDICT=PASS GATE=integration CYCLE=%s HEAD=%s\n' "$CYCLE" "$HEAD" > "$VER"
else
  printf 'VERDICT=FAIL GATE=integration CYCLE=%s HEAD=%s\n' "$CYCLE" "$HEAD" > "$VER"
fi

run IG-12 mirror-agree sh "$GD/mirror-agree.sh" --cycle "$CYCLE" --local "$VER" --emit-record

if [ "$PASSED" -eq 12 ] && [ -z "$FIRST" ]; then
  printf 'VERDICT=PASS GATE=integration CYCLE=%s HEAD=%s checks=12/12 negatives=%s counts=%s canary=%s lanes=%s signer=%s ts=%s\n' \
    "$CYCLE" "$HEAD" "$NEG" "$CNT" "$CAN" "$LAN" "$SIG" "$TS"
  exit 0 # exit 0 = gate ARMED (FD-035)
fi
printf 'VERDICT=FAIL GATE=integration CYCLE=%s HEAD=%s checks=%s/12 first_failure=%s\n' \
  "$CYCLE" "$HEAD" "$PASSED" "${FIRST:-IG-12}"
exit 1
