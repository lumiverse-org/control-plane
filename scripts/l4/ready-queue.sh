#!/usr/bin/env bash
# ready-queue.sh — L4 ready queue timing check & miss detector (FD-091/PFD-017, MasterSpec §29.4, §97.5)
# Verifies that items in the 'ready' column do not exceed the configured timing window (default 3 days).
# Usage: bash scripts/l4/ready-queue.sh [--check] [--work-file <path>] [--window-days <n>] [--as-of <date>]
set -euo pipefail

WINDOW=3  # days — FD-091/PFD-017: emit/flag when item exceeds timing window in ready state
CHECK_MODE=true
WORK_FILE="${WORK_FILE:-records/work/open.yaml}"
AS_OF=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) CHECK_MODE=true; shift ;;
    --work-file) WORK_FILE="$2"; shift 2 ;;
    --window-days) WINDOW="$2"; shift 2 ;;
    --as-of) AS_OF="$2"; shift 2 ;;
    *) shift ;;
  esac
done

echo "=== L4 Ready Queue Check ==="
echo "Window: $WINDOW days (FD-091/PFD-017, §29.4)"
echo "Work file: $WORK_FILE"
echo ""

if [[ ! -f "$WORK_FILE" ]]; then
  echo "No work file: $WORK_FILE"
  exit 0
fi

python3 - "$WORK_FILE" "$WINDOW" "$CHECK_MODE" "$AS_OF" <<'PYEOF'
import sys, yaml, datetime

work_file = sys.argv[1]
window_days = float(sys.argv[2])
check_mode = (sys.argv[3].lower() == "true")
as_of_str = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else None

if as_of_str:
    now_dt = datetime.datetime.fromisoformat(as_of_str.replace("Z", "+00:00"))
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=datetime.timezone.utc)
else:
    now_dt = datetime.datetime.now(datetime.timezone.utc)

try:
    with open(work_file, "r", encoding="utf-8") as f:
        d = yaml.safe_load(f) or {}
except Exception as exc:
    print(f"ERROR: failed to parse work file: {exc}")
    sys.exit(1)

items = d.get("items", []) or []
ready_items = [i for i in items if isinstance(i, dict) and i.get("column") == "ready"]
ready_count = len(ready_items)

print(f"Ready items: {ready_count}")
if ready_count == 0:
    print("No ready items — queue miss check not needed")
    sys.exit(0)

overdue_items = []
within_window_items = []

for item in ready_items:
    item_id = item.get("id", "unnamed-item")
    ts_str = (
        item.get("ready_at")
        or item.get("entered_ready_at")
        or item.get("entered_ready")
        or item.get("created_at")
        or item.get("timestamp")
        or item.get("date")
    )
    if not ts_str:
        # Item has no timestamp to calculate age
        within_window_items.append((item_id, 0.0, "no timestamp provided"))
        continue
    
    try:
        item_dt = datetime.datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
        if item_dt.tzinfo is None:
            item_dt = item_dt.replace(tzinfo=datetime.timezone.utc)
        age_days = (now_dt - item_dt).total_seconds() / 86400.0
        if age_days > window_days:
            overdue_items.append((item_id, age_days, str(ts_str)))
        else:
            within_window_items.append((item_id, age_days, str(ts_str)))
    except Exception as exc:
        within_window_items.append((item_id, 0.0, f"unparseable timestamp: {ts_str}"))

if overdue_items:
    print(f"FLAGGED: {len(overdue_items)} ready item(s) exceed {window_days}-day window:")
    for item_id, age, ts in overdue_items:
        print(f"  - {item_id}: age {age:.1f} days (entered ready: {ts})")
    if check_mode:
        sys.exit(1)
    sys.exit(0)
else:
    print(f"PASS: all {ready_count} ready item(s) are within the {window_days}-day window")
    sys.exit(0)
PYEOF

echo ""
echo "Done"
