#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
set +e
python3 -m tools.evidence.evidence_chain \
  --deployment "$ROOT/tools/evidence/tests/fixtures/gate-l2-008/deployment-gap.yaml" --summary \
  >"$HERE/out.txt" 2>"$HERE/err.txt"
RC=$?
set -e
test "$RC" -eq 2
grep -q 'q1_git_commit' "$HERE/err.txt"
rm -f "$HERE/out.txt" "$HERE/err.txt"
exit 0
