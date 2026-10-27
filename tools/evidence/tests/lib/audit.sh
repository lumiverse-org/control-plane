#!/usr/bin/env bash
# The L2 half of the negative-test doctrine's recursive clause
# (protocol/00-test-strategy.md section 4.1 rule 7).
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1

fail=0
# 1. Every gate declaration carries a negative block naming a real, non-empty fixture.
python3 - <<'PY' || fail=1
import glob, os, sys, yaml
bad = []
proves = []
for f in sorted(glob.glob('tools/evidence/gates/GATE-L2-*.yaml')):
    d = yaml.safe_load(open(f, encoding='utf-8'))
    n = (d or {}).get('negative') or {}
    fx = n.get('fixture')
    if not fx or not os.path.isdir(fx) or not os.listdir(fx):
        bad.append((f, 'fixture missing or empty'))
    if not n.get('proves'):
        bad.append((f, 'proves empty'))
    else:
        proves.append(n['proves'])
if len(proves) != len(set(proves)):
    bad.append(('<catalogue>', 'duplicated proves string'))
for f, why in bad:
    print('NEGATIVE-AUDIT-FAIL %s %s' % (f, why))
sys.exit(1 if bad else 0)
PY

# 2. The floor.
A="$(bash tools/evidence/lane-verify.sh   --all 2>/dev/null | tail -1 | sed -E 's/.*assertions=([0-9]+).*/\1/')"
N="$(bash tools/evidence/lane-negative.sh --all 2>/dev/null | tail -1 | sed -E 's/.*negatives_run=([0-9]+).*/\1/')"
FA="$(python3 -c "import yaml;print(yaml.safe_load(open('tools/evidence/tests/coverage-floor.yaml', encoding='utf-8'))['min_assertions'])")"
FN="$(python3 -c "import yaml;print(yaml.safe_load(open('tools/evidence/tests/coverage-floor.yaml', encoding='utf-8'))['min_negatives_run'])")"
[ "${A:-0}" -ge "$FA" ] || { echo "COVERAGE-FLOOR-FAIL assertions=$A floor=$FA"; fail=1; }
[ "${N:-0}" -ge "$FN" ] || { echo "COVERAGE-FLOOR-FAIL negatives_run=$N floor=$FN"; fail=1; }

# 3. The recursive clause: an injected declaration with no negative block MUST be rejected.
T=tools/evidence/gates/GATE-L2-999.yaml
printf 'gate_id: GATE-L2-999\nowner_lane: L2\nlevel: T1\ntitle: audit self-test\n' > "$T"
python3 - <<'PY' >/dev/null 2>&1
import glob, yaml, sys
sys.exit(0 if any((yaml.safe_load(open(f, encoding='utf-8')) or {}).get('negative') is None
                  for f in glob.glob('tools/evidence/gates/GATE-L2-*.yaml')) else 1)
PY
caught=$?
rm -f "$T"
[ "$caught" = "0" ] || { echo "AUDIT-SELF-TEST-FAIL: a declaration with no negative block was not detected"; fail=1; }

[ "$fail" = "0" ] && echo "NEGATIVE-AUDIT OK" || echo "NEGATIVE-AUDIT FAIL"
exit "$fail"
