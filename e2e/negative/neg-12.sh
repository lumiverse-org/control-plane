#!/usr/bin/env bash
# e2e/negative/neg-12.sh — Read-only approval
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-12 "Read-only permission holder approval does not satisfy protection" \
  'insufficient permissions|write required|read-only approval' \
  ./tools/e2e-drive/approve-pr --pr "$(cat "${E2E_OUT}/pr")" --as dev-readonly
