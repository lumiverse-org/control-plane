"""
L2-T545  Event writer: one file per event, bound envelope
§97.3 L8929-8953 — one file per event, nine required envelope fields,
event_type constrained to an identifier in Lane 4's published taxonomy.
PARTITION.md rule 3: no shared mutable file, ever.

Rejects an event at write time before any file is created when:
- any envelope field is missing
- event_type is not in Lane 4's published taxonomy

Lane 2 supplies the event; Lane 4 owns the enum.
No append mode (open 'a') anywhere in this file.

Exit codes:
  0  OK    checked=9 failed=0
  2  FAIL  checked=9 failed=<n>
  3  ERROR checked=0 failed=0
"""
from __future__ import annotations
import argparse, hashlib, sys, uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from tools.evidence import STATUS_OK, STATUS_FAIL, STATUS_ERROR, EXIT_OK, EXIT_FAIL, EXIT_ERROR

TOOL_ID = "event_writer"

# Nine required envelope fields (§97.3)
ENVELOPE_FIELDS = [
    "event_id",
    "event_type",
    "occurred_at",
    "actor",
    "environment",
    "product",
    "artifact_digest",
    "run_id",
    "correlation_id",
]

# Lane 4's published event_type taxonomy
# Populated from schemas/events/taxonomy.yaml when available at runtime.
# Hard-coded fallback for Lane 2 fixture testing only.
EVENT_TYPE_TAXONOMY = frozenset({
    "production_deployed",
    "staging_deployed",
    "migration_applied",
    "rollback_executed",
    "restore_completed",
    "restore_failed",
    "org_export_completed",
    "org_export_failed",
    "incident_declared",
    "exceptional_authorisation",
})


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def _load_event(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"event file not found: {path}")
    if yaml is None:
        raise ImportError("pyyaml is required")
    with open(p) as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError("event must be a YAML mapping")
    return data


def _load_taxonomy() -> frozenset[str]:
    """Load Lane 4's event_type taxonomy if available; fall back to hard-coded set."""
    taxonomy_path = Path("schemas/events/taxonomy.yaml")
    if taxonomy_path.exists() and yaml is not None:
        with open(taxonomy_path) as fh:
            data = yaml.safe_load(fh)
        if isinstance(data, list):
            return frozenset(data)
    return EVENT_TYPE_TAXONOMY


def validate_event(event: dict, taxonomy: frozenset[str]) -> tuple[int, int]:
    """Return (checked=9, failed=n). Validates before any write."""
    checked = len(ENVELOPE_FIELDS)
    failed = 0

    for field in ENVELOPE_FIELDS:
        if not event.get(field):
            print(f"FAIL: envelope field {field!r} missing or empty", file=sys.stderr)
            failed += 1

    # event_type taxonomy check
    event_type = event.get("event_type")
    if event_type and event_type not in taxonomy:
        print(
            f"FAIL: event_type {event_type!r} is not in Lane 4's published taxonomy;"
            f" valid values: {sorted(taxonomy)}",
            file=sys.stderr,
        )
        failed += 1

    return checked, failed


def _event_path(event: dict) -> Path:
    """Derive unique file path: records/events/<date>/<event_id>.yaml
    PARTITION.md rule 3: one file per event, never an append."""
    occurred = event.get("occurred_at", datetime.now(tz=timezone.utc).isoformat())
    date_part = occurred[:10]  # YYYY-MM-DD
    event_id = event.get("event_id") or str(uuid.uuid4())
    return Path(f"records/events/{date_part}/{event_id}.yaml")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Event writer: one file per event, bound envelope.")
    ap.add_argument("--event", required=True, help="Path to event YAML")
    ap.add_argument("--dry-run", action="store_true", help="Validate and print without writing")
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args(argv)

    try:
        event = _load_event(args.event)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if args.summary:
            _summary(STATUS_ERROR, 0, 0)
        sys.exit(EXIT_ERROR)

    taxonomy = _load_taxonomy()
    checked, failed = validate_event(event, taxonomy)

    if failed > 0:
        if args.summary:
            _summary(STATUS_FAIL, checked, failed)
        sys.exit(EXIT_FAIL)

    if args.dry_run:
        event_path = _event_path(event)
        print(f"DRY-RUN: event valid; would write to {event_path}", file=sys.stderr)
        if args.summary:
            _summary(STATUS_OK, checked, failed)
        sys.exit(EXIT_OK)

    # Live write: refuse to append, always a new file
    event_path = _event_path(event)
    if event_path.exists():
        print(f"FAIL: event file already exists at {event_path} — one file per event rule",
              file=sys.stderr)
        if args.summary:
            _summary(STATUS_FAIL, checked, 1)
        sys.exit(EXIT_FAIL)

    event_path.parent.mkdir(parents=True, exist_ok=True)
    if yaml is None:
        raise ImportError("pyyaml is required")
    # Open in 'w' (write) mode — never 'a' (append)
    with open(event_path, "w") as fh:
        yaml.safe_dump(event, fh, default_flow_style=False)

    print(f"OK: event written to {event_path}", file=sys.stderr)
    if args.summary:
        _summary(STATUS_OK, checked, failed)
    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
