#!/usr/bin/env bash
# e2e/negative/neg-08.sh — plan-checker (slopsquat package)
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-08 "plan adding slopsquat package name is rejected" \
  'slopsquat|illegitimate package|registry check failed' \
  ./tools/gate1/plan-check --plan e2e/fixtures/pilot-one/plan-slopsquat.md
