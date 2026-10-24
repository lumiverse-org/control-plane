#!/usr/bin/env bash
# e2e/negative/neg-02.sh — digest immutability (rebuild forbidden)
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-02 "trigger deploy-production.yml with rebuild: true" \
  'rebuild.*(not allowed|forbidden|refused)|never rebuilds' \
  ./tools/e2e-drive/run-workflow --repo "${E2E_REPO}" --workflow deploy-production.yml --digest "$(cat "${E2E_OUT}/digest")" --rebuild true
