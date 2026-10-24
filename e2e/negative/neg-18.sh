#!/usr/bin/env bash
# e2e/negative/neg-18.sh — the reconciler that finds nothing
set -euo pipefail
source e2e/lib/checkpoint.sh
[ ! -x ./tools/e2e-drive/canary-probe ] || ./tools/e2e-drive/canary-probe --remove 2>/dev/null || true
cp_refute NEG-18 "a reconciliation run reporting zero findings" \
  'canary not found|zero findings|SIG-13|FAILED run' \
  ./reconciler/run --mode detect --record --expect-canary
[ ! -x ./tools/e2e-drive/canary-probe ] || ./tools/e2e-drive/canary-probe --restore 2>/dev/null || true
cp_assert NEG-18b "canary restored and found again" \
  ./reconciler/run --mode detect --expect-canary
