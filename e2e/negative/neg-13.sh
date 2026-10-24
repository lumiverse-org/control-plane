#!/usr/bin/env bash
# e2e/negative/neg-13.sh — production self-approval
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-13 "the production approver dispatching their own deploy" \
  'approving identity.*(equal|same).*deploying identity|self-approval' \
  ./tools/e2e-drive/run-workflow --repo "${E2E_REPO}" --workflow deploy-production.yml \
    --digest "$(cat "${E2E_OUT}/digest")" --as lead-1 --approved-by lead-1
