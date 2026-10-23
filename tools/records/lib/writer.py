#!/usr/bin/env python3
"""tools/records/lib/writer.py
Writer library: UTC clock, id minting, path resolution.
Master Spec v4.0 Section 97.1 line 8839; L4-06-tasks.md row L4-P4-01.

Requirements:
- The clock emits UTC with offset only (e.g. 2026-10-22T03:52:00+00:00).
- A call that would emit a runner-local time raises.
- Ids are minted to the store's declared pattern.
"""
from datetime import datetime, timezone
import os
import pathlib
import re
import sys
from typing import Optional, Union
import yaml

OFFSET_RE = re.compile(r"(Z|[+-]\d{2}:\d{2})$")


def utc_now() -> str:
    """Return current timestamp in ISO 8601 UTC with explicit offset (+00:00)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def utc_day() -> str:
    """Return current UTC date as YYYY-MM-DD."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def assert_utc_offset(timestamp_str: str) -> None:
    """Validate that timestamp_str has an explicit UTC offset.
    Raises ValueError if missing or local without offset.
    """
    if not isinstance(timestamp_str, str):
        raise ValueError(f"timestamp must be a string, got {type(timestamp_str)}")
    if not OFFSET_RE.search(timestamp_str):
        raise ValueError(f"timestamp-without-utc-offset: {timestamp_str}")


def resolve_id_prefix(store: str, cp_root: Optional[pathlib.Path] = None) -> str:
    """Resolve the store's id prefix from write-paths.yaml or canonical spec mapping."""
    if cp_root is None:
        cp_root = pathlib.Path(__file__).resolve().parent.parent.parent
    wp_path = cp_root / "tools" / "records" / "write-paths.yaml"
    if wp_path.is_file():
        try:
            data = yaml.safe_load(wp_path.read_text(encoding="utf-8"))
            for entry in data.get("stores", []):
                if entry.get("store") == store and entry.get("id_prefix"):
                    return entry["id_prefix"]
        except Exception:
            pass

    fallbacks = {
        "incidents": "INC",
        "postmortems": "PM",
        "uat": "UAT",
        "estimates": "EST",
        "deployments": "DEP",
        "restore-tests": "RST",
        "decisions": "DEC",
        "breaches": "BRH",
        "deletion-requests": "DEL",
        "security-reviews": "SEC",
        "eval": "EVL",
        "launches": "LCH",
        "demos": "DMO",
        "support": "SUP",
        "onboarding": "ONB",
        "leave": "LEV",
    }
    return fallbacks.get(store, store[:3].upper())


def mint_id(
    store: str,
    cpr_root: Optional[Union[str, pathlib.Path]] = None,
    cp_root: Optional[pathlib.Path] = None,
    date_str: Optional[str] = None,
    seq: Optional[int] = None,
) -> str:
    """Mint an id according to store pattern: <PREFIX>-<YYYY-MM-DD>-<SEQ>.
    If cpr_root is provided and seq is None, count existing records for the day.
    """
    prefix = resolve_id_prefix(store, cp_root=cp_root)
    day = date_str if date_str is not None else utc_day()
    if seq is None and cpr_root is not None:
        cpr_path = pathlib.Path(cpr_root)
        store_dir = cpr_path / "records" / store
        if store_dir.is_dir():
            pattern = f"{prefix}-{day}-*.yaml"
            matches = list(store_dir.glob(pattern))
            seq = len(matches) + 1
        else:
            seq = 1
    elif seq is None:
        seq = 1
    return f"{prefix}-{day}-{seq:03d}"


def record_path(store: str, record_id: str) -> str:
    """Return the relative path 'records/<store>/<record_id>.yaml'."""
    return f"records/{store}/{record_id}.yaml"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--clock" in argv or "-c" in argv:
        print(utc_now())
        return 0
    if len(argv) >= 1 and argv[0] == "--mint-id":
        store = argv[1] if len(argv) > 1 else "uat"
        print(mint_id(store))
        return 0
    print(f"WRITER LIB OK (now={utc_now()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
