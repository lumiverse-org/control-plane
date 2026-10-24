#!/usr/bin/env bash
# e2e/negative/neg-23.sh — machine authority
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-23 "machine account cannot merge approve or deploy" \
  'machine account forbidden|actor gate|cannot merge|cannot approve' \
  ./tools/e2e-drive/machine-action --account machine-bg --action merge --pr "$(cat "${E2E_OUT}/pr")"
