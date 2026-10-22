#!/usr/bin/env python3
"""tools/records/record_write.py
Record emission CLI and library (spec §97.2 lines 8890–8892; L4-06-tasks.md row L4-P4-03; FD-131).
Usage: record-write <store> <id> <body-file> [schema-file]
   or: record-write --store <store> --id <id> --from-file <file> [--schema <schema>] [--validate-only]
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from typing import Any, Dict, Optional, Union
import yaml

from tools.records.lib.writer import assert_utc_offset
from tools.records.lib.nooverwrite import assert_not_exists, safe_write


RECORD_ENVELOPE = ["record_schema_version", "id", "product", "timestamp"]
PERSON_REF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,38}$")
DISPLAY_NAME_PATTERN = re.compile(r"^[A-Z][a-z]+ +[A-Z]")


class _NoImplicitDatesLoader(yaml.SafeLoader):
    pass


_NoImplicitDatesLoader.yaml_implicit_resolvers = {
    key: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def validate_record_dict(
    doc: Dict[str, Any],
    expected_id: Optional[str] = None,
    schema_path: Optional[str] = None,
) -> None:
    """Validate record envelope, D88 person reference constraints, and schema rules."""
    if not isinstance(doc, dict):
        raise ValueError("not-a-mapping")

    for key in RECORD_ENVELOPE:
        if key not in doc:
            raise ValueError(f"missing-envelope-field:{key}")

    if expected_id is not None and str(doc.get("id")) != str(expected_id):
        raise ValueError(f"id-mismatch: expected {expected_id}, got {doc.get('id')}")

    ts = str(doc.get("timestamp"))
    assert_utc_offset(ts)

    # D88 rule: person fields must not be display names
    for person_field in ("approved_by", "decider", "given_by", "executor", "actor", "reported_by", "executed_by", "verifier", "confirmed_by"):
        if person_field in doc:
            val = str(doc[person_field])
            if DISPLAY_NAME_PATTERN.search(val) or not PERSON_REF_PATTERN.match(val):
                raise ValueError(f"d88-display-name-rejected:{person_field}={val}")

    if schema_path and schema_path != "-" and os.path.exists(schema_path):
        schema = json.load(open(schema_path, encoding="utf-8"))
        for req_key in schema.get("required", []):
            if req_key not in doc:
                raise ValueError(f"missing-schema-required-field:{req_key}")
        try:
            import jsonschema
            from jsonschema import Draft202012Validator, RefResolver

            schema_dir = os.path.dirname(os.path.abspath(schema_path))
            store = {}
            for name in os.listdir(schema_dir):
                if name.endswith(".json"):
                    try:
                        sib_path = os.path.join(schema_dir, name)
                        sib = json.load(open(sib_path, encoding="utf-8"))
                        store[name] = sib
                        store[pathlib.Path(sib_path).as_uri()] = sib
                    except Exception:
                        continue
            resolver = RefResolver(base_uri=pathlib.Path(schema_dir).as_uri() + "/", referrer=schema, store=store)
            Draft202012Validator(schema, resolver=resolver).validate(
                json.loads(json.dumps(doc, default=str))
            )
        except ImportError:
            pass
        except Exception as exc:
            raise ValueError(f"schema-validation-failed:{exc}")


def emit_record(
    store: str,
    record_id: Optional[str],
    body_path: str,
    schema_file: Optional[str] = None,
    cpr_root: Optional[str] = None,
    validate_only: bool = False,
) -> pathlib.Path:
    """Validate and optionally write record to $CPR_ROOT/records/<store>/<id>.yaml.
    Returns written Path.
    """
    body_file = pathlib.Path(body_path)
    if not body_file.is_file():
        raise FileNotFoundError(f"body-file-not-found {body_path}")

    text = body_file.read_text(encoding="utf-8")
    try:
        doc = yaml.load(text, Loader=_NoImplicitDatesLoader)
        validate_record_dict(doc, expected_id=record_id, schema_path=schema_file)
    except Exception as exc:
        raise ValueError(f"invalid-record {body_path}: {exc}")

    if validate_only:
        return body_file

    if not record_id:
        record_id = str(doc.get("id"))

    if not cpr_root:
        cpr_root = os.environ.get("CPR_ROOT") or os.environ.get("RECORDS_DIR") or "."
    cpr_dir = pathlib.Path(cpr_root).resolve()
    store_dir = cpr_dir / "records" / store
    if not store_dir.is_dir():
        raise NotADirectoryError(f"no-store {store} (directory {store_dir} does not exist)")

    out_file = store_dir / f"{record_id}.yaml"
    assert_not_exists(out_file)

    safe_write(out_file, text)
    return out_file


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Emit or validate a record in records/<store>/<id>.yaml")
    parser.add_argument("positional", nargs="*", help="<store> <id> <body-file> [schema-file]")
    parser.add_argument("--store", help="Target record store")
    parser.add_argument("--id", dest="rec_id", help="Record ID")
    parser.add_argument("--body", "--from-file", dest="body", help="Path to record body file")
    parser.add_argument("--schema", help="Path to schema file")
    parser.add_argument("--cpr-root", help="Root of control-plane-records repository")
    parser.add_argument("--validate-only", action="store_true", help="Validate without writing")

    args = parser.parse_args(argv)

    store = None
    rec_id = None
    body = None
    schema = args.schema
    validate_only = args.validate_only

    if len(args.positional) >= 3:
        store = args.positional[0]
        rec_id = args.positional[1]
        body = args.positional[2]
        if len(args.positional) > 3:
            schema = args.positional[3]
    elif args.store and (args.rec_id or validate_only) and args.body:
        store = args.store
        rec_id = args.rec_id
        body = args.body
    elif validate_only and args.body:
        store = args.store or "records"
        rec_id = args.rec_id  # None if not explicitly given
        body = args.body
    else:
        print("Usage: record-write <store> <id> <body-file> [schema-file]", file=sys.stderr)
        return 2

    try:
        out = emit_record(
            store=store,
            record_id=rec_id,
            body_path=body,
            schema_file=schema,
            cpr_root=args.cpr_root,
            validate_only=validate_only,
        )
        if validate_only:
            print(f"VALIDATE OK {body}")
        else:
            print(str(out))
        return 0
    except (FileNotFoundError, ValueError, NotADirectoryError, FileExistsError) as exc:
        print(f"EMIT FAIL {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"EMIT ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
