#!/usr/bin/env bash
set -euo pipefail
# e2e/stages/11-rollback-restore.sh
source e2e/lib/checkpoint.sh
PREV="$(cat "${E2E_OUT}/prev-digest")"; DIGEST="$(cat "${E2E_OUT}/digest")"

# CP-1101 Rollback is exempt from production approval, runs from a human identity holding
#         incident-response or production-approval, and is recorded as an exceptional authorisation
#         (Section 27.2).
cp_assert CP-1101 "rollback to the previous approved digest succeeds" \
  ./tools/e2e-drive/run-workflow --repo "${E2E_REPO}" --workflow rollback.yml \
    --to-digest "${PREV}" --as lead-1 --expect success

cp_equal CP-1102 "/version reports the rolled-back digest" \
  "${PREV}" "$(./tools/evidence/read-version --env production --product "${E2E_PRODUCT}")"

cp_assert CP-1103 "rollback recorded as an exceptional authorisation with from- and to-digest" \
  ./tools/records/find-event --type rollback_initiated \
    --require "payload.from_digest=${DIGEST}" --require "payload.to_digest=${PREV}"

cp_assert CP-1104 "roll forward to the approved digest" \
  ./tools/e2e-drive/run-workflow --repo "${E2E_REPO}" --workflow deploy-production.yml \
    --digest "${DIGEST}" --expect success

# CP-1105 AT-103 — production restore executes end to end with NO credential handed to or typed by a human.
cp_assert CP-1105 "restore-production.yml runs with a scoped run identity and no human credential" \
  ./tools/e2e-drive/run-workflow --repo "${E2E_REPO}" --workflow restore-production.yml \
    --authorisation "$(./tools/records/open-exceptional-auth --type restore_scope --as lead-1)" \
    --assert-no-human-credential --expect success

cp_assert CP-1106 "restore-test record carries integrity_check and a named verifier" \
  ./tools/records/find-record --store records/restore-tests --product "${E2E_PRODUCT}" \
    --require-present integrity_check --require-present verified_by --require result=pass

# CP-1107 product.yaml restore_tested now matches a real record (Section 53.1 blocking row; invariant #4).
cp_assert CP-1107 "restore_tested date matches a passing record" \
  ./validators/drift/check-restore-tested --product "${E2E_PRODUCT}" --fail-on-unevidenced

# CP-1108 Every production bug becomes a permanent regression test (invariant #2). The pilot run plants one
#         defect, files it, fixes it, and asserts the regression test now exists and fails without the fix.
cp_refute CP-1108 "the planted defect's regression test fails without the fix" \
  'regression|assertion failed|FAIL' \
  ./tools/evidence/run-regression --repo "${E2E_REPO}" --test regression/pilot-001 --without-fix
