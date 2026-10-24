#!/usr/bin/env bash
# e2e/verdict.sh
set -euo pipefail
source e2e/lib/checkpoint.sh
[ -f "${E2E_LOG}" ] || { echo "VERDICT: FAIL — checkpoint log not found"; exit 1; }
fails=$(awk -F'\t' '$3=="FAIL"' "${E2E_LOG}" | wc -l)
pos=$(awk  -F'\t' '$2 ~ /^CP-/  && $3=="PASS"' "${E2E_LOG}" | wc -l)
neg=$(awk  -F'\t' '$2 ~ /^NEG-/ && $3=="PASS"' "${E2E_LOG}" | wc -l)

[ "$fails" -eq 0 ] || { echo "VERDICT: FAIL — ${fails} checkpoint failures"; echo "GATE-RESULT gate=E2E-VERDICT level=T3 assertions=$((pos+neg)) failures=${fails} negatives_run=${neg} negatives_that_failed_correctly=${neg}"; exit 1; }
[ "$neg" -ge 28 ]  || { echo "VERDICT: FAIL — only ${neg}/28 gates were proven able to fail"; echo "GATE-RESULT gate=E2E-VERDICT level=T3 assertions=$((pos+neg)) failures=0 negatives_run=${neg} negatives_that_failed_correctly=${neg}"; exit 1; }
[ "$pos" -ge 118 ] || { echo "VERDICT: FAIL — only ${pos}/118 positive checkpoints ran"; echo "GATE-RESULT gate=E2E-VERDICT level=T3 assertions=$((pos+neg)) failures=0 negatives_run=${neg} negatives_that_failed_correctly=${neg}"; exit 1; }
echo "VERDICT: PASS — ${pos} checkpoints, ${neg} gates proven able to fail"
echo "GATE-RESULT gate=E2E-VERDICT level=T3 assertions=$((pos+neg)) failures=0 negatives_run=${neg} negatives_that_failed_correctly=${neg}"
