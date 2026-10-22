#!/usr/bin/env sh
# =============================================================================
# merge-train.sh - L0-owned (contracts/gate/**, L0D-IG-1). IG-01.
#   --cycle <id> --base origin/main
# Asserts: all five lanes landed this cycle, in the FROZEN order 1,4,2,3,5, and
# no lane merged another lane's branch (PARTITION.md "Branch & merge model").
# Last line on stdout is the verdict. Exit 0 pass, 1 fail, 2 config error.
# =============================================================================
set -eu
CYCLE=""; BASE=""
while [ $# -gt 0 ]; do case "$1" in
  --cycle) CYCLE="$2"; shift 2 ;;
  --base)  BASE="$2";  shift 2 ;;
  *) echo "MERGE-TRAIN FAIL: unknown argument '$1'"; exit 2 ;;
esac; done
[ -n "$CYCLE" ] && [ -n "$BASE" ] || { echo "MERGE-TRAIN FAIL: --cycle <id> --base <ref> required"; exit 2; }
OUT="${GATE_OUT:-.gate}"; mkdir -p "$OUT"; DET="$OUT/merge-train.txt"; : > "$DET"
FROZEN="1 4 2 3 5"

git log --merges --reverse --format='%H%x09%s' "$BASE..origin/integration" 2>/dev/null > "$OUT/merges.tsv" || : > "$OUT/merges.tsv"
SEEN=""; CROSS=0
while IFS='	' read -r sha subj; do
  [ -n "$sha" ] || continue
  L=$(printf '%s' "$subj" | sed -n "s|.*lane/\([1-5]\)/.*|\1|p")
  if [ -z "$L" ]; then printf '%s NON-LANE MERGE %s\n' "$sha" "$subj" >> "$DET"; continue; fi
  N=$(git log -1 --format=%s "$sha^2" 2>/dev/null | sed -n "s|.*lane/\([1-5]\)/.*|\1|p")
  if [ -n "$N" ] && [ "$N" != "$L" ]; then
    CROSS=$((CROSS+1)); printf '%s CROSS-LANE MERGE lane%s merged lane%s\n' "$sha" "$L" "$N" >> "$DET"
  fi
  SEEN="$SEEN $L"
  printf '%s lane=%s %s\n' "$sha" "$L" "$subj" >> "$DET"
done < "$OUT/merges.tsv"

ACTUAL=$(printf '%s' "$SEEN" | tr ' ' '\n' | grep -v '^$' | awk '!seen[$0]++' | tr '\n' ' ' | sed 's/ $//')
LANES=$(printf '%s' "$ACTUAL" | tr ' ' '\n' | grep -c . || true)
OOO=0; [ "$ACTUAL" = "$FROZEN" ] || OOO=1
printf 'frozen=[%s] actual=[%s] out_of_order=%s cross=%s\n' "$FROZEN" "$ACTUAL" "$OOO" "$CROSS" >> "$DET"

if [ "$LANES" -eq 5 ] && [ "$OOO" -eq 0 ] && [ "$CROSS" -eq 0 ]; then
  printf 'MERGE-TRAIN PASS lanes=5/5 order=1,4,2,3,5 out_of_order=0 cross_lane_merges=0\n'; exit 0 # exit 0 = gate ARMED (FD-035)
fi
printf 'MERGE-TRAIN FAIL lanes=%s/5 order=%s out_of_order=%s cross_lane_merges=%s\n' \
  "$LANES" "$(printf '%s' "$ACTUAL" | tr ' ' ',')" "$OOO" "$CROSS"
exit 1
