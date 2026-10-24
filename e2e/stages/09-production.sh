#!/usr/bin/env bash
set -euo pipefail
# e2e/stages/09-production.sh
source e2e/lib/checkpoint.sh
DIGEST="$(cat "${E2E_OUT}/digest")"

# CP-0901 The freeze gate evaluates against the DECLARED working calendar and operating timezone, never a
#         runner's local time (Section 97.1) — a Friday-freeze gate resolving against runner local time
#         silently admits the deployments it exists to prevent.
cp_assert CP-0901 "freeze gate resolved against the declared calendar" \
  ./tools/evidence/verify-freeze-evaluation --product "${E2E_PRODUCT}" --expect-source declared-calendar

cp_assert CP-0902 "production deploy succeeded" \
  ./tools/e2e-drive/run-workflow --repo "${E2E_REPO}" --workflow deploy-production.yml \
    --digest "${DIGEST}" --expect success

# CP-0903 THE INVARIANT (#22). No rebuild happened between staging and production. Same digest, and the
#         production job pulled it rather than building it.
cp_assert CP-0903 "production job pulled the digest and ran no build step" \
  ./tools/evidence/verify-no-rebuild --run "$(cat "${E2E_OUT}/prod-run-id")" --digest "${DIGEST}"

# CP-0904 The deployment record and the event are REQUIRED, FAILING steps — a deploy whose record cannot
#         be written is a deploy whose evidence chain does not close (Section 97.2).
cp_assert CP-0904 "deployment record written to records/deployments/" \
  ./tools/records/find-record --store records/deployments --product "${E2E_PRODUCT}" \
    --require "digest=${DIGEST}" --require staging_verified=true --require smoke_result=pass \
    --require-fields id,product,digest,approved_by,approval_event,uat_record

cp_assert CP-0905 "production smoke passed" \
  ./tools/e2e-drive/run-smoke --env production --product "${E2E_PRODUCT}" --suite verification/smoke/

cp_assert CP-0906 "health checks green with dependency detail" \
  bash -c 'curl -sf --cert-type P12 --cert "$OPS_SCRAPE_CERT" "$(./tools/evidence/endpoint --env production --product pilot-one --path /health)" | jq -e ".status==\"ok\" and (.dependencies|length)>0"'

# CP-0907 /version on the LIVE service equals the approved digest (Section 41.2; question 11).
cp_equal CP-0907 "production /version equals the approved digest" \
  "${DIGEST}" "$(./tools/evidence/read-version --env production --product "${E2E_PRODUCT}")"

# CP-0908 Ship, as Section 34.1 redefines it — all eight conditions, including STATE.md.
cp_assert CP-0908 "all eight ship conditions satisfied" \
  ./tools/evidence/check-ship-definition --product "${E2E_PRODUCT}" --digest "${DIGEST}"
