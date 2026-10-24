#!/usr/bin/env bash
# e2e/negative/neg-25.sh — exception expiry
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-25 "exception without expiry date fails validation" \
  'expiry.*required|missing expiry|invalid exception' \
  ./validators/registry/validate-exceptions --file e2e/fixtures/pilot-one/exception-no-expiry.yaml
