#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
PEOPLE="$ROOT/tools/evidence/fixtures/actor/people.yaml"
set +e
python3 -m tools.evidence.actor_gate \
  --actor machine-1 --capability production-approval --people "$PEOPLE" --summary \
  >"$HERE/out.txt" 2>"$HERE/err.txt"
RC=$?
set -e
grep -q 'MACHINE_ACTOR_REJECTED' "$HERE/err.txt"
test "$RC" -eq 2
rm -f "$HERE/out.txt" "$HERE/err.txt"
exit 0
