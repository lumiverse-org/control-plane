#!/usr/bin/env bash
# e2e/verdict.sh
set -euo pipefail
source e2e/lib/checkpoint.sh
[ -f "${E2E_LOG}" ] || { echo "VERDICT: FAIL — checkpoint log not found"; exit 1; }
if [ "${E2E_OFFLINE_ONLY:-0}" = "1" ]; then
  total=$(wc -l < "${E2E_LOG}")
  passes=$(awk -F'\t' '$3=="PASS"' "${E2E_LOG}" | wc -l)
  fails=$(awk -F'\t' '$3=="FAIL"' "${E2E_LOG}" | wc -l)
  skips=$(awk -F'\t' '$3=="SKIP"' "${E2E_LOG}" | wc -l)
  offline_ran=$((passes + fails))
  pos_pass=$(awk -F'\t' '$2 ~ /^CP-/ && $3=="PASS"' "${E2E_LOG}" | wc -l)
  neg_pass=$(awk -F'\t' '$2 ~ /^NEG-/ && $3=="PASS"' "${E2E_LOG}" | wc -l)
  pos_fail=$(awk -F'\t' '$2 ~ /^CP-/ && $3=="FAIL"' "${E2E_LOG}" | wc -l)
  neg_fail=$(awk -F'\t' '$2 ~ /^NEG-/ && $3=="FAIL"' "${E2E_LOG}" | wc -l)

  echo "================================================================================"
  echo "OFFLINE-SUBSET RESULT: total=${total} offline_ran=${offline_ran} offline_pass=${passes} offline_fail=${fails} skipped=${skips}"
  echo "  Positive: ran=$((pos_pass + pos_fail)) passed=${pos_pass} failed=${pos_fail}"
  echo "  Negative: ran=$((neg_pass + neg_fail)) passed=${neg_pass} failed=${neg_fail}"
  echo "  Skipped (blocked on live infra): ${skips}"
  echo "NOTE: Per §7.2 of protocol/08-smoke-and-e2e.md, offline subset execution NEVER emits 'VERDICT: PASS'."
  echo "GATE-RESULT gate=OFFLINE-SUBSET level=T2 total=${total} offline_ran=${offline_ran} passed=${passes} failures=${fails} skipped=${skips}"
  echo "================================================================================"
  if [ "$fails" -eq 0 ]; then
    exit 0
  else
    exit 1
  fi
fi

fails=$(awk -F'\t' '$3=="FAIL"' "${E2E_LOG}" | wc -l)
pos=$(awk  -F'\t' '$2 ~ /^CP-/  && $3=="PASS"' "${E2E_LOG}" | wc -l)
neg=$(awk  -F'\t' '$2 ~ /^NEG-/ && $3=="PASS"' "${E2E_LOG}" | wc -l)

[ "$fails" -eq 0 ] || { echo "VERDICT: FAIL — ${fails} checkpoint failures"; echo "GATE-RESULT gate=E2E-VERDICT level=T3 assertions=$((pos+neg)) failures=${fails} negatives_run=${neg} negatives_that_failed_correctly=${neg}"; exit 1; }
[ "$neg" -ge 28 ]  || { echo "VERDICT: FAIL — only ${neg}/28 gates were proven able to fail"; echo "GATE-RESULT gate=E2E-VERDICT level=T3 assertions=$((pos+neg)) failures=0 negatives_run=${neg} negatives_that_failed_correctly=${neg}"; exit 1; }
[ "$pos" -ge 118 ] || { echo "VERDICT: FAIL — only ${pos}/118 positive checkpoints ran"; echo "GATE-RESULT gate=E2E-VERDICT level=T3 assertions=$((pos+neg)) failures=0 negatives_run=${neg} negatives_that_failed_correctly=${neg}"; exit 1; }
echo "VERDICT: PASS — ${pos} checkpoints, ${neg} gates proven able to fail"
echo "GATE-RESULT gate=E2E-VERDICT level=T3 assertions=$((pos+neg)) failures=0 negatives_run=${neg} negatives_that_failed_correctly=${neg}"
