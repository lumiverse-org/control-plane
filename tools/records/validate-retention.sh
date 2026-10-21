#!/usr/bin/env bash
# validate-retention.sh — Master Spec v4.0 §97.6, Invariant 47
# Validates store retention classes.
# Prints RETENTION OK on pass; exits non-zero on failure.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CP_ROOT="${CONTROL_PLANE_ROOT:-$(cd "$HERE/../.." && pwd)}"
L4_PY="${L4_PY:-python}"

RETENTION_FILE="$CP_ROOT/metrics/retention/retention-classes.yaml"
if [[ ! -f "$RETENTION_FILE" ]]; then
  echo "RETENTION FAIL: $RETENTION_FILE not found"
  exit 1
fi

"$L4_PY" - "$RETENTION_FILE" <<'PYEOF'
import sys
import yaml

path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
except Exception as exc:
    print(f"RETENTION FAIL: unreadable {path}: {exc}")
    sys.exit(1)

stores = doc.get("stores", [])
if not stores:
    print(f"RETENTION FAIL: no stores found in {path}")
    sys.exit(1)

failures = []

for s in stores:
    sid = s.get("id") or s.get("path") or "<unnamed>"

    # Rule 1: every store must have a non-blank retention_class
    rc = s.get("retention_class", "")
    if not rc:
        failures.append(f"{sid}: missing or blank retention_class")
        continue

    # Rule 2: permanent stores must carry permanence: true
    if rc == "permanent":
        if s.get("permanence") is not True:
            failures.append(f"{sid}: retention_class=permanent but permanence is not true (invariant 47)")

    # Rule 3: diagnostic stores must carry a positive integer diagnostic_window_days
    if rc == "diagnostic":
        wd = s.get("diagnostic_window_days")
        if not isinstance(wd, int) or wd <= 0:
            failures.append(f"{sid}: retention_class=diagnostic but diagnostic_window_days is missing or non-positive")

    # Rule 4: attention-session-raw (§97.6 named store) must be diagnostic with window declared
    if sid == "attention-session-raw":
        if rc != "diagnostic":
            failures.append(f"{sid}: §97.6 requires this store to be retention_class=diagnostic, found '{rc}'")
        wd = s.get("diagnostic_window_days")
        if not isinstance(wd, int) or wd <= 0:
            failures.append(f"{sid}: §97.6 requires declared diagnostic_window_days (positive integer)")

if failures:
    print(f"RETENTION FAIL: {len(failures)} violation(s):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print(f"RETENTION OK ({len(stores)} stores validated)")
sys.exit(0)
PYEOF
