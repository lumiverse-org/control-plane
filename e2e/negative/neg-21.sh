#!/usr/bin/env bash
# e2e/negative/neg-21.sh — renovate path guard
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-21 "non-Renovate author pushing lockfile to renovate branch rejected" \
  'renovate guard|unauthorized author|authorship guard' \
  ./tools/e2e-drive/push-commit --repo "${E2E_REPO}" --branch renovate/deps --author dev-a --files package-lock.json
