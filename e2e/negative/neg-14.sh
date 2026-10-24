#!/usr/bin/env bash
# e2e/negative/neg-14.sh — production approval ordering
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-14 "production approval rejected before staging verification completes" \
  'staging verification.*not completed|unverified digest|staging required' \
  ./tools/e2e-drive/approve-production --product "${E2E_PRODUCT}" --digest "${FOREIGN:-$(cat "${E2E_OUT}/digest")-unverified}" --as lead-1
