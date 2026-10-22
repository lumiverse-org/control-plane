#!/usr/bin/env sh
# =============================================================================
# human-signoff.sh - L0-owned (contracts/gate/**, L0D-IG-1). IG-11.
#   --cycle <id> --window 10
# Last line on stdout is the verdict. Exit 0 pass, 1 fail, 2 config error.
# =============================================================================
set -eu
CYCLE=""; WIN=10
while [ $# -gt 0 ]; do case "$1" in
  --cycle)  CYCLE="$2"; shift 2 ;;
  --window) WIN="$2";   shift 2 ;;
  *) echo "HUMAN-SIGNOFF FAIL: unknown argument '$1'"; exit 2 ;;
esac; done
GD="$(dirname "$0")"
[ -n "$CYCLE" ] || { echo "HUMAN-SIGNOFF FAIL: --cycle <id> required"; exit 2; }
OUT="${GATE_OUT:-.gate}"; mkdir -p "$OUT"; DET="$OUT/human-signoff.txt"; : > "$DET"
CPR="${CPR_ROOT:-$(cd "$OUT/../../.." && pwd)/control-plane-records}"

DR=$(grep -rl "cycle: $CYCLE" "$CPR/records/decisions/" 2>/dev/null | head -1 || true)
if [ -z "$DR" ]; then
  printf 'HUMAN-SIGNOFF FAIL signer=none decision_record=none machine_approvals=0 window_cycles=%s rejections=0 rubber_stamp_flag=1\n' "$WIN"
  exit 1
fi
SIGNER=$(awk -F': *' '/^signer:/{print $2}' "$DR")
DRID=$(awk -F': *' '/^id:/{print $2}' "$DR")
printf 'decision_record=%s signer=%s\n' "$DR" "$SIGNER" >> "$DET"

MACH=0
grep -qxF "@$SIGNER" "$GD/machine-identities.txt" 2>/dev/null && MACH=1

BIG=$(git log --format='%H %an' "origin/main..origin/integration" 2>/dev/null | while read -r sha an; do
        printf '%s\t%s\n' "$(git show --numstat --format= "$sha" 2>/dev/null | awk '{s+=$1+$2} END{print s+0}')" "$an"
      done | LC_ALL=C sort -rn | head -1 | cut -f2 || true)
SELF=0; [ "$BIG" = "$SIGNER" ] && [ -n "$BIG" ] && SELF=1
[ "$SELF" -eq 0 ] || printf 'self_signoff=1 largest_diff_author=%s signer=%s\n' "$BIG" "$SIGNER" >> "$DET"

MAPP=0
sed 's/^@//' "$GD/machine-identities.txt" > "$OUT/.cleaned-machines.txt"
for PR in $(git log --merges --format=%s "origin/main..origin/integration" 2>/dev/null | sed -n 's/.*#\([0-9]*\).*/\1/p'); do
  N=$(gh pr view "$PR" --json reviews --jq \
      '[.reviews[] | select(.state=="APPROVED") | .author.login] | join("\n")' 2>/dev/null \
      | grep -c -F -f "$OUT/.cleaned-machines.txt" || true)
  MAPP=$((MAPP+N))
  [ "$N" -eq 0 ] || printf 'PR %s carries %s machine approval(s) - invariant 18, D53\n' "$PR" "$N" >> "$DET"
done

REJ=$(ls -1 "$CPR"/records/gate/integration/*/*.yaml 2>/dev/null | LC_ALL=C sort | tail -n "$WIN" \
      | xargs grep -l '^verdict: FAIL' 2>/dev/null | grep -c . || true)
DRILLS=$(ls -1 "$CPR"/records/gate-runs/"$CYCLE"/drill-L*.yaml 2>/dev/null | grep -c . || true)
FLAG=0; [ "$REJ" -eq 0 ] && FLAG=1
ANSWERED=0
[ "$FLAG" -eq 0 ] || { grep -q '^rubber_stamp_answer:' "$DR" 2>/dev/null && ANSWERED=1; }
printf 'window=%s rejections=%s drills=%s/5 flag=%s answered=%s\n' "$WIN" "$REJ" "$DRILLS" "$FLAG" "$ANSWERED" >> "$DET"

if [ "$MACH" -eq 0 ] && [ "$SELF" -eq 0 ] && [ "$MAPP" -eq 0 ] && [ "$DRILLS" -eq 5 ] \
   && { [ "$FLAG" -eq 0 ] || [ "$ANSWERED" -eq 1 ]; }; then
  printf 'HUMAN-SIGNOFF PASS signer=%s decision_record=%s machine_approvals=0 window_cycles=%s rejections=%s rubber_stamp_flag=%s\n' \
    "$SIGNER" "$DRID" "$WIN" "$REJ" "$FLAG"
  exit 0 # exit 0 = gate ARMED (FD-035)
fi
printf 'HUMAN-SIGNOFF FAIL signer=%s decision_record=%s machine_signer=%s self_signoff=%s machine_approvals=%s drills=%s/5 rejections=%s rubber_stamp_flag=%s answered=%s\n' \
  "$SIGNER" "$DRID" "$MACH" "$SELF" "$MAPP" "$DRILLS" "$REJ" "$FLAG" "$ANSWERED"
exit 1
