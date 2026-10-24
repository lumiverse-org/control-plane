#!/usr/bin/env bash
# e2e/negative/neg-07.sh — plan-checker (non-existent symbol)
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-07 "plan referencing non-existent symbol is rejected" \
  'symbol.*not found|does not exist in source|unknown symbol' \
  ./tools/gate1/plan-check --plan e2e/fixtures/pilot-one/plan-bad-symbol.md --repo "${E2E_REPO}"
