#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../../.." && pwd)"
REC="$ROOT/tools/evidence/tests/fixtures/nt-04/staging-record.yaml"
OTHER="sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
set +e
python3 -m tools.evidence.digest_invariant \
  --requested "$OTHER" --staging-record "$REC" --summary \
  >"$HERE/out.txt" 2>"$HERE/err.txt"
RC=$?
set -e
grep -q 'DIGEST_INVARIANT_VIOLATION' "$HERE/err.txt"
test "$RC" -eq 2
rm -f "$HERE/out.txt" "$HERE/err.txt"
exit 0
