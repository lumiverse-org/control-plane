#!/usr/bin/env bash
# e2e/negative/neg-04.sh — a verification contract that cannot fail
set -euo pipefail
source e2e/lib/checkpoint.sh
./tools/e2e-drive/stage-contract --repo "${E2E_REPO}" --replace-with e2e/fixtures/pilot-one/contract-always-passes.yaml
cp_refute NEG-04 "an always-passing contract is rejected as non-discriminating" \
  'seeded[- ]defect passed|SIG-18|contract cannot fail' \
  ./tools/evidence/run-verification-contract --repo "${E2E_REPO}" --with-seeded-defect --expect-discrimination
./tools/e2e-drive/stage-contract --repo "${E2E_REPO}" --restore
