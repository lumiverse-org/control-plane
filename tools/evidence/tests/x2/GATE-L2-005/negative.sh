#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/../../../../.." || exit 1
any_fail=0
STDERR_FILE=$(mktemp)
for c in feature-branch unprotected-tag policy-absent policy-too-wide; do
  case_file="tools/evidence/tests/negative/GATE-L2-005/$c/case.json"
  EXPECT_TOKEN="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8')).get('expect_token',''))" "$case_file")"
  python3 -m tools.evidence.env_policy_assert --case "$case_file" --summary >"$STDERR_FILE" 2>&1
  rc=$?
  [ "$rc" = "2" ] || { echo "NEG FAIL: $c: expected exit 2, got $rc"; any_fail=1; }
  grep -q "$EXPECT_TOKEN" "$STDERR_FILE" \
    || { echo "NEG FAIL: $c: expected token '$EXPECT_TOKEN' not found"; any_fail=1; }
done
rm -f "$STDERR_FILE"
[ "$any_fail" = "0" ] && echo "NEG OK" && exit 0
exit 1
