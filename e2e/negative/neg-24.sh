#!/usr/bin/env bash
# e2e/negative/neg-24.sh — parity
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-24 "staging-only env var causes parity violation blocking deploy" \
  'parity violation|environment mismatch|staging.*prod.*differ' \
  ./tools/evidence/check-parity --repo "${E2E_REPO}" --staging-extra-var STAGING_ONLY_VAR=1
