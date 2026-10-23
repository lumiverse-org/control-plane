"""
tools.evidence.shipped_assert
L2-T553: The eight "shipped" conditions (§34.1 L2915-2929)

A change is shipped only when ALL eight conditions are true.
Merged and deployed are tracked as SEPARATE metrics — never collapsed.

Exit codes per §0.4: 0=OK, 2=FAIL, 3=ERROR
"""
import argparse
import sys
import os

try:
    import yaml
except ImportError:
    print("ERROR shipped_assert checked=0 failed=0")
    sys.exit(3)

TOOL_ID = "shipped_assert"
CHECKED = 8

# The eight conditions of §34.1, in order
CONDITIONS = [
    ("merged",           "1. Pull request merged"),
    ("artifact_built",   "2. Artifact built and digest recorded"),
    ("deployed",         "3. Deployed to the target environment"),
    ("deploy_success",   "4. Deployment reported success"),
    ("smoke_passed",     "5. Smoke tests passed"),
    ("version_recorded", "6. Production version recorded and matching the intended digest"),
    ("health_green",     "7. Health checks green"),
    ("state_md_updated", "8. STATE.md updated"),
]


def _summary(status: str, checked: int, failed: int) -> None:
    # Merged and deployed are emitted as separate fields (§34.1)
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def check(record: dict) -> tuple[int, dict]:
    """
    Returns (failed_count, field_states).
    merged and deployed are always separate fields.
    """
    failed = 0
    field_states = {}

    for field, description in CONDITIONS:
        value = record.get(field)
        # Truthiness check: True, non-empty string, non-zero int all count as met
        met = bool(value)
        field_states[field] = met
        if not met:
            print(
                f"FAIL: condition not met — {description}",
                file=sys.stderr,
            )
            failed += 1

    return failed, field_states


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deployment", required=True)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.deployment):
        print(f"ERROR: deployment record not found: {args.deployment}", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    try:
        with open(args.deployment, "r", encoding="utf-8") as fh:
            record = yaml.safe_load(fh)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot parse deployment record: {exc}", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    if not isinstance(record, dict):
        print("ERROR: deployment record is not a YAML mapping", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    failed, states = check(record)

    # Always emit merged and deployed as distinct fields (§34.1: "tracked as separate metrics")
    print(
        f"merged={states.get('merged', False)} "
        f"deployed={states.get('deployed', False)}",
        file=sys.stderr,
    )

    if failed == 0:
        _summary("OK", CHECKED, 0)
        sys.exit(0)
    else:
        _summary("FAIL", CHECKED, failed)
        sys.exit(2)


if __name__ == "__main__":
    main()
