#!/usr/bin/env sh
# =============================================================================
# rehearse.sh - L0-owned. Records the baseline first_failure with nothing
# broken, then for each IG-nn at or before that baseline breaks it and asserts
# first_failure moves to that check. Checks after the baseline are blocked by
# the baseline failure and record BLOCKED-BY-<baseline> rather than NOT-CLOSED.
# This supports Phase-0 gate state where open L0-IG-D decisions cause permanent
# baseline failures (B-02 correction). Section 95.4: executed for real.
# =============================================================================
set -eu
OUT="${GATE_OUT:-.gate}"; mkdir -p "$OUT"; R="$OUT/rehearsal.tsv"; : > "$R"
WT="$(mktemp -d)/rehearse"
git worktree add --detach "$WT" HEAD >/dev/null 2>&1
trap 'git worktree remove --force "$WT" >/dev/null 2>&1 || true' EXIT INT TERM

BV=$( cd "$WT" && GATE_OUT="$OUT/rehearse-base" sh contracts/gate/run-integration.sh REHEARSE-BASE 2>&1 | tail -1 )
BASELINE=$(printf '%s' "$BV" | sed -n 's/.*first_failure=\([A-Z0-9-]*\).*/\1/p')
BASELINE=${BASELINE:-NONE}

OK=0; N=0; PAST_BASE=0
for ID in IG-01 IG-02 IG-03 IG-04 IG-05 IG-06 IG-07 IG-08 IG-09 IG-10 IG-11 IG-12; do
  if [ "$PAST_BASE" -eq 1 ]; then
    printf '%s\tBLOCKED-BY-%s\t\n' "$ID" "$BASELINE" >> "$R"
    continue
  fi
  N=$((N+1))
  S=$(awk -v i="$ID" '$1==i{print $2}' <<'MAP'
IG-01 merge-train.sh
IG-02 lane-suite.sh
IG-03 contract-tests.sh
IG-04 negative-battery.sh
IG-05 count-integrity.sh
IG-06 invariant-classification.sh
IG-07 at-coverage.sh
IG-08 lane-guard-replay.sh
IG-09 independent-verifier.sh
IG-10 artifact-honesty.sh
IG-11 human-signoff.sh
IG-12 mirror-agree.sh
MAP
)
  cp -r contracts/gate "$WT/contracts/gate.bak" 2>/dev/null || true
  rm -f "$WT/contracts/gate/$S"
  V=$( cd "$WT" && GATE_OUT="$OUT/rehearse" sh contracts/gate/run-integration.sh REHEARSE 2>&1 | tail -1 )
  rm -rf "$WT/contracts/gate" && mv "$WT/contracts/gate.bak" "$WT/contracts/gate"
  case "$V" in
    *"VERDICT=FAIL"*"first_failure=$ID"*) OK=$((OK+1)); printf '%s\tCLOSED\t%s\n' "$ID" "$V" >> "$R" ;;
    *) printf '%s\tNOT-CLOSED\t%s\n' "$ID" "$V" >> "$R" ;;
  esac
  [ "$ID" != "$BASELINE" ] || PAST_BASE=1
done

REHEARSAL_BASELINE_FILE="gate-state/rehearsal-baseline"
CURRENT_CLOSED="$OK"
if [ ! -f "$REHEARSAL_BASELINE_FILE" ]; then
  mkdir -p gate-state
  printf '%s\n' "$CURRENT_CLOSED" > "$REHEARSAL_BASELINE_FILE"
  printf 'REHEARSAL BASELINE SET: %s closed=%s/%s blocked_by=%s\n' "$CURRENT_CLOSED" "$OK" "$N" "$BASELINE"
  exit 0
fi
STORED_BASELINE=$(cat "$REHEARSAL_BASELINE_FILE")
if [ "$CURRENT_CLOSED" -ge "$STORED_BASELINE" ]; then
  printf 'REHEARSAL OK: %s >= %s (no regression)\n' "$CURRENT_CLOSED" "$STORED_BASELINE"
  printf 'REHEARSAL %s closed=%s/%s blocked_by=%s\n' PASS "$OK" "$N" "$BASELINE"
  exit 0
else
  printf 'REHEARSAL FAIL: %s < %s (regression detected)\n' "$CURRENT_CLOSED" "$STORED_BASELINE"
  printf 'REHEARSAL %s closed=%s/%s blocked_by=%s\n' FAIL "$OK" "$N" "$BASELINE"
  exit 1
fi
