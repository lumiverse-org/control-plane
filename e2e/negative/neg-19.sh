#!/usr/bin/env bash
# e2e/negative/neg-19.sh — a required check that can only pass
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-19 "a required check emitted by a path-filtered job" \
  'skipped|neutral|required context did not report' \
  ./tools/e2e-drive/path-filter-probe --repo "${E2E_REPO}" --job verification-contract --add-path-filter
