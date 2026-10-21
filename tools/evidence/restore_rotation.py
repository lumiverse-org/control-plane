"""
tools.evidence.restore_rotation
L2-T552: Restore-rotation scheduler computation (§44.2 L3993-4002)

Deterministic date arithmetic only.
The rotation is computed, never remembered.
The restore_tested date is derived, not declared.
A hand-edited date is drift, not evidence.

Windows: critical = 30 days, all others = 90 days (the floor — never wider).

Exit codes per §0.4: 0=OK, 2=FAIL, 3=ERROR
"""
import argparse
import sys
import os
import glob
from datetime import date, timedelta

try:
    import yaml
except ImportError:
    print("ERROR restore_rotation checked=0 failed=0")
    sys.exit(3)

TOOL_ID = "restore_rotation"

WINDOW_CRITICAL_DAYS = 30
WINDOW_FLOOR_DAYS = 90  # never wider


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def _get_window_days(criticality: str) -> int:
    """Returns the window in days. classification.reliability_criticality may only tighten."""
    if criticality == "critical":
        return WINDOW_CRITICAL_DAYS
    # All other values use the 90-day floor; no code path produces a deadline beyond 90 days
    return WINDOW_FLOOR_DAYS


def _derive_restore_tested(product_name: str, records_dir: str) -> date | None:
    """
    Derives the restore_tested date from the newest passing record in records/restore-tests/.
    Never uses a hand-declared value.
    """
    pattern = os.path.join(records_dir, f"{product_name}-*.yaml")
    files = sorted(glob.glob(pattern), reverse=True)
    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as fh:
                rec = yaml.safe_load(fh) or {}
            if rec.get("result") == "pass" and rec.get("tested_date"):
                return date.fromisoformat(str(rec["tested_date"]))
        except Exception:  # noqa: BLE001
            continue
    return None


def compute(estate_path: str, as_of_str: str, records_dir: str) -> tuple[int, int]:
    """
    Returns (checked, failed).
    """
    try:
        as_of = date.fromisoformat(as_of_str)
    except ValueError as exc:
        print(f"ERROR: invalid --as-of date: {exc}", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    if not os.path.exists(estate_path):
        print(f"ERROR: estate file not found: {estate_path}", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    try:
        with open(estate_path, "r", encoding="utf-8") as fh:
            estate = yaml.safe_load(fh)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot parse estate: {exc}", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    products = estate.get("products", [])
    checked = len(products)
    failed = 0

    for product in products:
        name = product.get("name", "unknown")
        criticality = product.get("classification", {}).get("reliability_criticality", "standard")
        declared_restore_tested = product.get("restore_tested")

        window_days = _get_window_days(criticality)

        # Derive restore_tested from records — never use declared value
        derived_date = _derive_restore_tested(name, records_dir)

        # Check for hand-edited date drift
        if declared_restore_tested and derived_date:
            declared_as_date = date.fromisoformat(str(declared_restore_tested))
            if declared_as_date != derived_date:
                print(
                    f"FAIL: product '{name}' — declared restore_tested '{declared_restore_tested}' "
                    f"differs from derived date '{derived_date}' (§44.2: a hand-edited date is drift)",
                    file=sys.stderr,
                )
                failed += 1
                continue

        if derived_date is None:
            print(
                f"FAIL: product '{name}' has no passing restore record — "
                f"window={window_days}d (criticality={criticality})",
                file=sys.stderr,
            )
            failed += 1
            continue

        deadline = derived_date + timedelta(days=window_days)
        days_remaining = (deadline - as_of).days

        if days_remaining < 0:
            print(
                f"FAIL: product '{name}' is past its {window_days}-day restore window — "
                f"last tested {derived_date}, deadline {deadline} ({abs(days_remaining)} days overdue)",
                file=sys.stderr,
            )
            failed += 1
        else:
            print(
                f"OK: product '{name}' — last tested {derived_date}, "
                f"deadline {deadline} ({days_remaining} days remaining)",
                file=sys.stderr,
            )

    return checked, failed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--estate", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--records-dir", default="records/restore-tests")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    records_dir = args.records_dir
    if records_dir == "records/restore-tests":
        estate_dir = os.path.dirname(args.estate)
        candidate = os.path.join(estate_dir, "records")
        if os.path.isdir(candidate):
            records_dir = candidate

    checked, failed = compute(args.estate, args.as_of, records_dir)

    if failed == 0:
        _summary("OK", checked, 0)
        sys.exit(0)
    else:
        _summary("FAIL", checked, failed)
        sys.exit(2)


if __name__ == "__main__":
    main()
