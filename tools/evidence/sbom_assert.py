"""
L2-T538  SBOM-beside-digest assertion
§48.3 L4317-4320 — every production artifact build emits a Software Bill of
Materials beside the artifact digest — same pipeline step, same storage
discipline, same immutability.

Exit codes (tools.evidence contract):
  0  OK    — executed; zero failures
  2  FAIL  — executed; one or more failures
  3  ERROR — could not execute (missing/unreadable input)
"""
from __future__ import annotations
import argparse, json, sys
from tools.evidence import STATUS_OK, STATUS_FAIL, STATUS_ERROR, EXIT_OK, EXIT_FAIL, EXIT_ERROR

TOOL_ID = "sbom_assert"


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def _load(path: str) -> list[dict]:
    try:
        with open(path) as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            raise ValueError("manifest must be a JSON array")
        return data
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR reading {path}: {exc}", file=sys.stderr)
        _summary(STATUS_ERROR, 0, 0)
        sys.exit(EXIT_ERROR)


def check_manifest(entries: list[dict]) -> tuple[int, int]:
    """Return (checked, failed).

    Rules:
      - checked = number of digests recorded
      - failed  = number of digests with no conforming SBOM (same step_id,
                  same storage_prefix, immutability marker present)
      - An empty manifest is ERROR (checked=0).
    """
    checked = len(entries)
    failed = 0
    for entry in entries:
        digest = entry.get("digest")
        sbom   = entry.get("sbom")
        if not digest:
            print(f"WARN: entry missing digest field: {entry!r}", file=sys.stderr)
            failed += 1
            continue
        if not sbom:
            print(f"FAIL: digest {digest!r} has no sbom entry", file=sys.stderr)
            failed += 1
            continue
        # Same pipeline step
        if entry.get("step_id") != sbom.get("step_id"):
            print(
                f"FAIL: digest {digest!r} sbom emitted in different step"
                f" (artifact step={entry.get('step_id')!r},"
                f" sbom step={sbom.get('step_id')!r})",
                file=sys.stderr,
            )
            failed += 1
            continue
        # Same storage prefix
        if entry.get("storage_prefix") != sbom.get("storage_prefix"):
            print(
                f"FAIL: digest {digest!r} sbom in different storage prefix",
                file=sys.stderr,
            )
            failed += 1
            continue
        # Immutability marker
        if not sbom.get("immutable"):
            print(
                f"FAIL: digest {digest!r} sbom missing immutability marker",
                file=sys.stderr,
            )
            failed += 1
    return checked, failed


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Assert SBOM is beside every artifact digest.")
    ap.add_argument("--manifest", required=True, help="Path to build manifest JSON array")
    ap.add_argument("--summary", action="store_true", help="Print §0.4 summary line to stdout")
    args = ap.parse_args(argv)

    entries = _load(args.manifest)

    if len(entries) == 0:
        # A build that produced no artifact is not a passing build
        print("ERROR: manifest contains zero digest entries — not a clean build", file=sys.stderr)
        if args.summary:
            _summary(STATUS_ERROR, 0, 0)
        sys.exit(EXIT_ERROR)

    checked, failed = check_manifest(entries)

    if args.summary:
        if failed == 0:
            _summary(STATUS_OK, checked, failed)
        else:
            _summary(STATUS_FAIL, checked, failed)

    sys.exit(EXIT_OK if failed == 0 else EXIT_FAIL)


if __name__ == "__main__":
    main()
