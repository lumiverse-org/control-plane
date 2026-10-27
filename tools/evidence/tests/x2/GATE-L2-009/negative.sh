#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
APP="$ROOT/tools/evidence/tests/fixtures/gate-l2-009/approval.yaml"
set +e
python3 -m tools.evidence.identity_gate \
  --approval "$APP" --deployer dev-one --summary \
  >"$HERE/out.txt" 2>"$HERE/err.txt"
RC=$?
set -e
grep -q 'APPROVER_EQUALS_DEPLOYER' "$HERE/err.txt"
test "$RC" -eq 2
set +e
python3 -m tools.evidence.identity_gate \
  --approval "$ROOT/tools/evidence/tests/fixtures/gate-l2-009/missing.yaml" \
  --deployer dev-two --summary >"$HERE/out2.txt" 2>"$HERE/err2.txt"
RC2=$?
set -e
test "$RC2" -eq 3
grep -q 'approval record not found' "$HERE/err2.txt"
rm -f "$HERE/out.txt" "$HERE/err.txt" "$HERE/out2.txt" "$HERE/err2.txt"
exit 0
