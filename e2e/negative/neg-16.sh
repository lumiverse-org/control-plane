#!/usr/bin/env bash
# e2e/negative/neg-16.sh — environment ref policy
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-16 "deployment from unauthorized branch rejected by environment ref policy" \
  'branch policy|environment ref policy|protected ref required' \
  ./tools/e2e-drive/run-workflow --repo "${E2E_REPO}" --workflow deploy-production.yml --ref refs/heads/unauthorized-branch --digest "$(cat "${E2E_OUT}/digest")"
