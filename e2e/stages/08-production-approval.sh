#!/usr/bin/env bash
set -euo pipefail
# e2e/stages/08-production-approval.sh
source e2e/lib/checkpoint.sh
DIGEST="$(cat "${E2E_OUT}/digest")"

# CP-0801 No open verification block exists for the change or the product. Production approval and
#         deploy-production.yml fail CLOSED while one does (Section 27).
cp_assert CP-0801 "no open verification-block record" \
  ./tools/records/check-verification-block --product "${E2E_PRODUCT}" --expect none

# CP-0802 Approval is against THIS digest, which has already passed smoke and UAT (Section 27).
cp_assert CP-0802 "production approval recorded against the staging-verified digest" \
  ./tools/e2e-drive/approve-production --product "${E2E_PRODUCT}" --digest "${DIGEST}" --as lead-1

# CP-0803 The approver is not the author (invariant #12; Section 27.1 routing table).
cp_assert CP-0803 "production approver differs from the change author" \
  ./tools/records/verify-approval-identity --digest "${DIGEST}" --author dev-a --expect-not dev-a

# CP-0804 The approval is its own event, distinct from Gate 2 — the two are not one decision.
cp_assert CP-0804 "production_approval_granted event distinct from gate_2_approval" \
  ./tools/records/find-event --type production_approval_granted --product "${E2E_PRODUCT}" \
    --require "payload.digest=${DIGEST}" --require payload.approver=lead-1
