#!/usr/bin/env bash
set -euo pipefail
# e2e/stages/07-staging.sh
source e2e/lib/checkpoint.sh
DIGEST="$(cat "${E2E_OUT}/digest")"

cp_assert CP-0701 "migration applied through CI, not by hand" \
  ./tools/e2e-drive/run-workflow --repo "${E2E_REPO}" --workflow migrate.yml \
    --env staging --digest "${DIGEST}" --expect success

# CP-0702 Backward compatibility for one release cycle (Section 34.3): the PREVIOUS digest must still run
#         against the NEW schema. This is what makes rollback possible, so it is proven, not assumed.
cp_assert CP-0702 "previous digest runs against the new schema" \
  ./tools/e2e-drive/compat-probe --env staging --schema new --digest "$(cat "${E2E_OUT}/prev-digest")"

cp_assert CP-0703 "staging deploy succeeded with the built digest" \
  ./tools/e2e-drive/run-workflow --repo "${E2E_REPO}" --workflow deploy-staging.yml \
    --digest "${DIGEST}" --expect success

# CP-0704 Staging /version reports the digest we built. The chain must hold at every hop, not only at the end.
cp_equal CP-0704 "staging /version equals the built digest" \
  "${DIGEST}" "$(./tools/evidence/read-version --env staging --product "${E2E_PRODUCT}")"

cp_assert CP-0705 "staging smoke passed" \
  ./tools/e2e-drive/run-smoke --env staging --product "${E2E_PRODUCT}" --suite verification/smoke/

# CP-0706 Performance mechanism executed and within declared thresholds (Section 31.3, required at high).
cp_assert CP-0706 "performance assertions within declared thresholds" \
  ./tools/evidence/run-performance --env staging --product "${E2E_PRODUCT}" --contract verification/contract.yaml

# CP-0707 Manual UAT by qa-1, reaching the record store through RECORD-VERIFICATION-RESULT and NOT by
#         anyone editing a record file by hand (Section 97.2).
cp_assert CP-0707 "UAT result recorded via RECORD-VERIFICATION-RESULT" \
  gh workflow run record-verification-result.yml -R "${E2E_CP_REPO}" \
    -f product="${E2E_PRODUCT}" -f item="$(cat "${E2E_OUT}/pr")" -f mechanism=manual_uat \
    -f result=pass -f evidence="$(cat "${E2E_OUT}/uat-evidence-url")" -f actor=qa-1

cp_assert CP-0708 "records/uat/ carries the run's UAT record" \
  ./tools/records/find-record --store records/uat --product "${E2E_PRODUCT}" \
    --require result=pass --require-fields record_schema_version,id,product,timestamp \
    --newer-than "${E2E_RUN_START}"

# CP-0709 The UAT record was written by the records-writer credential into the records repository — not by
#         a human, not into the control plane (Section 97.1, D89).
cp_assert CP-0709 "UAT record authored by records-writer in control-plane-records" \
  ./tools/records/verify-author --repo "${E2E_RECORDS_REPO}" \
    --path "$(cat "${E2E_OUT}/uat-record-path")" --expect-author records-writer[bot]
