#!/usr/bin/env bash
# L4 suite 5 - attention-hour derivation. MasterSpec v4.0 Section 97.4 lines 8954-8981.
# Expected values are fixed by L4-07-tests-and-runbook.md task L4-P7-T09. Never edit them
# to make a run pass: a mismatch is a defect in metrics/attention/derive.py, not here.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; CP="$(cd "$HERE/../.." && pwd)"
. "$CP/tools/records/test/lib.sh"
IN="$CP/tools/records/fixtures/attention/input"
EX="$CP/tools/records/fixtures/attention/expected"
NORM='import sys,json;print(json.dumps(json.load(open(sys.argv[1])),sort_keys=True,separators=(",",":")))'

if [ "${1:-}" = "--provenance" ]; then
  out="$(python3 "$CP/metrics/attention/derive.py" --input "$IN/dc-8.yaml" --json 2>/dev/null)"
  n="$(printf '%s' "$out" | python3 -c 'import sys,json;d=json.load(sys.stdin);print(sum(1 for r in d["apportioned"] if r.get("provenance")=="self-reported"))')"
  if [ "$n" = "3" ]; then echo "PROVENANCE OK"; exit 0; else echo "PROVENANCE FAIL labelled=$n expected=3"; exit 1; fi
fi

# L4-P6-12 - five-minute collection-cost cap assertion (Section 67.3 line 5605 /
# Section 97.4 line 8980). collection_cost.py holds no threshold literal; it reads
# the cap through lib/config.py's load_calibration(), same as every other module here.
if [ "${1:-}" = "--cost-cap" ]; then
  ok=0; total=0
  CC="$CP/metrics/attention/collection_cost.py"
  # 1: a five-minute design is at the cap and must be accepted.
  total=$((total+1))
  python3 "$CC" --minutes 5 >/dev/null 2>&1 && ok=$((ok+1))
  # 2: a six-minute design exceeds the cap and must be rejected, not accepted.
  total=$((total+1))
  python3 "$CC" --minutes 6 >/dev/null 2>&1 || ok=$((ok+1))
  # 3: the ledger's own declared cap must itself be at or under five minutes.
  total=$((total+1))
  python3 "$CC" >/dev/null 2>&1 && ok=$((ok+1))
  if [ "$ok" -eq "$total" ]; then
    echo "COST-CAP OK $ok/$total"; exit 0
  fi
  echo "COST-CAP FAIL $ok/$total"; exit 1
fi

for c in 1 2 3 4 5 6 7 8; do
  id="DC-$c"
  got="$(python3 "$CP/metrics/attention/derive.py" --input "$IN/dc-$c.yaml" --json 2>/dev/null \
        | python3 -c 'import sys,json;print(json.dumps(json.load(sys.stdin),sort_keys=True,separators=(",",":")))')"
  want="$(python3 -c "$NORM" "$EX/dc-$c.json")"
  assert_eq "$id" "$want" "$got"
done
assert_rejects "DC-9" python3 "$CP/metrics/attention/derive.py" --input "$IN/dc-9.yaml" --json

if [ "$L4_FAIL" -eq 0 ]; then echo "ATTENTION OK"; exit 0; else echo "ATTENTION FAIL $L4_FAIL of 9"; exit 1; fi
