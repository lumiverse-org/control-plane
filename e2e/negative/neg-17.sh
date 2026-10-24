#!/usr/bin/env bash
# e2e/negative/neg-17.sh — record write path
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-17 "reconciler credential cannot write to records store" \
  'permission denied|unauthorized|records-writer only' \
  ./tools/records/test-write --store records/deployments --with-credential reconciler
