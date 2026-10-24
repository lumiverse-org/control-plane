#!/usr/bin/env bash
# e2e/negative/neg-10.sh — Gate 2 independence (author approves own PR)
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-10 "Gate 2 author cannot approve own PR" \
  'author cannot approve|self-review|non-author approval required' \
  ./tools/e2e-drive/approve-pr --pr "$(cat "${E2E_OUT}/pr")" --as dev-a
