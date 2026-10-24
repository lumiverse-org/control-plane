#!/usr/bin/env bash
# tools/freeze-window-check.sh — Friday freeze and deployment window awareness (§34.2, CP-0005, FD-092)
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

python3 - "$CALENDAR" "$NEED_MINUTES" "$SIMULATE_TIME" <<'PYEOF'
import sys, re, os, datetime
import yaml

calendar_path = sys.argv[1]
need_minutes = int(sys.argv[2])
simulate = sys.argv[3].strip().lower()

# Check calendar file
if not os.path.exists(calendar_path):
    print(f"FREEZE: Declared calendar file '{calendar_path}' not found — failing closed.")
    sys.exit(1)

try:
    with open(calendar_path, "r", encoding="utf-8") as f:
        cal = yaml.safe_load(f) or {}
except Exception as e:
    print(f"FREEZE: Failed to parse calendar '{calendar_path}': {e} — failing closed.")
    sys.exit(1)

# Extract declared parameters from calendar
core_start_str = cal.get("core_hours", {}).get("start", "09:00")
core_end_str = cal.get("core_hours", {}).get("end", "18:00")
friday_freeze_str = cal.get("friday_freeze_start", "15:00")
working_days_list = cal.get("working_days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
public_holidays = set(cal.get("public_holidays") or [])
timezone_str = cal.get("operating_timezone", "UTC")

def time_to_minutes(t_str):
    parts = t_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])

core_start_minutes = time_to_minutes(core_start_str)
core_end_minutes = time_to_minutes(core_end_str)
friday_freeze_minutes = time_to_minutes(friday_freeze_str)

day_map = {
    "monday": 1, "tuesday": 2, "wednesday": 3, "thursday": 4,
    "friday": 5, "saturday": 6, "sunday": 7
}
working_dows = set(day_map[d.lower()] for d in working_days_list if d.lower() in day_map)

# Check simulation or current UTC time
if simulate:
    is_friday = "friday" in simulate or "fri" in simulate
    is_sat = "saturday" in simulate or "sat" in simulate
    is_sun = "sunday" in simulate or "sun" in simulate
    
    time_match = re.search(r'(\d{1,2}):(\d{2})', simulate)
    if time_match:
        hour, minute = int(time_match.group(1)), int(time_match.group(2))
    else:
        hour, minute = 15, 30
    
    if is_friday:
        dow = 5
    elif is_sat:
        dow = 6
    elif is_sun:
        dow = 7
    elif "mon" in simulate:
        dow = 1
    elif "tue" in simulate:
        dow = 2
    elif "wed" in simulate:
        dow = 3
    elif "thu" in simulate:
        dow = 4
    else:
        dow = 1
    
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', simulate)
    current_date_str = date_match.group(1) if date_match else None
else:
    now = datetime.datetime.now(datetime.timezone.utc)
    dow = now.isoweekday() # 1=Mon .. 7=Sun
    hour = now.hour
    minute = now.minute
    current_date_str = now.strftime("%Y-%m-%d")

now_minutes = hour * 60 + minute

# 0. Public holiday check
if current_date_str and current_date_str in public_holidays:
    print(f"FREEZE: Declared date ({current_date_str}) is a public holiday in {calendar_path}. Production deploy window closed.")
    sys.exit(1)

# 1. Non-working day / weekend check
if dow not in working_dows:
    print(f"FREEZE: Current day (DOW {dow}, {hour:02d}:{minute:02d} {timezone_str}) is not a working day in {calendar_path}. No compliant production deploy window exists.")
    sys.exit(1)

# 2. Friday freeze rule (§34.2, declared friday_freeze_start)
if dow == 5:
    if now_minutes >= friday_freeze_minutes:
        print(f"FREEZE: Cannot deploy: Friday freeze in effect after {friday_freeze_str} {timezone_str} (current: {hour:02d}:{minute:02d}). Outside core hours and observation window cannot complete.")
        sys.exit(1)
    if now_minutes + need_minutes > core_end_minutes:
        print(f"FREEZE: Cannot deploy: deployment plus observation window ({need_minutes}m) exceeds core hours end ({core_end_str} {timezone_str}). Observation window cannot complete inside core hours.")
        sys.exit(1)

# 3. Standard working hours check
if now_minutes < core_start_minutes or now_minutes > core_end_minutes:
    print(f"FREEZE: Current time ({hour:02d}:{minute:02d} {timezone_str}) is outside declared core hours ({core_start_str} - {core_end_str} {timezone_str}). No compliant window exists.")
    sys.exit(1)

if now_minutes + need_minutes > core_end_minutes:
    print(f"FREEZE: Deployment plus observation window ({need_minutes}m) exceeds core hours end ({core_end_str} {timezone_str}). Observation window cannot complete inside core hours.")
    sys.exit(1)

print(f"FREEZE-WINDOW OPEN: Compliant {need_minutes}-minute production deployment window available (calendar: {calendar_path}, {core_start_str}-{core_end_str} {timezone_str}).")
sys.exit(0)
PYEOF

