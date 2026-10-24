#!/usr/bin/env bash
# e2e/negative/neg-11.sh — Gate 2 staleness (push after approval)
set -euo pipefail
source e2e/lib/checkpoint.sh
[ ! -x ./tools/e2e-drive/push-commit ] || ./tools/e2e-drive/push-commit --repo "${E2E_REPO}" --branch pilot/disable-customer --message "stale commit after approval" 2>/dev/null || true
cp_refute NEG-11 "merge blocked after new push invalidates Gate 2 approval" \
  'stale approval|approval invalidated|new commits pushed' \
  ./tools/e2e-drive/merge-pr --pr "$(cat "${E2E_OUT}/pr")"
