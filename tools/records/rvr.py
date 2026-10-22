#!/usr/bin/env python3
"""tools/records/rvr.py
RECORD-VERIFICATION-RESULT handler library and CLI (spec §97.2 line 8871; L4-06 row L4-P4-06; FD-131).
Usage: record-verification-result <product> <item> <mechanism> <pass|fail> <evidence_link> <actor>
"""
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys
from typing import Any, Dict, Optional, Tuple
import yaml

from tools.records.lib.writer import mint_id, utc_now, utc_day
from tools.records.lib.nooverwrite import safe_write, assert_not_exists
from tools.records.record_write import emit_record, validate_record_dict
from tools.records.event_append import emit_event


def load_rvr_config(cp_root: Optional[pathlib.Path] = None) -> Dict[str, Any]:
    """Load tools/records/dispatch/rvr-inputs.yaml."""
    if cp_root is None:
        cp_root = pathlib.Path(__file__).resolve().parent.parent.parent
    cfg_path = cp_root / "tools" / "records" / "dispatch" / "rvr-inputs.yaml"
    if not cfg_path.is_file():
        raise FileNotFoundError(f"rvr-inputs-absent: {cfg_path}")
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8"))


def handle_rvr(
    product: str,
    item: str,
    mechanism: str,
    result: str,
    evidence_link: str,
    actor: str,
    cpr_root: Optional[str] = None,
    cp_root: Optional[pathlib.Path] = None,
) -> Tuple[str, str, str]:
    """Execute RECORD-VERIFICATION-RESULT.
    Returns (record_id, store, event_type).
    Raises ValueError on bad inputs (exit 2).
    Raises PermissionError on unarmed mechanisms (exit 3).
    """
    if cp_root is None:
        cp_root = pathlib.Path(__file__).resolve().parent.parent.parent

    # Input validations
    fields = [
        ("product", product),
        ("item", item),
        ("mechanism", mechanism),
        ("result", result),
        ("evidence_link", evidence_link),
        ("actor", actor),
    ]
    for name, val in fields:
        if not val or not str(val).strip():
            raise ValueError(f"empty-input {name}")

    if result not in ("pass", "fail"):
        raise ValueError(f"bad-result {result}")

    if not (evidence_link.startswith("http://") or evidence_link.startswith("https://")):
        raise ValueError(f"bad-evidence-link {evidence_link}")

    config = load_rvr_config(cp_root=cp_root)
    mech_entry = None
    for m in config.get("mechanisms", []):
        if m.get("mechanism") == mechanism:
            mech_entry = m
            break

    if mech_entry is None:
        raise ValueError(f"unknown-mechanism {mechanism}")

    if not mech_entry.get("armed", False):
        spec_ref = mech_entry.get("spec_ref", "unarmed")
        raise PermissionError(f"unarmed-mechanism {mechanism} - UNARMED {spec_ref}")

    target_store = mech_entry["target_store"]
    schema_name = mech_entry.get("schema")
    event_type = mech_entry["event_type"]

    if not cpr_root:
        cpr_root = os.environ.get("CPR_ROOT") or os.environ.get("RECORDS_DIR") or "."
    cpr_dir = pathlib.Path(cpr_root).resolve()

    # Mint record ID
    record_id = mint_id(target_store, cpr_root=cpr_dir, cp_root=cp_root)
    now_ts = utc_now()

    # Build record document
    if target_store == "uat":
        record_doc = {
            "record_schema_version": 1,
            "id": record_id,
            "product": product,
            "timestamp": now_ts,
            "result": result,
            "executed_by": actor,
            "uat_contract": item,
            "environment": "local",
            "evidence": evidence_link,
            "work_item": item,
        }
    elif target_store == "restore-tests":
        record_doc = {
            "record_schema_version": 1,
            "id": record_id,
            "product": product,
            "timestamp": now_ts,
            "result": result,
            "restore_environment": "staging",
            "integrity_check": "backup_checksum_and_schema_migration",
            "integrity_check_result": result,
            "verifier": actor,
            "confirmed_by": actor,
            "confirmed_at": now_ts,
        }
    else:
        record_doc = {
            "record_schema_version": 1,
            "id": record_id,
            "product": product,
            "timestamp": now_ts,
            "mechanism": mechanism,
            "item": item,
            "result": result,
            "evidence_link": evidence_link,
            "reported_by": actor,
            "write_path": "rvr-dispatch",
        }

    schema_path = str(cp_root / "schemas" / "records" / schema_name) if schema_name else None
    validate_record_dict(record_doc, expected_id=record_id, schema_path=schema_path)

    # Payload for the event
    payload_dict = {
        "mechanism": mechanism,
        "result": result,
        "item": item,
        "evidence_link": evidence_link,
    }

    # Safe atomic pair write
    store_dir = cpr_dir / "records" / target_store
    store_dir.mkdir(parents=True, exist_ok=True)
    rec_path = store_dir / f"{record_id}.yaml"
    assert_not_exists(rec_path)
    safe_write(rec_path, yaml.safe_dump(record_doc, sort_keys=False))

    subject_ref = f"records/{target_store}/{record_id}.yaml"
    try:
        ev_path = emit_event(
            event_type=event_type,
            actor=actor,
            product=product,
            subject_ref=subject_ref,
            payload_input=payload_dict,
            occurred_at=now_ts,
            cpr_root=str(cpr_dir),
            cp_root=cp_root,
        )
    except Exception as exc:
        # Rollback record if event write fails
        if rec_path.is_file():
            rec_path.unlink()
        raise RuntimeError(f"pair-rolled-back {record_id}: {exc}")

    # Commit if cpr_dir is a git repository
    if (cpr_dir / ".git").is_dir():
        commit_msg = f"records: {record_id} ({target_store}) + {ev_path.stem} [{event_type}]"
        try:
            subprocess.run(["git", "-C", str(cpr_dir), "add", "-A"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(cpr_dir), "commit", "-q", "-m", commit_msg], check=True, capture_output=True)
        except Exception:
            pass

    return record_id, target_store, event_type


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Handle RECORD-VERIFICATION-RESULT dispatch")
    parser.add_argument("positional", nargs="*", help="<product> <item> <mechanism> <pass|fail> <evidence_link> <actor>")
    parser.add_argument("--product", help="Product slug")
    parser.add_argument("--item", help="Item verified")
    parser.add_argument("--mechanism", help="Mechanism used")
    parser.add_argument("--result", help="Result: pass or fail")
    parser.add_argument("--evidence-link", help="Evidence URL")
    parser.add_argument("--actor", help="Reporting actor")
    parser.add_argument("--cpr-root", help="Root of control-plane-records repo")

    args = parser.parse_args(argv)

    if len(args.positional) == 6:
        product, item, mechanism, result, evidence_link, actor = args.positional
    elif (
        args.product
        and args.item
        and args.mechanism
        and args.result
        and args.evidence_link
        and args.actor
    ):
        product = args.product
        item = args.item
        mechanism = args.mechanism
        result = args.result
        evidence_link = args.evidence_link
        actor = args.actor
    else:
        print(f"RVR FAIL wrong-arity expected 6 got {len(args.positional)}", file=sys.stderr)
        return 2

    try:
        rec_id, store, ev_type = handle_rvr(
            product=product,
            item=item,
            mechanism=mechanism,
            result=result,
            evidence_link=evidence_link,
            actor=actor,
            cpr_root=args.cpr_root,
        )
        print(f"RVR OK {rec_id} {store} {ev_type}")
        return 0
    except ValueError as exc:
        print(f"RVR FAIL {exc}", file=sys.stderr)
        return 2
    except PermissionError as exc:
        print(f"RVR FAIL {exc}", file=sys.stderr)
        return 3
    except Exception as exc:
        print(f"RVR FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
