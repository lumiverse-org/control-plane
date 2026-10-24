#!/usr/bin/env bash
# e2e/negative/neg-03.sh — /version match (hot-patch detection)
set -euo pipefail
source e2e/lib/checkpoint.sh
./tools/e2e-drive/hot-patch-container --env production --product "${E2E_PRODUCT}" --tamper
cp_refute NEG-03 "verify-digest-chain catches hot-patched running container" \
  'mismatch|P0|tampered|digest.*differ' \
  ./tools/evidence/verify-digest-chain --product "${E2E_PRODUCT}" --fail-on-mismatch
./tools/e2e-drive/hot-patch-container --env production --product "${E2E_PRODUCT}" --restore
