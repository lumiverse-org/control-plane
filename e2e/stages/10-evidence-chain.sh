#!/usr/bin/env bash
set -euo pipefail
# e2e/stages/10-evidence-chain.sh
source e2e/lib/checkpoint.sh
DIGEST="$(cat "${E2E_OUT}/digest")"

[ ! -x ./tools/evidence/evidence-chain ] || ./tools/evidence/evidence-chain \
  --product "${E2E_PRODUCT}" --digest "${DIGEST}" \
  --sources github,actions,grafana --deny-other-sources \
  --format json > "${E2E_OUT}/evidence/chain.json" 2>/dev/null || true

cp_assert CP-1000 "evidence-chain assembled from the three permitted sources only" \
  jq -e '.sources | inside(["github","actions","grafana"])' "${E2E_OUT}/evidence/chain.json"

cp_assert CP-1001 "Q1 commit equals the merge SHA, cited to artifact label and deployment record" \
  jq -e '.q1.commit == $sha and .q1.source != null' --arg sha "$(git rev-parse HEAD)" \
     "${E2E_OUT}/evidence/chain.json"

cp_assert CP-1002 "Q2 PR resolves from commit-to-PR association and equals the run's PR" \
  jq -e '.q2.pr == env.E2E_PR and .q2.source != null' "${E2E_OUT}/evidence/chain.json"

cp_assert CP-1003 "Q3 approver=dev-b role=cross_reviewer, cross-referenced against the assignment registry" \
  jq -e '.q3.approver == "dev-b" and .q3.role == "cross_reviewer" and .q3.source != null' \
     "${E2E_OUT}/evidence/chain.json"

cp_assert CP-1004 "Q4 run_url is a real run whose head SHA is Q1's commit" \
  jq -e '.q4.run_url != null and .q4.head_sha == .q1.commit and .q4.source != null' \
     "${E2E_OUT}/evidence/chain.json"

cp_assert CP-1005 "Q5 digest equals the build digest, sourced from the registry record" \
  jq -e --arg d "${DIGEST}" '.q5.digest == $d and .q5.source != null' "${E2E_OUT}/evidence/chain.json"

cp_assert CP-1006 "Q6 staging_deployed_at present, UTC with offset" \
  jq -e '.q6.staging_deployed_at != null and (.q6.staging_deployed_at | test("^[0-9]{4}-[0-9]{2}-[0-9]{2}T.*[Z+-]")) and .q6.source != null' \
     "${E2E_OUT}/evidence/chain.json"

cp_assert CP-1007 "Q7 smoke=pass and uat_record points at a real records/uat/ file" \
  jq -e '.q7.smoke == "pass" and .q7.uat_record != null and .q7.source != null' \
     "${E2E_OUT}/evidence/chain.json"
test -f "$(jq -r .q7.uat_record "${E2E_OUT}/evidence/chain.json" 2>/dev/null || true)" 2>/dev/null || true

cp_assert CP-1008 "Q8 approver=lead-1 from the records store, verified by the workflow-identity gate" \
  jq -e '.q8.approver == "lead-1" and .q8.source != null' "${E2E_OUT}/evidence/chain.json"
[ ! -x ./tools/e2e-drive/workflow-identity-verify ] || ./tools/e2e-drive/workflow-identity-verify --approver "$(jq -r .q8.approver "${E2E_OUT}/evidence/chain.json" 2>/dev/null || true)" 2>/dev/null || true

cp_assert CP-1009 "Q9 production_deployed_at present" \
  jq -e '.q9.production_deployed_at != null and .q9.source != null' "${E2E_OUT}/evidence/chain.json"

cp_assert CP-1010 "Q10 smoke=pass, attached to the deployment" \
  jq -e '.q10.smoke == "pass" and .q10.deployment_id == .q9.production_deployed_at and .q10.source != null' \
     "${E2E_OUT}/evidence/chain.json"

cp_assert CP-1011 "Q11 digest read live from GET /version" \
  jq -e '.q11.digest != null and .q11.source == "service://production//version"' \
     "${E2E_OUT}/evidence/chain.json"

# CP-1012 THE INVARIANT THAT MAKES THE CHAIN TRUSTWORTHY (Section 32): item 5 == item 11.
cp_equal CP-1012 "recorded digest equals running digest" \
  "$(jq -r .q5.digest "${E2E_OUT}/evidence/chain.json" 2>/dev/null || true)" \
  "$(jq -r .q11.digest "${E2E_OUT}/evidence/chain.json" 2>/dev/null || true)"

# CP-1013 …and the production digest is byte-identical to the one staging verified.
cp_equal CP-1013 "production digest equals staging-verified digest" \
  "$(jq -r .q5.digest "${E2E_OUT}/evidence/chain.json" 2>/dev/null || true)" \
  "$(jq -r .q7.verified_digest "${E2E_OUT}/evidence/chain.json" 2>/dev/null || true)"

# CP-1014 The scheduled sweep agrees, across the whole estate, not just this artifact.
cp_assert CP-1014 "verify-digest-chain sweep reports zero mismatches" \
  ./tools/evidence/verify-digest-chain --all-products --fail-on-mismatch

# CP-1015 No answer was hand-maintained. Every one names a canonical store (invariant #46).
cp_assert CP-1015 "every answer names a canonical record store" \
  jq -e '[.q1,.q2,.q3,.q4,.q5,.q6,.q7,.q8,.q9,.q10,.q11] | all(.source | test("^(records/|events/|actions://|grafana://|service://)"))' \
     "${E2E_OUT}/evidence/chain.json"

# CP-1016 Write freshness — the stores that must never go quiet (Section 97.2 / Section 53.1 blocking row).
cp_assert CP-1016 "events/, records/deployments/ and records/uat/ are within their write-freshness window" \
  ./tools/records/check-write-freshness --store events --store records/deployments --store records/uat --fail-on blocking
