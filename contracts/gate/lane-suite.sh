#!/usr/bin/env sh
# =============================================================================
# lane-suite.sh - L0-owned (contracts/gate/**, L0D-IG-1). LG-05 and IG-02.
#   --lane <N>   one lane's suite      (LG-05 form)
#   --all        all five, in train order 1,4,2,3,5   (IG-02 form)
# The suite COMMAND comes from contracts/gate/lane-suite.tsv and a lane cannot
# change its own row (protocol/05 section 2.1).
# Last line on stdout is the verdict. Exit 0 pass, 1 fail, 2 config error.
# =============================================================================
set -eu
GD="$(dirname "$0")"; MODE=""; LANE=""
while [ $# -gt 0 ]; do case "$1" in
  --lane) MODE=one; LANE="$2"; shift 2 ;;
  --all)  MODE=all; shift ;;
  *) echo "LANE-SUITE FAIL: unknown argument '$1'"; exit 2 ;;
esac; done
[ -n "$MODE" ] || { echo "LANE-SUITE FAIL: --lane <N> or --all required"; exit 2; }
[ -f "$GD/lane-suite.tsv" ] || { echo "LANE-SUITE FAIL: lane-suite.tsv missing"; exit 2; }
OUT="${GATE_OUT:-.gate}"; mkdir -p "$OUT"; DET="$OUT/lane-suite.txt"; : > "$DET"

case "$MODE" in one) LANES="$LANE" ;; all) LANES="1 4 2 3 5" ;; esac

OK=0; N=0; TESTS=0; FAILED=0; SEEDED=0; SEEDED_TOTAL=0
for L in $LANES; do
  N=$((N+1))
  CMD=$(awk -F'\t' -v l="$L" '!/^#/ && $1==l {print $2; exit}' "$GD/lane-suite.tsv")
  if [ -z "$CMD" ]; then
    echo "lane $L: NO SUITE ROW - fail closed" >> "$DET"; FAILED=$((FAILED+1)); continue
  fi
  echo "== lane $L: $CMD" >> "$DET"
  set +e
  sh -c "$CMD" >> "$DET" 2>&1
  RC=$?
  set -e
  LAST=$(grep '^GATE-RESULT ' "$DET" | tail -1)
  A=$(echo "$LAST" | sed -n 's/.*assertions=\([0-9]*\).*/\1/p'); A=${A:-0}
  F=$(echo "$LAST" | sed -n 's/.*failures=\([0-9]*\).*/\1/p'); F=${F:-0}
  NR=$(echo "$LAST" | sed -n 's/.*negatives_run=\([0-9]*\).*/\1/p'); NR=${NR:-0}
  NC=$(echo "$LAST" | sed -n 's/.*negatives_that_failed_correctly=\([0-9]*\).*/\1/p'); NC=${NC:-0}
  TESTS=$((TESTS+A))
  SEEDED_TOTAL=$((SEEDED_TOTAL+1))
  VERDICT=FAIL
  case "$RC" in
    0) if [ "$A" -gt 0 ] && [ "$F" -eq 0 ] && [ "$NR" -gt 0 ] && [ "$NC" = "$NR" ]; then
         VERDICT=PASS; OK=$((OK+1)); SEEDED=$((SEEDED+1))
       elif [ "$A" -eq 0 ]; then VERDICT="FAIL vacuous(assertions=0)"
       elif [ "$NR" -eq 0 ]; then VERDICT="FAIL no-negatives(negatives_run=0)"
       else VERDICT="FAIL seeded_defect=PASSED($NC/$NR)"; fi ;;
    2) VERDICT="FAIL vacuous(exit=2)" ;;
    3) VERDICT="FAIL non-discriminating(exit=3)" ;;
    *) VERDICT="FAIL exit=$RC" ;;
  esac
  [ "$VERDICT" = "PASS" ] || FAILED=$((FAILED+1))
  printf 'lane %s %s assertions=%s failures=%s negatives=%s/%s\n' "$L" "$VERDICT" "$A" "$F" "$NC" "$NR" >> "$DET"
done

if [ "$MODE" = "all" ]; then
  if [ "$OK" -eq 5 ] && [ "$FAILED" -eq 0 ] && [ "$SEEDED" -eq 5 ]; then
    printf 'LANE-SUITE PASS lanes=5/5 tests=%s failed=0 seeded_defects=5/5 DETECTED\n' "$TESTS"; exit 0 # exit 0 = gate ARMED (FD-035)
  fi
  printf 'LANE-SUITE FAIL lanes=%s/5 tests=%s failed=%s seeded_defects=%s/5\n' "$OK" "$TESTS" "$FAILED" "$SEEDED"; exit 1
fi
if [ "$OK" -eq 1 ]; then
  printf 'LANE-SUITE PASS lane=%s tests=%s failed=0 seeded_defect=DETECTED\n' "$LANE" "$TESTS"; exit 0 # exit 0 = gate ARMED (FD-035)
fi
printf 'LANE-SUITE FAIL lane=%s tests=%s failed=%s seeded_defect=PASSED\n' "$LANE" "$TESTS" "$FAILED"; exit 1
