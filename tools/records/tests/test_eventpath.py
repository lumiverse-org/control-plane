"""Unit tests for L4-P4-04: event path resolution (tools.records.lib.eventpath).
Master Spec v4.0 Section 97.3 line 8929; L4-06-tasks.md row L4-P4-04; FD-131.
"""
from __future__ import annotations

import pathlib
import sys
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.records.lib.eventpath import event_path


def test_event_path_valid():
    p = event_path("EVT-2026-10-22-000001", "2026-10-22T08:30:00+00:00")
    assert p == "events/2026-10-22/EVT-2026-10-22-000001.yaml"


def test_event_path_valid_with_z_offset():
    p = event_path("evt-12345", "2026-10-22T12:00:00Z")
    assert p == "events/2026-10-22/evt-12345.yaml"


def test_event_path_seeded_failure_naive_timestamp():
    # Naive timestamp without UTC offset must raise
    with pytest.raises(ValueError, match="timestamp-without-utc-offset"):
        event_path("EVT-001", "2026-10-22T08:30:00")


def test_event_path_seeded_failure_invalid_event_id():
    # Invalid characters or path traversal attempts
    with pytest.raises(ValueError, match="invalid-event-id"):
        event_path("../bad_id", "2026-10-22T08:30:00Z")

    with pytest.raises(ValueError, match="invalid-event-id"):
        event_path("", "2026-10-22T08:30:00Z")
