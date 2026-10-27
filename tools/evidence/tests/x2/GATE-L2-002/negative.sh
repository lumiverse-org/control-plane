#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
FIX="$ROOT/tools/evidence/tests/negative/NT-11"
set +e
python3 -m tools.evidence.check_required_contexts \
  --templates "$FIX" --registry "$FIX/required-checks.yaml" --summary \
  >"$HERE/out.txt" 2>"$HERE/err.txt"
RC=$?
set -e
grep -q 'PATH_FILTER_ON_REQUIRED_CONTEXT' "$HERE/err.txt"
test "$RC" -eq 2
rm -f "$HERE/out.txt" "$HERE/err.txt"
exit 0
