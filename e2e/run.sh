#!/usr/bin/env bash
# e2e/run.sh
set -euo pipefail
export E2E_RUN_ID="${E2E_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short HEAD)}"
export E2E_PRODUCT=pilot-one
export E2E_REPO=org/pilot-one-api
export E2E_CP_REPO=org/control-plane
export E2E_RECORDS_REPO=org/control-plane-records
export E2E_RUN_START="$(date -u +%Y-%m-%dT%H:%M:%SZ)"   # freshness floor for CP-0708, CP-1204, CP-1207

# --first-run (CP-0003) and --bootstrap (§8.4) are flags, not environment folklore the operator must
# know to export by hand.
export E2E_FIRST_RUN="${E2E_FIRST_RUN:-0}"
export E2E_BOOTSTRAP="${E2E_BOOTSTRAP:-0}"
for arg in "$@"; do
  case "$arg" in
    --first-run) E2E_FIRST_RUN=1 ;;
    --bootstrap) E2E_BOOTSTRAP=1 ;;
  esac
done
export E2E_FIRST_RUN E2E_BOOTSTRAP
source e2e/lib/checkpoint.sh

for s in e2e/stages/*.sh;   do echo "== $s"; bash "$s" || break; done
for n in e2e/negative/*.sh; do
  # §8.4 bootstrap variant: skip and explicitly record as unproven the independence gates.
  case "$n" in
    */neg-09.sh|*/neg-10.sh|*/neg-12.sh|*/neg-13.sh)
      if [ "${E2E_BOOTSTRAP}" = "1" ]; then
        echo "== $n (skipped — bootstrap: independence gate unarmed, recorded unproven per §8.4)"
        continue
      fi
      ;;
  esac
  echo "== $n"; bash "$n" || break
done
bash e2e/verdict.sh          # §7 — the only thing allowed to print PASS for the run; `|| break` above keeps a
                              # stage/negative failure from killing this script under `set -e`, so verdict.sh —
                              # and its VERDICT: FAIL — always runs and its exit code is what run.sh returns
