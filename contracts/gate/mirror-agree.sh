#!/usr/bin/env sh
# =============================================================================
# mirror-agree.sh - L0-owned (contracts/gate/**, L0D-IG-1). LG-12 and IG-12.
#   --cycle <id> --local .gate/integration.verdict [--emit-record]
# Compares the L0 verdict of record against the CI mirror (selfci-gate-b), and
# on --emit-record writes ONE append-only file per run (invariant 47).
# Last line on stdout is the verdict. Exit 0 pass, 1 fail, 2 config error.
# =============================================================================
set -eu
CYCLE=""; LOCAL=""; EMIT=0
while [ $# -gt 0 ]; do case "$1" in
  --cycle) CYCLE="$2"; shift 2 ;;
  --local) LOCAL="$2"; shift 2 ;;
  --emit-record) EMIT=1; shift ;;
  *) echo "MIRROR-AGREE FAIL: unknown argument '$1'"; exit 2 ;;
esac; done
[ -n "$CYCLE" ] && [ -n "$LOCAL" ] || { echo "MIRROR-AGREE FAIL: --cycle <id> --local <file> required"; exit 2; }
[ -f "$LOCAL" ] || { echo "MIRROR-AGREE FAIL: local verdict file missing - absence of output is never a pass"; exit 1; }
CPR="${CPR_ROOT:-$(cd "$LOCAL/../../.." && pwd)/control-plane-records}"
OUT="${GATE_OUT:-.gate}"; mkdir -p "$OUT"

LV=$(sed -n 's/^VERDICT=\([A-Z]*\).*/\1/p' "$LOCAL" | head -1); LV=${LV:-ABSENT}
SHA=$(git rev-parse HEAD 2>/dev/null || echo "0000000")
CV=$(gh api "repos/{owner}/{repo}/commits/$SHA/check-runs" \
      --jq '.check_runs[] | select(.name=="selfci-gate-b") | .conclusion' 2>/dev/null | head -1 || true)
case "$CV" in
  success) CV=PASS ;;
  failure) CV=FAIL ;;
  ""|null) CV=ABSENT ;;
  *) CV="$(printf '%s' "$CV" | tr '[:lower:]' '[:upper:]')" ;;
esac

DELTA=0; [ "$LV" = "$CV" ] || DELTA=1
case "$CV" in SKIPPED|NEUTRAL|ABSENT|CANCELLED) DELTA=1 ;; esac

REC="records/gate/integration/$(date -u +%F)/CYCLE-$CYCLE.yaml"
if [ "$EMIT" -eq 1 ]; then
  mkdir -p "$CPR/$(dirname "$REC")"
  [ -e "$CPR/$REC" ] && { echo "MIRROR-AGREE FAIL: $REC already exists - records are append-only, never overwritten (invariant 47)"; exit 1; }
  {
    printf 'record_schema_version: 1\nid: GATE-%s\nproduct: control-plane\n' "$CYCLE"
    printf 'timestamp: %s\ngate: integration\ncycle: %s\nhead: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$CYCLE" "$SHA"
    printf 'verdict: %s\nci_mirror: %s\ndelta: %s\n' "$LV" "$CV" "$DELTA"
    printf 'at_denominator: "37/110 (protocol/02 section 9.1)"\nchecks:\n'
    if [ -f "$OUT/integration.log" ]; then
      sed 's/^/  - "/; s/$/"/' "$OUT/integration.log"
    fi
  } > "$CPR/$REC"
fi

if [ "$DELTA" -eq 0 ] && { [ "$EMIT" -eq 0 ] || [ -f "$CPR/$REC" ]; }; then
  printf 'MIRROR-AGREE PASS ci=%s local=%s delta=0 record=%s\n' "$CV" "$LV" "$REC"; exit 0 # exit 0 = gate ARMED (FD-035)
fi
printf 'MIRROR-AGREE FAIL ci=%s local=%s delta=%s record=%s\n' "$CV" "$LV" "$DELTA" "$REC"
exit 1
