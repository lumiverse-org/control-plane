#!/usr/bin/env bash
# e2e/negative/neg-26.sh — auto-repair direction
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-26 "auto-repair refuses to move toward looser control" \
  'stricter-only|cannot relax|looser control rejected' \
  ./reconciler/auto-repair --control branch_protection --direction loosen
