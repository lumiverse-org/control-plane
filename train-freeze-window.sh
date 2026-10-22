#!/usr/bin/env sh
# train-freeze-window.sh — L0-owned. Friday 15:00 deployment freeze (Section 94.8, spec L8586).
# Prints FREEZE-WINDOW OPEN or FREEZE-WINDOW CLOSED. Exit 0 open, 1 closed.
set -eu
DOW=$(date +%u); HOUR=$(date +%H)
if [ "$DOW" -gt 5 ] || { [ "$DOW" -eq 5 ] && [ "$HOUR" -ge 15 ]; }; then
  echo "FREEZE-WINDOW CLOSED"; exit 1
fi
echo "FREEZE-WINDOW OPEN"; exit 0
