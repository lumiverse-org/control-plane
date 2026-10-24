#!/usr/bin/env bash
# e2e/negative/neg-22.sh — the Friday freeze
set -euo pipefail
source e2e/lib/checkpoint.sh
cp_refute NEG-22 "a production deploy dispatched at 15:30 Friday declared-calendar time" \
  'freeze|outside core hours|observation window' \
  ./tools/freeze-window-check.sh --need-minutes 90 --simulate-calendar-time "friday 15:30"
