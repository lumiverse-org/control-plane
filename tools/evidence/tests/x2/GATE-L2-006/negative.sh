#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
set +e
python3 -m tools.evidence.timegate \
  --at 2026-09-11T09:31:00Z --tz Asia/Kolkata --profile business-hours --summary \
  >"$HERE/out.txt" 2>"$HERE/err.txt"
RC=$?
set -e
test "$RC" -eq 2
grep -q 'FAIL' "$HERE/err.txt"
rm -f "$HERE/out.txt" "$HERE/err.txt"
exit 0
