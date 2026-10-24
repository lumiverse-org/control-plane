#!/usr/bin/env bash
# e2e/negative/neg-09.sh — Gate 1 independence (self-approval)
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-09 "Gate 1 author cannot approve own plan" \
  'self-approval|cannot approve own plan|author == approver' \
  ./tools/gate1/approve --plan-id "$(cat "${E2E_OUT}/plan-id")" --as dev-a
