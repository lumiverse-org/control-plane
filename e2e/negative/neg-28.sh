#!/usr/bin/env bash
# e2e/negative/neg-28.sh — customer data
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-28 "fixture containing customer data is detected and rejected" \
  'customer data|PII detected|fixture provenance' \
  ./tools/evidence/check-no-customer-data --fixture e2e/fixtures/pilot-one/customer-data-fixture.json
