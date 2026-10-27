#!/usr/bin/env bash
# Three broken contexts against the three named privileged workflows.
# The fourth workflow is the rollback filename from contracts. If that key is
# absent, D-L2-05 stays unresolved: the line is recorded and no filename is chosen.
set -uo pipefail
cd "$(dirname "$0")/../../../../.." || exit 1
WFS="deploy-production.yml migrate.yml restore-production.yml"
RB="$(python3 -c "import glob,yaml,sys
for f in glob.glob('contracts/**/*.y*ml', recursive=True):
    try: d=yaml.safe_load(open(f, encoding='utf-8'))
    except Exception: continue
    if isinstance(d,dict) and d.get('rollback_workflow_filename'):
        print(d['rollback_workflow_filename']); sys.exit(0)
" 2>/dev/null || true)"
if [ -n "$RB" ]; then
  WFS="$WFS $RB"
else
  echo "ROLLBACK_WORKFLOW_FILENAME UNRESOLVED (D-L2-05)" >&2
fi
any_fail=0
STDERR_FILE=$(mktemp)
for c in shared-pool non-ephemeral unresolvable; do
  ctx="tools/evidence/tests/negative/NT-05/$c/context.env"
  EXPECT_TOKEN="$(bash -c '. "$1" && echo "${EXPECT_TOKEN:-}"' -- "$ctx")"
  for w in $WFS; do
    ( set -a; . "$ctx"; set +a
      python3 -m tools.evidence.assert_runner_tier --workflow "$w" --summary >/dev/null ) 2>"$STDERR_FILE"
    rc=$?
    [ "$rc" = "2" ] || { echo "NEG FAIL: $c/$w: expected exit 2, got $rc"; any_fail=1; }
    grep -q "${EXPECT_TOKEN}" "$STDERR_FILE" \
      || { echo "NEG FAIL: $c/$w: expected token '${EXPECT_TOKEN}' not found"; any_fail=1; }
  done
done
rm -f "$STDERR_FILE"
[ "$any_fail" = "0" ] && echo "NEG OK" && exit 0
exit 1
