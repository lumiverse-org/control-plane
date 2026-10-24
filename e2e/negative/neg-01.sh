#!/usr/bin/env bash
# e2e/negative/neg-01.sh — digest immutability
set -euo pipefail
source e2e/lib/checkpoint.sh
FOREIGN="$(./tools/e2e-drive/build-unverified-digest --repo "${E2E_REPO}" 2>/dev/null || true)"
cp_refute NEG-01 "production deploy of a digest staging never verified" \
  'digest.*(differ|mismatch|not verified in staging)' \
  ./tools/e2e-drive/run-workflow --repo "${E2E_REPO}" --workflow deploy-production.yml --digest "${FOREIGN}"
