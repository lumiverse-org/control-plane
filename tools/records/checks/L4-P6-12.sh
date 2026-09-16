#!/usr/bin/env bash
set -euo pipefail
# Check: L4-P6-12 - five-minute collection-cost cap assertion
# Section 67.3 line 5605 / Section 97.4 line 8980: the declared collection cost
# per person per week is asserted at or under 5 minutes. A design exceeding it
# fails the check rather than being accepted.
HERE="$(cd "$(dirname "$0")" && pwd)"
CP_DIR="$(cd "$HERE/../../.." && pwd)"
CC="$CP_DIR/metrics/attention/collection_cost.py"
TD="$CP_DIR/metrics/attention/test-derivation.sh"
VAC="$CP_DIR/metrics/attention/validate-attention-config.sh"
[[ -f "$CC" ]]  || { echo "ABSENT: $CC" >&2; exit 1; }
[[ -f "$TD" ]]  || { echo "ABSENT: $TD" >&2; exit 1; }
[[ -f "$VAC" ]] || { echo "ABSENT: $VAC" >&2; exit 1; }

# Positive: the ledger's own declared cap is at or under five minutes.
python3 "$CC" | grep -q '^COST-CAP OK' || { echo "collection_cost.py did not report OK on the real calibration" >&2; exit 1; }

# Positive: the harness's --cost-cap mode passes end to end.
bash "$TD" --cost-cap >/dev/null || { echo "test-derivation.sh --cost-cap failed" >&2; exit 1; }

# neg fixture: a design declaring 6 minutes/person/week must be rejected, not accepted.
if python3 "$CC" --minutes 6 >/dev/null 2>&1; then
  echo "neg-fixture: a 6-minute design was accepted; the cap should reject it" >&2
  exit 1
fi

# bad_fixture: a calibration file with the cap raised above 5 minutes must be
# rejected by the config validator (proves the cap is enforced, not decorative).
TMP=$(mktemp -d)
cp "$CP_DIR/metrics/attention/taxonomy.yaml" "$CP_DIR/metrics/attention/sources.yaml" \
   "$CP_DIR/metrics/attention/calibration.yaml" "$CP_DIR/metrics/attention/validate-attention-config.sh" "$TMP/"
python3 - "$TMP/calibration.yaml" <<'PY'
import sys, yaml
p = sys.argv[1]
d = yaml.safe_load(open(p, encoding="utf-8"))
d["self_report_cap_minutes_per_person_per_week"]["value"] = 10
yaml.safe_dump(d, open(p, "w", encoding="utf-8"), sort_keys=False)
PY
if bash "$TMP/validate-attention-config.sh" >/dev/null 2>&1; then
  echo "bad_fixture: a cap raised to 10 minutes was accepted by validate-attention-config.sh" >&2
  rm -rf "$TMP"
  exit 1
fi
rm -rf "$TMP"

echo "CHECK L4-P6-12 PASS"
