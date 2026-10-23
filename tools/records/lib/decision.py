"""tools/records/lib/decision.py
Decision record library: pending decision prompts and decided records.
Master Spec v4.0 Section 97.2 lines 8865-8866; Section 99.2 line 9230; L4-06-tasks.md row L4-P4-07; FD-131.

Rules:
1. Opening a decision prompt writes to `records/decisions/pending/<id>.yaml`.
2. Deciding writes a new file to `records/decisions/<id>.yaml`.
3. The pending record is marked superseded by writing a follow-up record, never by in-place edit (invariant 48).
4. All timestamps must carry UTC offset.
5. Decider must be a valid role token or opaque person identifier, never a display name (D88).
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Union
import yaml

from tools.records.lib.writer import assert_utc_offset, mint_id, utc_day, utc_now
from tools.records.lib.nooverwrite import assert_not_exists, safe_write

DECISION_ID_PATTERN = re.compile(r"^DEC-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3}$")
PERSON_REF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,38}$")
DISPLAY_NAME_PATTERN = re.compile(r"^[A-Z][a-z]+ +[A-Z]")


def validate_decider(decider: str) -> None:
    """Ensure decider satisfies D88: role token or person identifier, not display name."""
    if not isinstance(decider, str):
        raise ValueError(f"decider must be string, got {type(decider)}")
    if DISPLAY_NAME_PATTERN.search(decider) or not PERSON_REF_PATTERN.match(decider):
        raise ValueError(f"d88-display-name-rejected: decider '{decider}' must be an opaque identifier or role token")


def mint_decision_id(
    records_root: Optional[Union[str, Path]] = None,
    date_str: Optional[str] = None,
    seq: Optional[int] = None,
) -> str:
    """Mint a unique decision ID conforming to DEC-YYYY-MM-DD-NNN."""
    day = date_str or utc_day()
    if seq is None and records_root is not None:
        root_path = Path(records_root)
        pending_dir = root_path / "records" / "decisions" / "pending"
        decided_dir = root_path / "records" / "decisions"
        existing = set()
        pattern = f"DEC-{day}-*.yaml"
        if pending_dir.is_dir():
            existing.update(p.name for p in pending_dir.glob(pattern))
        if decided_dir.is_dir():
            existing.update(p.name for p in decided_dir.glob(pattern))
        seq = len(existing) + 1
    elif seq is None:
        seq = 1
    return f"DEC-{day}-{seq:03d}"


def create_pending_decision(
    records_root: Union[str, Path],
    product: str,
    decider: str,
    subject: str,
    prompt_received: Optional[str] = None,
    decision_id: Optional[str] = None,
    timestamp: Optional[str] = None,
    options_considered: Optional[List[str]] = None,
    evidence: Optional[List[str]] = None,
    gap_window: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create and write a pending decision record."""
    root = Path(records_root)
    day = utc_day()
    dec_id = decision_id or mint_decision_id(records_root=root, date_str=day)
    if not DECISION_ID_PATTERN.match(dec_id):
        raise ValueError(f"invalid-decision-id: '{dec_id}' does not match pattern DEC-YYYY-MM-DD-NNN")

    validate_decider(decider)

    ts = timestamp or utc_now()
    assert_utc_offset(ts)

    p_rec = prompt_received or day

    record: Dict[str, Any] = {
        "record_schema_version": 1,
        "id": dec_id,
        "product": product,
        "timestamp": ts,
        "decider": decider,
        "prompt_received": p_rec,
        "subject": subject,
    }
    if options_considered is not None:
        record["options_considered"] = options_considered
    if evidence is not None:
        record["evidence"] = evidence
    if gap_window is not None:
        record["gap_window"] = gap_window

    target_dir = root / "records" / "decisions" / "pending"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / f"{dec_id}.yaml"

    assert_not_exists(target_file)
    safe_write(target_file, yaml.safe_dump(record, sort_keys=False))
    return record


def decide_pending_decision(
    records_root: Union[str, Path],
    decision_id: str,
    options_considered: List[str],
    evidence: List[str],
    decided: Optional[str] = None,
    review_date: Optional[str] = None,
    gap_window: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolve a pending decision into a decided record in records/decisions/."""
    root = Path(records_root)
    if not DECISION_ID_PATTERN.match(decision_id):
        raise ValueError(f"invalid-decision-id: '{decision_id}' does not match pattern DEC-YYYY-MM-DD-NNN")

    pending_file = root / "records" / "decisions" / "pending" / f"{decision_id}.yaml"
    if not pending_file.is_file():
        raise FileNotFoundError(f"pending-decision-not-found: {pending_file}")

    with open(pending_file, "r", encoding="utf-8") as f:
        pending_data = yaml.safe_load(f)

    if not isinstance(pending_data, dict):
        raise ValueError(f"corrupt-pending-decision: {pending_file}")

    dec_date = decided or utc_day()
    ts = timestamp or utc_now()
    assert_utc_offset(ts)

    decided_record: Dict[str, Any] = {
        "record_schema_version": 1,
        "id": decision_id,
        "product": pending_data["product"],
        "timestamp": ts,
        "decider": pending_data["decider"],
        "prompt_received": pending_data["prompt_received"],
        "decided": dec_date,
        "subject": pending_data["subject"],
        "options_considered": options_considered or pending_data.get("options_considered", ["default"]),
        "evidence": evidence or pending_data.get("evidence", []),
    }
    if review_date:
        decided_record["review_date"] = review_date
    if gap_window or "gap_window" in pending_data:
        decided_record["gap_window"] = gap_window or pending_data.get("gap_window")

    decided_dir = root / "records" / "decisions"
    decided_dir.mkdir(parents=True, exist_ok=True)
    decided_file = decided_dir / f"{decision_id}.yaml"

    assert_not_exists(decided_file)
    safe_write(decided_file, yaml.safe_dump(decided_record, sort_keys=False))

    # Mark pending decision superseded via a separate follow-up record, never by editing in-place
    superseded_record = {
        "record_schema_version": 1,
        "id": f"{decision_id}-SUPERSEDED",
        "supersedes": decision_id,
        "status": "decided",
        "timestamp": ts,
        "target_file": f"records/decisions/{decision_id}.yaml",
    }
    superseded_file = root / "records" / "decisions" / "pending" / f"{decision_id}.superseded.yaml"
    safe_write(superseded_file, yaml.safe_dump(superseded_record, sort_keys=False))

    return decided_record
