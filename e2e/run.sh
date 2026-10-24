#!/usr/bin/env bash
# e2e/run.sh
set -euo pipefail
export E2E_RUN_ID="${E2E_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short HEAD)}"
export E2E_PRODUCT=pilot-one
export E2E_REPO=org/pilot-one-api
export E2E_CP_REPO=org/control-plane
export E2E_RECORDS_REPO=org/control-plane-records
export E2E_RUN_START="$(date -u +%Y-%m-%dT%H:%M:%SZ)"   # freshness floor for CP-0708, CP-1204, CP-1207

# --first-run (CP-0003), --bootstrap (§8.4), --instrument-checks (§8.1), and --offline-only are flags,
# not environment folklore the operator must know to export by hand.
export E2E_FIRST_RUN="${E2E_FIRST_RUN:-0}"
export E2E_BOOTSTRAP="${E2E_BOOTSTRAP:-0}"
export E2E_INSTRUMENT_CHECKS="${E2E_INSTRUMENT_CHECKS:-0}"
export E2E_OFFLINE_ONLY="${E2E_OFFLINE_ONLY:-0}"
for arg in "$@"; do
  case "$arg" in
    --first-run) E2E_FIRST_RUN=1 ;;
    --bootstrap) E2E_BOOTSTRAP=1 ;;
    --instrument-checks) E2E_INSTRUMENT_CHECKS=1 ;;
    --offline-only) E2E_OFFLINE_ONLY=1 ;;
  esac
done
export E2E_FIRST_RUN E2E_BOOTSTRAP E2E_INSTRUMENT_CHECKS E2E_OFFLINE_ONLY
source e2e/lib/checkpoint.sh

if [ "${E2E_OFFLINE_ONLY}" = "1" ]; then
  # Parse classifications directly from canonical gap inventory
  python3 e2e/lib/parse_gap.py protocol/08-E2E-READINESS-GAP.md > "${E2E_OUT}/classifications.tsv"

  # Initialize baseline artifact paths so stage scripts' command substitutions don't fail under set -e
  [ -f "${E2E_OUT}/plan-id" ] || echo "plan-${E2E_PRODUCT}-001" > "${E2E_OUT}/plan-id"
  [ -f "${E2E_OUT}/pr" ] || echo "1" > "${E2E_OUT}/pr"
  [ -f "${E2E_OUT}/merge-sha" ] || echo "0000000000000000000000000000000000000000" > "${E2E_OUT}/merge-sha"
  [ -f "${E2E_OUT}/digest" ] || echo "sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad" > "${E2E_OUT}/digest"
  [ -f "${E2E_OUT}/prev-digest" ] || echo "sha256:1111111111111111111111111111111111111111111111111111111111111111" > "${E2E_OUT}/prev-digest"
  [ -f "${E2E_OUT}/uat-evidence-url" ] || echo "https://github.com/org/control-plane-records/actions/runs/1" > "${E2E_OUT}/uat-evidence-url"
  [ -f "${E2E_OUT}/uat-record-path" ] || echo "records/uat/uat-${E2E_PRODUCT}-001.yaml" > "${E2E_OUT}/uat-record-path"
  [ -f "${E2E_OUT}/prod-run-id" ] || echo "1000000001" > "${E2E_OUT}/prod-run-id"
fi

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
  if [ "${E2E_OFFLINE_ONLY}" = "1" ]; then
    bash "$s" || true
  else
    bash "$s" || break
  fi
done

for n in "${NEGATIVES[@]}"; do
  [ -f "$n" ] || continue
  # §8.4 bootstrap variant: skip and explicitly record as unproven the independence gates.
  case "$n" in
    */neg-09.sh|*/neg-10.sh|*/neg-12.sh|*/neg-13.sh)
      if [ "${E2E_BOOTSTRAP}" = "1" ] && [ "${E2E_OFFLINE_ONLY}" != "1" ]; then
        echo "== $n (skipped — bootstrap: independence gate unarmed, recorded unproven per §8.4)"
        continue
      fi
      ;;
  esac
  echo "== $n"
  if [ "${E2E_OFFLINE_ONLY}" = "1" ]; then
    bash "$n" || true
  else
    bash "$n" || break
  fi
done
bash e2e/verdict.sh          # §7 — the only thing allowed to print PASS for the run; `|| break` above keeps a
                              # stage/negative failure from killing this script under `set -e`, so verdict.sh —
                              # and its VERDICT: FAIL — always runs and its exit code is what run.sh returns
