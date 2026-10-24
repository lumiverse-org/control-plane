#!/usr/bin/env bash
set -euo pipefail
# e2e/stages/03-verification-contract.sh
source e2e/lib/checkpoint.sh

cp_assert CP-0301 "verification/contract.yaml present and schema-valid" \
  ./validators/registry/validate-verification-contract --repo "${E2E_REPO}"

# CP-0302 reliability_criticality: high ⇒ the performance mechanism is REQUIRED (Section 31.3).
cp_assert CP-0302 "performance mechanism declared" \
  bash -c 'gh api repos/${E2E_REPO}/contents/verification/contract.yaml --jq .content | base64 -d | yq -e ".mechanisms.performance == \"required\"" -'

# CP-0303 A seeded-defect case is declared (Section 31.2).
cp_assert CP-0303 "seeded-defect case declared in contract.yaml" \
  bash -c 'gh api repos/${E2E_REPO}/contents/verification/contract.yaml --jq .content | base64 -d | yq -e ".seeded_defect.path != null" -'

# CP-0304 THE CHECK THAT CAN FAIL. Run the contract against the seeded defect. The contract MUST fail it.
#         A run in which the seeded defect PASSES is a FAILED run, raises SIG-18, and is Blocking for the
#         product until the case fails again. This is the same logic AT-102 applies to the reconciler.
cp_refute CP-0304 "verification contract rejects its seeded defect" \
  'seeded[- ]defect|assertion failed|FAIL' \
  ./tools/evidence/run-verification-contract --repo "${E2E_REPO}" --with-seeded-defect

# CP-0305 …and passes on the clean tree, so CP-0304 is discrimination, not a contract that always fails.
cp_assert CP-0305 "verification contract passes on the clean tree" \
  ./tools/evidence/run-verification-contract --repo "${E2E_REPO}"

# CP-0306 Coverage mapping exists and uat.md is stubbed at plan time (Section 31.2).
cp_assert CP-0306 "coverage map resolves every requirement to a check" \
  ./tools/evidence/check-coverage-map --repo "${E2E_REPO}" --fail-on-unmapped
