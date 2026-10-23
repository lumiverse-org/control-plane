#!/usr/bin/env sh
# =============================================================================
# lane-guard-replay.sh - L0-owned (contracts/gate/**, L0D-IG-1). IG-08.
#   --base origin/main --head origin/integration
# Replays LG-02 over EVERY commit in the merged range, so a foreign path that
# entered inside a merge commit is caught. Delegates to lane-guard.sh v2
# (L0-02-02) - the partition rule has exactly one implementation.
# Last line on stdout is the verdict. Exit 0 pass, 1 fail, 2 config error.
# =============================================================================
set -eu
BASE=""; HEAD=""
while [ $# -gt 0 ]; do case "$1" in
  --base) BASE="$2"; shift 2 ;;
  --head) HEAD="$2"; shift 2 ;;
  *) echo "LANE-GUARD-REPLAY FAIL: unknown argument '$1'"; exit 2 ;;
esac; done
[ -n "$BASE" ] && [ -n "$HEAD" ] || { echo "LANE-GUARD-REPLAY FAIL: --base and --head required"; exit 2; }
[ -x ./lane-guard.sh ] || { echo "LANE-GUARD-REPLAY FAIL: ./lane-guard.sh missing - fail closed"; exit 2; }
OUT="${GATE_OUT:-.gate}"; mkdir -p "$OUT"; DET="$OUT/lane-guard-replay.txt"; : > "$DET"

N=0; FOREIGN=0; UNOWNED=0
for SHA in $(git rev-list --reverse --no-merges "$BASE..$HEAD" 2>/dev/null || true); do
  N=$((N+1))
  SUBJ=$(git log -1 --format=%s "$SHA")
  L=$(git log -1 --format='%D %s' "$SHA" | sed -n "s|.*lane/\([1-5]\)/.*|\1|p")
  L=${L:-0}
  set +e
  R=$(./lane-guard.sh "$L" "$SHA^" "$SHA" 2>&1)
  set -e
  case "$(printf '%s' "$R" | tail -1)" in
    "LANE-GUARD OK") : ;;
    *) printf '%s lane=%s %s\n%s\n' "$SHA" "$L" "$SUBJ" "$R" >> "$DET" ;;
  esac
  FOREIGN=$((FOREIGN + $(printf '%s' "$R" | grep -c 'VIOLATION \[FOREIGN-PATH\]' || true)))
  UNOWNED=$((UNOWNED + $(printf '%s' "$R" | grep -c 'VIOLATION \[UNASSIGNED-PATH\]' || true)))
done

if [ "$FOREIGN" -eq 0 ] && [ "$UNOWNED" -eq 0 ]; then
  printf 'LANE-GUARD-REPLAY PASS commits=%s foreign=0 unowned=0\n' "$N"; exit 0 # exit 0 = gate ARMED (FD-035)
fi
printf 'LANE-GUARD-REPLAY FAIL commits=%s foreign=%s unowned=%s\n' "$N" "$FOREIGN" "$UNOWNED"
exit 1
