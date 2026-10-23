#!/usr/bin/env sh
# =============================================================================
# negative-battery.sh - L0-owned (contracts/gate/**, L0D-IG-1). LG-07 and IG-04.
#   --gate lane --lane <N>        prove the twelve LG- checks
#   --gate integration --full     prove all 24, plus the canary and seeded defects
# Every mutation is applied in a THROWAWAY WORKTREE and never in $CP_ROOT.
# Last line on stdout is the verdict. Exit 0 pass, 1 fail, 2 config error.
# =============================================================================
set -eu
GD="$(dirname "$0")"; GATE=""; LANE=""; FULL=0
while [ $# -gt 0 ]; do case "$1" in
  --gate) GATE="$2"; shift 2 ;;
  --lane) LANE="$2"; shift 2 ;;
  --full) FULL=1; shift ;;
  *) echo "NEGATIVE-BATTERY FAIL: unknown argument '$1'"; exit 2 ;;
esac; done
[ "$GATE" = "lane" ] || [ "$GATE" = "integration" ] || { echo "NEGATIVE-BATTERY FAIL: --gate lane|integration required"; exit 2; }
[ -f "$GD/negative-battery.tsv" ] || { echo "NEGATIVE-BATTERY FAIL: manifest missing - fail closed"; exit 2; }
OUT="${GATE_OUT:-.gate}"; mkdir -p "$OUT"; DET="$OUT/negative-battery.txt"; : > "$DET"

EXPECT=$(sort -u "$GD/expected-checks.txt" | grep -c .)
HAVE=$(cut -f1 "$GD/negative-battery.tsv" | grep -v '^#' | sort -u | grep -c .)
DUPS=$(cut -f1 "$GD/negative-battery.tsv" | grep -v '^#' | sort | uniq -d | grep -c . || true)
MISSING=$(comm -23 <(sort -u "$GD/expected-checks.txt") <(cut -f1 "$GD/negative-battery.tsv" | grep -v '^#' | sort -u) | tr '\n' ' ')
if [ "$HAVE" != "$EXPECT" ] || [ "$DUPS" -ne 0 ]; then
  printf 'manifest coverage broken have=%s expect=%s dups=%s missing=[%s]\n' "$HAVE" "$EXPECT" "$DUPS" "$MISSING" >> "$DET"
  printf 'NEGATIVE-BATTERY FAIL proven=0/%s unproven=%s canary=UNKNOWN seeded_defects=UNKNOWN\n' "$EXPECT" "$EXPECT"
  exit 1
fi

WT="$(mktemp -d)/probe"
git worktree add --detach "$WT" HEAD >/dev/null 2>&1 || { echo "NEGATIVE-BATTERY FAIL: cannot create throwaway worktree"; exit 2; }
cleanup() { git worktree remove --force "$WT" >/dev/null 2>&1 || true; }
trap cleanup EXIT INT TERM

PROVEN=0; UNPROVEN=0; TOTAL=0
while IFS='	' read -r check gate mutation token; do
  case "$check" in ''|\#*) continue ;; esac
  if [ "$GATE" = "lane" ] && [ "$gate" != "lane" ]; then continue; fi
  if [ "$GATE" = "integration" ] && [ "$FULL" -eq 0 ] && [ "$gate" != "integration" ]; then continue; fi
  TOTAL=$((TOTAL+1))
  M="$GD/mutations/$check.sh"
  if [ ! -x "$M" ]; then
    UNPROVEN=$((UNPROVEN+1)); printf '%s UNPROVEN no-mutation-script %s\n' "$check" "$M" >> "$DET"; continue
  fi
  set +e
  RESULT=$(GATE_PROBE_WT="$WT" GATE_OUT="$OUT/probe" sh "$M" 2>&1 | tail -1)
  set -e
  case "$RESULT" in
    *"$token"*) PROVEN=$((PROVEN+1)); printf '%s PROVEN bit-on=[%s] mutation=%s\n' "$check" "$token" "$mutation" >> "$DET" ;;
    *) UNPROVEN=$((UNPROVEN+1)); printf '%s UNPROVEN expected=[%s] got=[%s] mutation=%s\n' "$check" "$token" "$RESULT" "$mutation" >> "$DET" ;;
  esac
done < "$GD/negative-battery.tsv"

CANARY=n/a; SEEDED=n/a
if [ "$GATE" = "integration" ] && [ "$FULL" -eq 1 ]; then
  CR=$(GATE_PROBE_WT="$WT" sh "$GD/mutations/CANARY.sh" 2>&1 | tail -1)
  case "$CR" in *canary=MISSING*) CANARY=FOUND ;; *) CANARY=UNPROVEN ;; esac
  printf 'CANARY probe=[%s] verdict=%s (AT-102, section 53.1, EC-109)\n' "$CR" "$CANARY" >> "$DET"
  SR=$(GATE_PROBE_WT="$WT" sh "$GD/mutations/SEEDED-DEFECT.sh" 2>&1 | tail -1)
  case "$SR" in *seeded_defect=PASSED*) SEEDED=DETECTED ;; *) SEEDED=UNPROVEN ;; esac
  printf 'SEEDED-DEFECT probe=[%s] verdict=%s (section 31.2, SIG-18)\n' "$SR" "$SEEDED" >> "$DET"
fi

if [ "$UNPROVEN" -eq 0 ] && [ "$PROVEN" -eq "$TOTAL" ] \
   && { [ "$GATE" = "lane" ] || [ "$FULL" -eq 0 ] || { [ "$CANARY" = "FOUND" ] && [ "$SEEDED" = "DETECTED" ]; }; }; then
  printf 'NEGATIVE-BATTERY PASS proven=%s/%s unproven=0 canary=%s seeded_defects=%s\n' "$PROVEN" "$TOTAL" "$CANARY" "$SEEDED"
  exit 0 # exit 0 = gate ARMED (FD-035)
fi
printf 'NEGATIVE-BATTERY FAIL proven=%s/%s unproven=%s canary=%s seeded_defects=%s\n' "$PROVEN" "$TOTAL" "$UNPROVEN" "$CANARY" "$SEEDED"
exit 1
