#!/usr/bin/env bash
# tools/freeze-window-check.sh — Friday freeze and deployment window awareness (§34.2, CP-0005)
set -euo pipefail

NEED_MINUTES=90
CALENDAR="records/leave/company-calendar.yaml"
SIMULATE_TIME=""

while [ $# -gt 0 ]; do
  case "$1" in
    --need-minutes) NEED_MINUTES="$2"; shift 2 ;;
    --calendar) CALENDAR="$2"; shift 2 ;;
    --simulate-calendar-time) SIMULATE_TIME="$2"; shift 2 ;;
    --product) shift 2 ;;
    *) shift ;;
  esac
done

python3 - <<PYEOF
import sys, re, datetime

need_minutes = int("${NEED_MINUTES}")
simulate = "${SIMULATE_TIME}".strip().lower()

# Check simulation
if simulate:
    # Example format: "friday 15:30" or ISO format
    is_friday = "friday" in simulate or "fri" in simulate
    time_match = re.search(r'(\d{1,2}):(\d{2})', simulate)
    if time_match:
        hour, minute = int(time_match.group(1)), int(time_match.group(2))
    else:
        hour, minute = 15, 30
    
    if is_friday:
        dow = 5
    elif "saturday" in simulate or "sat" in simulate:
        dow = 6
    elif "sunday" in simulate or "sun" in simulate:
        dow = 7
    else:
        dow = 1
else:
    # Use real current UTC time
    now = datetime.datetime.now(datetime.timezone.utc)
    dow = now.isoweekday() # 1=Mon .. 7=Sun
    hour = now.hour
    minute = now.minute

now_minutes = hour * 60 + minute
core_start_minutes = 9 * 60   # 09:00
core_end_minutes = 18 * 60    # 18:00
friday_freeze_minutes = 15 * 60 # 15:00

# 1. Weekend check
if dow in (6, 7):
    print(f"FREEZE: Current time ({hour:02d}:{minute:02d} DOW {dow}) is on a weekend (outside core hours). No compliant production deploy window exists.")
    sys.exit(1)

# 2. Friday freeze rule (§34.2)
if dow == 5:
    if now_minutes >= friday_freeze_minutes:
        print(f"FREEZE: Cannot deploy: Friday freeze in effect after 15:00 (current: {hour:02d}:{minute:02d}). Outside core hours and observation window cannot complete.")
        sys.exit(1)
    if now_minutes + need_minutes > core_end_minutes:
        print(f"FREEZE: Cannot deploy: deployment plus observation window ({need_minutes}m) exceeds core hours end (18:00). Observation window cannot complete inside core hours.")
        sys.exit(1)

# 3. Mon-Thu working hours check
if now_minutes < core_start_minutes or now_minutes > core_end_minutes:
    print(f"FREEZE: Current time ({hour:02d}:{minute:02d}) is outside core hours (09:00 - 18:00). No compliant window exists.")
    sys.exit(1)

if now_minutes + need_minutes > core_end_minutes:
    print(f"FREEZE: Deployment plus observation window ({need_minutes}m) exceeds core hours end (18:00). Observation window cannot complete inside core hours.")
    sys.exit(1)

print(f"FREEZE-WINDOW OPEN: Compliant {need_minutes}-minute production deployment window available.")
sys.exit(0)
PYEOF
