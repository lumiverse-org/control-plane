#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
set +e
python3 -m tools.evidence.seeded_defect \
  --result "$ROOT/tools/evidence/tests/fixtures/gate-l2-003/seed-slipped.json" --summary \
  >"$HERE/out.txt" 2>"$HERE/err.txt"
RC=$?
set -e
grep -q 'SIG-18' "$HERE/err.txt"
test "$RC" -eq 2
rm -f "$HERE/out.txt" "$HERE/err.txt"
exit 0
