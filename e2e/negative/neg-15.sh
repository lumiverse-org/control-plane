#!/usr/bin/env bash
# e2e/negative/neg-15.sh — verification block
set -euo pipefail
source e2e/lib/checkpoint.sh
./tools/records/open-verification-block --product "${E2E_PRODUCT}" --reason "test-block" --as qa-1
cp_refute NEG-15 "production deploy fails closed while verification block exists" \
  'verification block|blocked from deploy|fail-closed' \
  ./tools/e2e-drive/run-workflow --repo "${E2E_REPO}" --workflow deploy-production.yml --digest "$(cat "${E2E_OUT}/digest")"
./tools/records/close-verification-block --product "${E2E_PRODUCT}" --as qa-1
