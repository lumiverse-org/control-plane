"""Unit tests for tools/records/find-event query tool (§97.3).
Exercises happy path, negative path (event absent/mismatched/out of window),
and malformed input handling (fail-closed).
"""

from __future__ import annotations

import pathlib
import subprocess
import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
FIND_EVENT_SCRIPT = REPO_ROOT / "tools" / "records" / "find-event"


def to_bash_path(path: pathlib.Path) -> str:
    p = path.resolve().as_posix()
    if len(p) >= 2 and p[1] == ":":
        return f"/mnt/{p[0].lower()}{p[2:]}"
    return p


def run_find_event(cwd: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = ["bash", to_bash_path(FIND_EVENT_SCRIPT), *args]
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_find_event_happy_path(tmp_path: pathlib.Path):
    """Happy path: matching event exists with correct fields and payload."""
    events_dir = tmp_path / "events" / "2026-10-25"
    events_dir.mkdir(parents=True, exist_ok=True)
    evt_path = events_dir / "EVT-2026-10-25-000001.yaml"

    event_data = {
        "event_schema_version": 1,
        "event_id": "EVT-2026-10-25-000001",
        "event_type": "plan_approved",
        "occurred_at": "2026-10-25T10:00:00+00:00",
        "recorded_at": "2026-10-25T10:00:00+00:00",
        "actor": "lead-1",
        "product": "pilot-one",
        "subject_ref": "records/plans/PLAN-001.yaml",
        "payload": {
            "gate": 1,
            "agent_authored": True,
        },
    }
    evt_path.write_text(yaml.safe_dump(event_data), encoding="utf-8")

    res = run_find_event(
        tmp_path,
        "--type", "plan_approved",
        "--product", "pilot-one",
        "--require", "payload.gate=1",
        "--require", "payload.agent_authored=True",
        "--require-fields", "event_schema_version,event_id,occurred_at,recorded_at,actor,product,subject_ref",
    )
    assert res.returncode == 0
    assert "FIND-EVENT PASS: found" in res.stdout
    assert "matching event(s) of type 'plan_approved'" in res.stdout


def test_find_event_negative_missing_type(tmp_path: pathlib.Path):
    """Negative path: event type does not match anything in the store."""
    events_dir = tmp_path / "events" / "2026-10-25"
    events_dir.mkdir(parents=True, exist_ok=True)
    evt_path = events_dir / "EVT-2026-10-25-000001.yaml"

    event_data = {
        "event_schema_version": 1,
        "event_id": "EVT-2026-10-25-000001",
        "event_type": "plan_approved",
        "occurred_at": "2026-10-25T10:00:00+00:00",
        "product": "pilot-one",
    }
    evt_path.write_text(yaml.safe_dump(event_data), encoding="utf-8")

    res = run_find_event(
        tmp_path,
        "--type", "gate_2_approval",
        "--product", "pilot-one",
    )
    assert res.returncode == 1
    assert "FIND-EVENT FAIL: no matching event found" in res.stdout


def test_find_event_negative_mismatched_require(tmp_path: pathlib.Path):
    """Negative path: payload attribute does not match --require."""
    events_dir = tmp_path / "events" / "2026-10-25"
    events_dir.mkdir(parents=True, exist_ok=True)
    evt_path = events_dir / "EVT-2026-10-25-000001.yaml"

    event_data = {
        "event_schema_version": 1,
        "event_id": "EVT-2026-10-25-000001",
        "event_type": "plan_approved",
        "occurred_at": "2026-10-25T10:00:00+00:00",
        "product": "pilot-one",
        "payload": {
            "gate": 1,
        },
    }
    evt_path.write_text(yaml.safe_dump(event_data), encoding="utf-8")

    res = run_find_event(
        tmp_path,
        "--type", "plan_approved",
        "--product", "pilot-one",
        "--require", "payload.gate=2",
    )
    assert res.returncode == 1
    assert "FIND-EVENT FAIL: no matching event found" in res.stdout


def test_find_event_negative_older_than(tmp_path: pathlib.Path):
    """Negative path: event timestamp is older than --newer-than boundary."""
    events_dir = tmp_path / "events" / "2026-10-20"
    events_dir.mkdir(parents=True, exist_ok=True)
    evt_path = events_dir / "EVT-2026-10-20-000001.yaml"

    event_data = {
        "event_schema_version": 1,
        "event_id": "EVT-2026-10-20-000001",
        "event_type": "plan_approved",
        "occurred_at": "2026-10-20T10:00:00+00:00",
        "product": "pilot-one",
    }
    evt_path.write_text(yaml.safe_dump(event_data), encoding="utf-8")

    res = run_find_event(
        tmp_path,
        "--type", "plan_approved",
        "--product", "pilot-one",
        "--newer-than", "2026-10-24T00:00:00+00:00",
    )
    assert res.returncode == 1
    assert "FIND-EVENT FAIL: no matching event found" in res.stdout


def test_find_event_malformed_input_fails_closed(tmp_path: pathlib.Path):
    """Malformed input: corrupt YAML file fails closed rather than crashing."""
    events_dir = tmp_path / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    corrupt_file = events_dir / "corrupt_event.yaml"
    corrupt_file.write_text("event_type: [unclosed list:\n  - incomplete\n", encoding="utf-8")

    res = run_find_event(
        tmp_path,
        "--type", "plan_approved",
    )
    assert res.returncode == 1
    assert "FIND-EVENT FAIL: no matching event found" in res.stdout
