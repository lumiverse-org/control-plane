#!/usr/bin/env python3
"""tools/records/event_append.py
Event append CLI and library (spec §97.3 lines 8929–8947; L4-06-tasks.md row L4-P4-05; FD-131).
Usage: event-append <event_type> <actor> <product> <subject_ref> [payload-file]
   or: event-append --event-type <type> --actor <actor> --product <product> --subject-ref <ref> [--payload <file>] [--from-file <event-file>] [--validate-only]
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from typing import Any, Dict, Optional, Set, Union
import yaml

from tools.records.lib.writer import assert_utc_offset, utc_day, utc_now
from tools.records.lib.eventpath import event_path
from tools.records.lib.nooverwrite import assert_not_exists, safe_write


EVENT_ENVELOPE = [
    "event_schema_version",
    "event_id",
    "event_type",
    "occurred_at",
    "recorded_at",
    "actor",
    "product",
    "subject_ref",
    "payload",
]
PERSON_REF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,38}$")
DISPLAY_NAME_PATTERN = re.compile(r"^[A-Z][a-z]+ +[A-Z]")


class _NoImplicitDatesLoader(yaml.SafeLoader):
    pass


_NoImplicitDatesLoader.yaml_implicit_resolvers = {
    key: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_event_types(cp_root: Optional[pathlib.Path] = None) -> Set[str]:
    """Load valid event types from metrics/taxonomy/event-types.yaml."""
    if cp_root is None:
        cp_root = pathlib.Path(__file__).resolve().parent.parent.parent
    tax_path = cp_root / "metrics" / "taxonomy" / "event-types.yaml"
    if not tax_path.is_file():
        raise FileNotFoundError(f"taxonomy-absent: {tax_path}")

    data = yaml.safe_load(tax_path.read_text(encoding="utf-8"))
    types = set()
    for item in data.get("event_types", []):
        if isinstance(item, dict) and "id" in item:
            types.add(item["id"])
    return types


def validate_event_dict(
    doc: Dict[str, Any],
    cp_root: Optional[pathlib.Path] = None,
    schema_path: Optional[str] = None,
) -> None:
    """Validate event envelope, closed taxonomy enum, and D88 constraints."""
    if not isinstance(doc, dict):
        raise ValueError("not-a-mapping")

    for key in EVENT_ENVELOPE:
        if key not in doc:
            raise ValueError(f"missing-envelope-field:{key}")

    et = doc.get("event_type")
    valid_types = load_event_types(cp_root=cp_root)
    if et not in valid_types:
        raise ValueError(f"unknown-event-type {et}")

    assert_utc_offset(str(doc.get("occurred_at")))
    assert_utc_offset(str(doc.get("recorded_at")))

    # D88 rule: actor must be a valid person_ref, never a display name
    actor = str(doc.get("actor", ""))
    if DISPLAY_NAME_PATTERN.search(actor) or not PERSON_REF_PATTERN.match(actor):
        raise ValueError(f"d88-display-name-rejected:actor={actor}")

    if schema_path and schema_path != "-" and os.path.exists(schema_path):
        schema = json.load(open(schema_path, encoding="utf-8"))
        try:
            import jsonschema
            jsonschema.validate(json.loads(json.dumps(doc, default=str)), schema)
        except ImportError:
            pass
        except Exception as exc:
            raise ValueError(f"schema-validation-failed:{exc}")


def emit_event(
    event_type: str,
    actor: str,
    product: str,
    subject_ref: str,
    payload_input: Union[str, Dict[str, Any], None] = None,
    occurred_at: Optional[str] = None,
    event_id: Optional[str] = None,
    cpr_root: Optional[str] = None,
    cp_root: Optional[pathlib.Path] = None,
    validate_only: bool = False,
) -> pathlib.Path:
    """Construct, validate and append an event file to $CPR_ROOT/events/<YYYY-MM-DD>/<event_id>.yaml."""
    if cp_root is None:
        cp_root = pathlib.Path(__file__).resolve().parent.parent.parent

    # Parse payload
    payload_dict: Dict[str, Any] = {}
    if isinstance(payload_input, dict):
        payload_dict = payload_input
    elif isinstance(payload_input, str) and payload_input != "-" and payload_input.strip():
        payload_file = pathlib.Path(payload_input)
        if payload_file.is_file():
            parsed = yaml.load(payload_file.read_text(encoding="utf-8"), Loader=_NoImplicitDatesLoader)
            payload_dict = parsed if isinstance(parsed, dict) else {}
        else:
            try:
                parsed = yaml.load(payload_input, Loader=_NoImplicitDatesLoader)
                payload_dict = parsed if isinstance(parsed, dict) else {}
            except Exception:
                payload_dict = {}

    now_ts = utc_now()
    occ_ts = occurred_at or os.environ.get("EMIT_OCCURRED_AT") or now_ts
    day = utc_day()

    if not cpr_root:
        cpr_root = os.environ.get("CPR_ROOT") or os.environ.get("RECORDS_DIR") or "."
    cpr_dir = pathlib.Path(cpr_root).resolve()
    edir = cpr_dir / "events" / day

    if not event_id:
        if edir.is_dir():
            existing = list(edir.glob("EVT-*.yaml"))
            seq = len(existing) + 1
        else:
            seq = 1
        event_id = f"EVT-{day}-{seq:06d}"

    rel_path = event_path(event_id, occ_ts)
    out_file = cpr_dir / rel_path

    doc = {
        "event_schema_version": 1,
        "event_id": event_id,
        "event_type": event_type,
        "occurred_at": occ_ts,
        "recorded_at": now_ts,
        "actor": actor,
        "product": product,
        "subject_ref": subject_ref,
        "payload": payload_dict,
    }

    validate_event_dict(doc, cp_root=cp_root)

    if validate_only:
        return out_file

    assert_not_exists(out_file)
    safe_write(out_file, yaml.safe_dump(doc, sort_keys=False))
    return out_file


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Append or validate an event in events/<YYYY-MM-DD>/<event_id>.yaml")
    parser.add_argument("positional", nargs="*", help="<event_type> <actor> <product> <subject_ref> [payload-file]")
    parser.add_argument("--event-type", help="Event type identifier")
    parser.add_argument("--actor", help="Actor person reference")
    parser.add_argument("--product", help="Product identity slug")
    parser.add_argument("--subject-ref", help="Subject reference path or URI")
    parser.add_argument("--payload", "--payload-file", dest="payload", help="Payload YAML file or string")
    parser.add_argument("--from-file", dest="from_file", help="Path to full event YAML file to validate")
    parser.add_argument("--cpr-root", help="Root of control-plane-records repository")
    parser.add_argument("--validate-only", action="store_true", help="Validate without writing")

    args = parser.parse_args(argv)

    if args.from_file:
        p = pathlib.Path(args.from_file)
        if not p.is_file():
            print(f"EMIT FAIL file-not-found {args.from_file}", file=sys.stderr)
            return 1
        try:
            doc = yaml.load(p.read_text(encoding="utf-8"), Loader=_NoImplicitDatesLoader)
            validate_event_dict(doc)
            print(f"VALIDATE OK {args.from_file}")
            return 0
        except Exception as exc:
            print(f"EMIT FAIL invalid-event: {exc}", file=sys.stderr)
            return 1

    event_type = None
    actor = None
    product = None
    subject_ref = None
    payload = None

    if len(args.positional) >= 4:
        event_type = args.positional[0]
        actor = args.positional[1]
        product = args.positional[2]
        subject_ref = args.positional[3]
        payload = args.positional[4] if len(args.positional) > 4 else "-"
    elif args.event_type and args.actor and args.product and args.subject_ref:
        event_type = args.event_type
        actor = args.actor
        product = args.product
        subject_ref = args.subject_ref
        payload = args.payload or "-"
    else:
        print("Usage: event-append <event_type> <actor> <product> <subject_ref> [payload-file]", file=sys.stderr)
        return 2

    try:
        out = emit_event(
            event_type=event_type,
            actor=actor,
            product=product,
            subject_ref=subject_ref,
            payload_input=payload,
            cpr_root=args.cpr_root,
            validate_only=args.validate_only,
        )
        print(str(out))
        return 0
    except (FileNotFoundError, ValueError, FileExistsError) as exc:
        print(f"EMIT FAIL {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"EMIT ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
