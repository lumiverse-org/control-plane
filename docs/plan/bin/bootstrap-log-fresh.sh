#!/usr/bin/env sh
# =============================================================================
# bootstrap-log-fresh.sh — L0-owned. The Section 95.4 staleness detector, run
# locally until the control-plane CI rule exists (L1, master/06 R-6) and the
# drift classification lands (L3 validators/drift/**).
# Window: 7 days, the initial calibrated value of Section 95.4 (spec L8708),
# changed only by a recorded decision (L0D-17). Override for tests only.
# Exit 0 fresh / 1 stale — Blocking / 2 configuration error — FAIL CLOSED.
# =============================================================================
set -u
CP="${CP:-$PWD}"
WIN="${BOOT_LOG_WINDOW_DAYS:-7}"
DIR="$CP/docs/plan/bootstrap-log"
TODAY="${BOOT_TODAY:-$(date -u +%F)}"
cfgfail() { printf 'BOOTSTRAP-LOG FAIL: configuration error — %s\n' "$1"; exit 2; }
[ -d "$DIR" ] || cfgfail "bootstrap-log directory not found at $DIR"
NEW=$(ls "$DIR"/*.md 2>/dev/null | sed 's#.*/##; s#\.md$##' | LC_ALL=C sort | tail -1)
[ -n "$NEW" ] || { printf 'BOOTSTRAP-LOG STALE age=INFINITE (no entry exists) — Blocking, Section 95.4\n'; exit 1; }
A=$(date -u -d "$TODAY" +%s) || cfgfail "cannot parse today '$TODAY'"
B=$(date -u -d "$NEW" +%s)   || cfgfail "newest entry name '$NEW' is not a date"
AGE=$(( (A - B) / 86400 ))
if [ "$AGE" -le "$WIN" ]; then
  printf 'BOOTSTRAP-LOG FRESH age=%s window=%s newest=%s\n' "$AGE" "$WIN" "$NEW"; exit 0
fi
printf 'BOOTSTRAP-LOG STALE age=%s window=%s newest=%s — Blocking, Section 95.4\n' "$AGE" "$WIN" "$NEW"
exit 1
