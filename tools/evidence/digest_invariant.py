"""
L2-T543  Digest invariant: requested versus staging-verified
§32 L2803-2828 — CI rejects any production deployment where the requested
digest differs from the digest that passed staging verification.
§101 invariants 22 and 23, L9483-9484.

No tolerance. No normalisation. No 'close enough'. No rebuild call.

The one sanctioned equivalence: S18 platform-rebuild deployment (§32, D78).
The recorded identity — pinned commit, lockfile AND build configuration —
stands in for the digest. All three components must be present; a record
claiming platform-rebuild equivalence without all three fails.

Exit codes:
  0  OK    checked=1 failed=0
  2  FAIL  checked=1 failed=1
  3  ERROR checked=0 failed=0
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from tools.evidence import STATUS_OK, STATUS_FAIL, STATUS_ERROR, EXIT_OK, EXIT_FAIL, EXIT_ERROR

TOOL_ID = "digest_invariant"

S18_REQUIRED_FIELDS = frozenset({"pinned_commit", "lockfile", "build_configuration"})


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def _load_record(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"staging record not found: {path}")
    if yaml is None:
        raise ImportError("pyyaml is required")
    with open(p) as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError("staging record must be a YAML mapping")
    return data


def evaluate(requested: str, record: dict) -> tuple[int, int]:
    """Return (checked=1, failed=0|1)."""
    if not requested:
        raise ValueError("requested digest is empty — fail-closed")

    staging_digest = record.get("verified_digest")
    platform_rebuild = record.get("platform_rebuild")

    if platform_rebuild:
        # S18 equivalence path: all three components required
        identity = platform_rebuild if isinstance(platform_rebuild, dict) else {}
        missing = S18_REQUIRED_FIELDS - set(identity.keys())
        if missing:
            print(
                f"FAIL: S18 platform-rebuild record missing required fields: {missing}",
                file=sys.stderr,
            )
            return 1, 1
        print(
            f"INFO: S18 platform-rebuild equivalence accepted for {requested!r}",
            file=sys.stderr,
        )
        return 1, 0

    if not staging_digest:
        raise ValueError("staging record has no verified_digest — fail-closed")

    # Byte-identical comparison. No tolerance.
    if requested != staging_digest:
        print("DIGEST_INVARIANT_VIOLATION", file=sys.stderr)
        print(
            f"FAIL: requested={requested!r} != staging_verified={staging_digest!r}",
            file=sys.stderr,
        )
        return 1, 1

    return 1, 0


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Digest invariant: requested vs staging-verified.")
    ap.add_argument("--requested", required=True, help="Requested artifact digest (sha256:...)")
    ap.add_argument("--staging-record", required=True, help="Path to staging verification record YAML")
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args(argv)

    try:
        record = _load_record(args.staging_record)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if args.summary:
            _summary(STATUS_ERROR, 0, 0)
        sys.exit(EXIT_ERROR)

    try:
        checked, failed = evaluate(args.requested, record)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if args.summary:
            _summary(STATUS_ERROR, 0, 0)
        sys.exit(EXIT_ERROR)

    if args.summary:
        _summary(STATUS_OK if failed == 0 else STATUS_FAIL, checked, failed)

    sys.exit(EXIT_OK if failed == 0 else EXIT_FAIL)


if __name__ == "__main__":
    main()
