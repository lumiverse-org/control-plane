#!/usr/bin/env bash
# e2e/negative/neg-06.sh — plan-checker (missing verify command)
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-06 "plan with no automated verify command is rejected" \
  'verify command required|automated verify|hard reject' \
  ./tools/gate1/plan-check --plan e2e/fixtures/pilot-one/plan-no-verify.md
