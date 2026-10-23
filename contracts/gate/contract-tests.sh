#!/usr/bin/env sh
# =============================================================================
# contract-tests.sh - L0-owned (contracts/gate/**, L0D-IG-1). LG-06 and IG-03.
#   --lane <N>          the LG-06 form: everything lane N consumes and produces
#   --mode integrated   the IG-03 form: every pair, live producers only
# Delegates execution to the harness of protocol/01 section 9 and adds the two
# assertions only the gate can make: fixture immutability, and stubbed=0.
# Last line on stdout is the verdict. Exit 0 pass, 1 fail, 2 config error.
# =============================================================================
set -eu
GD="$(dirname "$0")"; MODE=""; LANE=""
while [ $# -gt 0 ]; do case "$1" in
  --lane) MODE=lane; LANE="$2"; shift 2 ;;
  --mode) MODE="$2"; shift 2 ;;
  *) echo "CONTRACT-TESTS FAIL: unknown argument '$1'"; exit 2 ;;
esac; done
[ "$MODE" = "lane" ] || [ "$MODE" = "integrated" ] || { echo "CONTRACT-TESTS FAIL: --lane <N> or --mode integrated required"; exit 2; }
OUT="${GATE_OUT:-.gate}"; mkdir -p "$OUT"; DET="$OUT/contract-tests.txt"; : > "$DET"
HARNESS="contracts/harness/run-contract-tests.sh"
MANIFEST="contracts/harness/pairs.tsv"
[ -x "$HARNESS" ] || { echo "CONTRACT-TESTS FAIL: harness $HARNESS missing - fail closed"; exit 1; }
[ -f "$MANIFEST" ] || { echo "CONTRACT-TESTS FAIL: pair manifest $MANIFEST missing - fail closed"; exit 1; }

# --- fixtures_match: the frozen tree must be byte-identical -------------------
HAVE=$(find contracts/fixtures -type f | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1)
WANT=$(cat "$GD/FIXTURES.sha256")
FM=0; [ "$HAVE" = "$WANT" ] && FM=1
printf 'fixtures have=%s want=%s match=%s\n' "$HAVE" "$WANT" "$FM" >> "$DET"

# --- L0-IG-D1: the manifest's pair count must agree with COUNTS.tsv ----------
PAIRS=$(grep -vc '^#' "$MANIFEST")
D00=$(awk -F'\t' '$1=="ct_pairs_p00"{print $2}' "$GD/COUNTS.tsv")
D01=$(awk -F'\t' '$1=="ct_pairs_p01"{print $2}' "$GD/COUNTS.tsv")
DECL=$(awk -F'\t' '$1=="ct_pairs"{print $2}' "$GD/COUNTS.tsv")
PAIRS_OK=0
if [ -n "$DECL" ]; then
  [ "$PAIRS" = "$DECL" ] && PAIRS_OK=1
else
  echo "L0-IG-D1 UNRESOLVED: manifest declares $PAIRS pairs; COUNTS.tsv declares $D00 (protocol/00) and $D01 (protocol/01)" >> "$DET"
fi

if [ "$MODE" = "integrated" ]; then
  set +e; "$HARNESS" --all --mode integrated --report "tsv:$OUT/contract-report.tsv" >> "$DET" 2>&1; RC=$?; set -e
else
  set +e; "$HARNESS" --side consumer --lane "L$LANE" --report "tsv:$OUT/contract-report.tsv" >> "$DET" 2>&1; RC=$?; set -e
fi

CASES=$(grep -vc '^#' "$OUT/contract-report.tsv" 2>/dev/null || echo 0)
FAILED=$(awk -F'\t' '!/^#/ && $3!="pass"{n++} END{print n+0}' "$OUT/contract-report.tsv" 2>/dev/null || echo 0)
STUBBED=$(awk -F'\t' '!/^#/ && $4 ~ /contract-stubs/{n++} END{print n+0}' "$OUT/contract-report.tsv" 2>/dev/null || echo 0)

if [ "$RC" -eq 0 ] && [ "$FAILED" -eq 0 ] && [ "$FM" -eq 1 ] && [ "$CASES" -gt 0 ] \
   && { [ "$MODE" = "lane" ] || { [ "$STUBBED" -eq 0 ] && [ "$PAIRS_OK" -eq 1 ]; }; }; then
  printf 'CONTRACT-TESTS PASS pairs=%s cases=%s failed=0 stubbed=%s fixtures_match=1\n' "$PAIRS" "$CASES" "$STUBBED"
  exit 0 # exit 0 = gate ARMED (FD-035)
fi
printf 'CONTRACT-TESTS FAIL pairs=%s cases=%s failed=%s stubbed=%s fixtures_match=%s\n' "$PAIRS" "$CASES" "$FAILED" "$STUBBED" "$FM"
exit 1
