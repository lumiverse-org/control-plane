"""
tools.evidence.version_monitor
L2-T551: /version digest-match monitor (§41.2 L3717-3729, §32 item 11)

Answers evidence-chain question 11.
A mismatch is a failure and raises P0_DIGEST_MISMATCH.
An unreachable endpoint is ERROR, exit 3 — not matching.

Exit codes per §0.4: 0=OK, 2=FAIL, 3=ERROR
"""
import argparse
import json
import sys
import os

TOOL_ID = "version_monitor"

# Conformance profiles that do not expose a /version endpoint (§15.7, §41.2)
NON_SERVICE_PROFILES = {
    "client-app",
    "library",
    "batch",
    "customer-hosted",
    "white-label",
    "static-site",
}


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def check_fixture(fixture: dict) -> tuple[str, int, int]:
    """
    Returns (status, checked, failed).
    """
    profile = fixture.get("conformance_profile", "service")

    # Non-service profiles route to profile_evidence (§41.2, §15.7)
    if profile in NON_SERVICE_PROFILES:
        profile_evidence = fixture.get("profile_evidence")
        if profile_evidence:
            # Profile substitution satisfied
            return "OK", 1, 0
        # Even for non-service profiles, absence of substitution evidence is a failure
        print(
            f"FAIL: profile '{profile}' declares no profile_evidence for item 11",
            file=sys.stderr,
        )
        return "FAIL", 1, 1

    # Service profile: compare approved digest with /version response
    unreachable = fixture.get("unreachable", False)
    if unreachable:
        print(
            "ERROR: /version endpoint is unreachable — unreachable is not matching (§41.2)",
            file=sys.stderr,
        )
        return "ERROR", 0, 0

    status_code = fixture.get("status_code", 200)
    if status_code != 200:
        print(
            f"ERROR: /version endpoint returned HTTP {status_code} — "
            "unreachable is not matching (§41.2)",
            file=sys.stderr,
        )
        return "ERROR", 0, 0

    approved_digest = fixture.get("approved_digest")
    live_digest = fixture.get("live_digest")

    if not approved_digest or not live_digest:
        print(
            "ERROR: fixture missing approved_digest or live_digest",
            file=sys.stderr,
        )
        return "ERROR", 0, 0

    if approved_digest != live_digest:
        print(
            f"approved='{approved_digest}' live='{live_digest}' (§41.2)",
            file=sys.stderr,
        )
        print("P0_DIGEST_MISMATCH", file=sys.stderr)
        return "FAIL", 1, 1

    return "OK", 1, 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True, help="Path to version observation fixture JSON")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.fixture):
        print(f"ERROR: fixture file not found: {args.fixture}", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    try:
        with open(args.fixture, "r", encoding="utf-8") as fh:
            fixture = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot parse fixture JSON: {exc}", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    status, checked, failed = check_fixture(fixture)
    _summary(status, checked, failed)

    if status == "OK":
        sys.exit(0)
    elif status == "FAIL":
        sys.exit(2)
    else:
        sys.exit(3)


if __name__ == "__main__":
    main()
