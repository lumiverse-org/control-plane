#!/usr/bin/env bash
# e2e/negative/neg-27.sh — deployment record
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-27 "production deploy aborts when deployment record write fails" \
  'deployment record.*failed|record write required|evidence chain broken' \
  ./tools/e2e-drive/run-workflow --repo "${E2E_REPO}" --workflow deploy-production.yml --digest "$(cat "${E2E_OUT}/digest")" --simulate-record-failure
