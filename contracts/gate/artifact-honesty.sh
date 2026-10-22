#!/usr/bin/env sh
# =============================================================================
# artifact-honesty.sh - L0-owned (contracts/gate/**, L0D-IG-1). IG-10.
#   --range <base>..<head>
# Preconditions (L0D-IG-2): the assembled-system smoke of protocol/08 has run and
# e2e/verdict.sh printed "VERDICT: PASS". Without it there is no digest chain to
# inspect and the check FAILS - it is never skipped and never not-applicable.
# Last line on stdout is the verdict. Exit 0 pass, 1 fail, 2 config error.
# =============================================================================
set -eu
RANGE=""
while [ $# -gt 0 ]; do case "$1" in
  --range) RANGE="$2"; shift 2 ;;
  *) echo "ARTIFACT-HONESTY FAIL: unknown argument '$1'"; exit 2 ;;
esac; done
[ -n "$RANGE" ] || { echo "ARTIFACT-HONESTY FAIL: --range <base>..<head> required"; exit 2; }
OUT="${GATE_OUT:-.gate}"; mkdir -p "$OUT"; DET="$OUT/artifact-honesty.txt"; : > "$DET"

E2E_STDOUT="${E2E_STDOUT:-$OUT/e2e.stdout}"
E2E=FAIL
if [ -f "$E2E_STDOUT" ] && grep -Fq 'VERDICT: PASS' "$E2E_STDOUT"; then E2E=PASS; fi
POS=$(sed -n 's/.*PASS — \([0-9]*\) checkpoints.*/\1/p' "$E2E_STDOUT" 2>/dev/null | tail -1); POS=${POS:-0}
NEGP=$(sed -n 's/.*checkpoints, \([0-9]*\) gates proven able to fail.*/\1/p' "$E2E_STDOUT" 2>/dev/null | tail -1); NEGP=${NEGP:-0}
printf 'e2e verdict=%s checkpoints=%s/118 gates_proven=%s/28\n' "$E2E" "$POS" "$NEGP" >> "$DET"

CPR="${CPR_ROOT:-$(cd "$OUT/../../.." && pwd)/control-plane-records}"
MIS=0; REBUILT=0; PAIRS=0
for D in "$CPR"/records/deployments/*.yaml; do
  [ -f "$D" ] || continue
  ENVN=$(sed -n 's/^ *environment: *//p' "$D")
  [ "$ENVN" = "production" ] || continue
  PAIRS=$((PAIRS+1))
  PD=$(sed -n 's/^ *digest: *//p' "$D")
  SD=$(sed -n 's/^ *staging_verified_digest: *//p' "$D")
  RB=$(sed -n 's/^ *rebuilt: *//p' "$D"); RB=${RB:-false}
  [ "$PD" = "$SD" ] || { MIS=$((MIS+1)); printf 'digest mismatch %s prod=%s staging=%s\n' "$D" "$PD" "$SD" >> "$DET"; }
  [ "$RB" = "false" ] || { REBUILT=$((REBUILT+1)); printf 'rebuilt artifact %s\n' "$D" >> "$DET"; }
done

SKIP=0; NEU=0
for SHA in $(git log --format=%H "$RANGE" 2>/dev/null || true); do
  gh api "repos/{owner}/{repo}/commits/$SHA/check-runs" --jq \
    '.check_runs[] | select(.conclusion=="skipped" or .conclusion=="neutral") | .name + " " + .conclusion' \
    2>/dev/null >> "$OUT/conclusions.txt" || true
done
SKIP=$(grep -c ' skipped$' "$OUT/conclusions.txt" 2>/dev/null || true)
NEU=$(grep -c ' neutral$' "$OUT/conclusions.txt" 2>/dev/null || true)

if [ "$E2E" = "PASS" ] && [ "$PAIRS" -gt 0 ] && [ "$MIS" -eq 0 ] && [ "$REBUILT" -eq 0 ] \
   && [ "$SKIP" -eq 0 ] && [ "$NEU" -eq 0 ]; then
  printf 'ARTIFACT-HONESTY PASS digest_mismatches=0 rebuilt=0 skipped=0 neutral=0\n'
  exit 0 # exit 0 = gate ARMED (FD-035)
fi
printf 'ARTIFACT-HONESTY FAIL e2e=%s deployments=%s digest_mismatches=%s rebuilt=%s skipped=%s neutral=%s\n' \
  "$E2E" "$PAIRS" "$MIS" "$REBUILT" "$SKIP" "$NEU"
exit 1
