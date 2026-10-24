#!/usr/bin/env bash
# e2e/negative/neg-05.sh — plan-checker (missing rollback strategy)
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-05 "schema-touching plan with no rollback strategy is rejected" \
  'rollback strategy required|hard reject|schema.*rollback' \
  ./tools/gate1/plan-check --plan e2e/fixtures/pilot-one/plan-no-rollback.md --change-class normal
