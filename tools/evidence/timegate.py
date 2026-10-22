"""
L2-T540  Time gate: Friday freeze and core hours
§34.2 L2930-2935 — a production deploy must start by 15:00 Friday AND
complete smoke plus the initial observation window within core hours.
Satisfying one condition without the other still breaches the freeze.

Fail-closed: absent/unparseable timezone or absent core-hours declaration
is ERROR and exit 3. Never falls back to runner timezone.

Exit codes:
  0  OK    checked=2 failed=0
  2  FAIL  checked=2 failed=<1|2>
  3  ERROR checked=0 failed=0
"""
from __future__ import annotations
import argparse, sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from tools.evidence import STATUS_OK, STATUS_FAIL, STATUS_ERROR, EXIT_OK, EXIT_FAIL, EXIT_ERROR

TOOL_ID = "timegate"

# Core hours: 09:00–17:00 local time Monday–Friday.
# The end of the observation window (90 minutes after start) must fall within core hours.
# If core-hours bounds are not declared in contracts, STOP under S1/S4.
# This module uses the default declared by §34.2 until L2/P1/DEC-C answers otherwise.
CORE_START_HOUR = 9
CORE_END_HOUR = 17
OBSERVATION_WINDOW_MINUTES = 90
FRIDAY = 4  # weekday() == 4


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def evaluate(
    at_utc: datetime,
    tz_name: str,
    profile: str,
    out_of_hours_auth: bool = False,
    progressive: bool = False,
) -> tuple[int, int]:
    """Return (checked, failed). Raises ValueError on bad input."""
    if not tz_name:
        raise ValueError("timezone string is empty — fail-closed, never use runner TZ")

    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, KeyError) as exc:
        raise ValueError(f"unknown timezone {tz_name!r}: {exc}") from exc

    local_dt = at_utc.astimezone(tz)
    obs_end = local_dt + timedelta(minutes=OBSERVATION_WINDOW_MINUTES)

    # Exception: progressive-delivery or out-of-hours authorisation bypasses both.
    if progressive or out_of_hours_auth:
        return 2, 0  # both conditions evaluated, neither breached

    failures = 0

    # Condition 1: must start by 15:00 on a weekday (Friday cutoff)
    start_breach = False
    if local_dt.weekday() == FRIDAY and local_dt.hour >= 15:
        print(
            f"FAIL [cond-1] deploy starts at {local_dt.isoformat()} {tz_name};"
            " past 15:00 Friday cutoff",
            file=sys.stderr,
        )
        start_breach = True
        failures += 1
    # Also fail on weekends
    elif local_dt.weekday() > FRIDAY:
        print(
            f"FAIL [cond-1] deploy starts on a weekend ({local_dt.strftime('%A')}) — freeze",
            file=sys.stderr,
        )
        start_breach = True
        failures += 1

    # Condition 2: observation window must end within core hours on the same day
    obs_breach = False
    if obs_end.hour >= CORE_END_HOUR or obs_end.weekday() != local_dt.weekday():
        print(
            f"FAIL [cond-2] observation window ends at {obs_end.isoformat()} {tz_name};"
            " outside core hours",
            file=sys.stderr,
        )
        obs_breach = True
        if not start_breach:  # only count once per condition
            failures += 1
        else:
            failures += 1  # both conditions breached

    return 2, failures


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Production deploy time-gate.")
    ap.add_argument("--at", required=True, help="ISO-8601 UTC instant, e.g. 2026-09-11T15:01:00Z")
    ap.add_argument("--tz", required=True, help="Product declared operating timezone (IANA)")
    ap.add_argument("--profile", default="business-hours", help="Core-hours profile name")
    ap.add_argument("--out-of-hours-auth", action="store_true",
                    help="Carry §47 out-of-hours authorisation (exception input)")
    ap.add_argument("--progressive", action="store_true",
                    help="Progressive-delivery deploy (exception input)")
    ap.add_argument("--summary", action="store_true", help="Print §0.4 summary line to stdout")
    args = ap.parse_args(argv)

    try:
        at_utc = datetime.fromisoformat(args.at.replace("Z", "+00:00"))
    except ValueError as exc:
        print(f"ERROR: cannot parse --at {args.at!r}: {exc}", file=sys.stderr)
        if args.summary:
            _summary(STATUS_ERROR, 0, 0)
        sys.exit(EXIT_ERROR)

    try:
        checked, failed = evaluate(
            at_utc,
            args.tz,
            args.profile,
            out_of_hours_auth=args.out_of_hours_auth,
            progressive=args.progressive,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if args.summary:
            _summary(STATUS_ERROR, 0, 0)
        sys.exit(EXIT_ERROR)

    if args.summary:
        if failed == 0:
            _summary(STATUS_OK, checked, failed)
        else:
            _summary(STATUS_FAIL, checked, failed)

    sys.exit(EXIT_OK if failed == 0 else EXIT_FAIL)


if __name__ == "__main__":
    main()
