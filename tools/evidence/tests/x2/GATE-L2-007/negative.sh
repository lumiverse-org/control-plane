#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
FIX="$ROOT/tools/evidence/tests/negative/NT-12/workflow.yml"
set +e
python3 -m tools.evidence.lint_workflow --path "$FIX" --summary \
  >"$HERE/out.txt" 2>"$HERE/err.txt"
RC=$?
set -e
grep -q 'LW-03' "$HERE/err.txt"
test "$RC" -eq 2
rm -f "$HERE/out.txt" "$HERE/err.txt"
exit 0
