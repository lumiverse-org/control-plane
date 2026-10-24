#!/usr/bin/env bash
# e2e/run.sh
set -euo pipefail
export E2E_RUN_ID="${E2E_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short HEAD)}"
export E2E_PRODUCT=pilot-one
export E2E_REPO=org/pilot-one-api
export E2E_CP_REPO=org/control-plane
export E2E_RECORDS_REPO=org/control-plane-records
export E2E_RUN_START="$(date -u +%Y-%m-%dT%H:%M:%SZ)"   # freshness floor for CP-0708, CP-1204, CP-1207

# --first-run (CP-0003), --bootstrap (§8.4), and --instrument-checks (§8.1) are flags, not environment folklore the operator must
# know to export by hand.
export E2E_FIRST_RUN="${E2E_FIRST_RUN:-0}"
export E2E_BOOTSTRAP="${E2E_BOOTSTRAP:-0}"
export E2E_INSTRUMENT_CHECKS="${E2E_INSTRUMENT_CHECKS:-0}"
for arg in "$@"; do
  case "$arg" in
    --first-run) E2E_FIRST_RUN=1 ;;
    --bootstrap) E2E_BOOTSTRAP=1 ;;
    --instrument-checks) E2E_INSTRUMENT_CHECKS=1 ;;
  esac
done
export E2E_FIRST_RUN E2E_BOOTSTRAP E2E_INSTRUMENT_CHECKS
source e2e/lib/checkpoint.sh

if [ "${E2E_INSTRUMENT_CHECKS}" = "1" ]; then
  STAGES=(e2e/stages/00-preflight.sh e2e/stages/01-create-product.sh e2e/stages/02-assign.sh e2e/stages/03-verification-contract.sh)
  NEGATIVES=(e2e/negative/neg-04.sh e2e/negative/neg-18.sh e2e/negative/neg-19.sh)
else
  STAGES=(e2e/stages/*.sh)
  NEGATIVES=(e2e/negative/*.sh)
fi

for s in "${STAGES[@]}"; do
  [ -f "$s" ] || continue
  echo "== $s"
  bash "$s" || break
done

for n in "${NEGATIVES[@]}"; do
  [ -f "$n" ] || continue
  # §8.4 bootstrap variant: skip and explicitly record as unproven the independence gates.
  case "$n" in
    */neg-09.sh|*/neg-10.sh|*/neg-12.sh|*/neg-13.sh)
      if [ "${E2E_BOOTSTRAP}" = "1" ]; then
        echo "== $n (skipped — bootstrap: independence gate unarmed, recorded unproven per §8.4)"
        continue
      fi
      ;;
  esac
  echo "== $n"
  bash "$n" || break
done
bash e2e/verdict.sh          # §7 — the only thing allowed to print PASS for the run; `|| break` above keeps a
                              # stage/negative failure from killing this script under `set -e`, so verdict.sh —
                              # and its VERDICT: FAIL — always runs and its exit code is what run.sh returns
