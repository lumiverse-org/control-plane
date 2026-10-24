#!/usr/bin/env bash
# e2e/negative/neg-20.sh — tag pin integrity
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-20 "tag ruleset blocks updating reusable workflow tag" \
  'ruleset.*(prevented|blocked)|cannot update tag|bypass list empty' \
  ./tools/e2e-drive/move-workflow-tag --tag "workflows/v1" --sha "$(git rev-parse HEAD)"
