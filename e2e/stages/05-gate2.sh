#!/usr/bin/env bash
set -euo pipefail
# e2e/stages/05-gate2.sh
source e2e/lib/checkpoint.sh

cp_assert CP-0501 "branch pushed and PR opened by dev-a" \
  ./tools/e2e-drive/open-pr --repo "${E2E_REPO}" --as dev-a \
    --branch pilot/disable-customer --fixture e2e/fixtures/pilot-one/change/

# CP-0502 Every required status check reports a REAL conclusion. A `skipped` or `neutral` conclusion on a
#         required context is Blocking drift (Section 33.2) — a skip that branch protection counts as
#         satisfied is a check that can only pass.
cp_assert CP-0502 "no required check reports skipped or neutral" \
  ./tools/evidence/check-conclusions --pr "$(cat "${E2E_OUT}/pr")" \
    --required-from templates/protection/service.json --forbid skipped,neutral

# CP-0503 The full CI set ran: unit, integration, build, security scan, licence scan, contract validation,
#         registry validation, parity, verification contract (Section 33.2).
for job in unit integration build security-scan licence-scan contract-validation registry-validation parity verification-contract; do
  cp_assert "CP-0503-${job}" "CI job ${job} concluded success" \
    ./tools/evidence/check-job --pr "$(cat "${E2E_OUT}/pr")" --job "${job}" --expect success
done

# CP-0504 Parity is clean across local, staging and production declarations (Section 33.1).
cp_assert CP-0504 "environment parity clean" \
  ./tools/evidence/check-job --pr "$(cat "${E2E_OUT}/pr")" --job parity --expect success

# CP-0505 Gate 2 by dev-b — independent, not the author (invariants #8, #9).
cp_assert CP-0505 "Gate 2 approved by an independent reviewer" \
  ./tools/e2e-drive/approve-pr --pr "$(cat "${E2E_OUT}/pr")" --as dev-b

cp_assert CP-0506 "gate_2_approval event carries the reviewer role" \
  ./tools/records/find-event --type gate_2_approval --product "${E2E_PRODUCT}" --require payload.reviewer_role=cross_reviewer

# CP-0507 Merge is MECHANICAL once protection is satisfied (Section 27) — it is not a decision and needs
#         no separate authorisation event.
cp_assert CP-0507 "merge succeeds once protection is satisfied" \
  ./tools/e2e-drive/merge-pr --pr "$(cat "${E2E_OUT}/pr")"
