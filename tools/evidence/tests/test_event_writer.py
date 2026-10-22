"""Unit tests for L2-T545: event_writer (tools.evidence.event_writer)."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.evidence.event_writer import ENVELOPE_FIELDS, EVENT_TYPE_TAXONOMY, validate_event

FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "events"


def run_tool(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    import os
    cmd = [sys.executable, "-m", "tools.evidence.event_writer", *args]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def test_dry_run_production_deployed_passes():
    event_file = str(FIXTURES_DIR / "production_deployed.yaml")
    res = run_tool("--event", event_file, "--dry-run", "--summary")
    assert res.returncode == 0
    assert "OK event_writer checked=9 failed=0" in res.stdout
    assert "DRY-RUN: event valid; would write to" in res.stderr
    assert "evt-20260906-001.yaml" in res.stderr


def test_missing_actor_fails():
    event_file = str(FIXTURES_DIR / "no-actor.yaml")
    res = run_tool("--event", event_file, "--dry-run", "--summary")
    assert res.returncode == 2
    assert "FAIL event_writer checked=9 failed=1" in res.stdout
    assert "FAIL: envelope field 'actor' missing or empty" in res.stderr


def test_free_text_type_fails():
    event_file = str(FIXTURES_DIR / "free-text-type.yaml")
    res = run_tool("--event", event_file, "--dry-run", "--summary")
    assert res.returncode == 2
    assert "FAIL event_writer checked=9 failed=1" in res.stdout
    assert "is not in Lane 4's published taxonomy" in res.stderr
    assert "we pushed some code today it went well" in res.stderr


def test_missing_event_file_errors():
    event_file = str(FIXTURES_DIR / "nonexistent.yaml")
    res = run_tool("--event", event_file, "--summary")
    assert res.returncode == 3
    assert "ERROR event_writer checked=0 failed=0" in res.stdout
    assert "event file not found" in res.stderr


def test_invalid_yaml_errors(tmp_path: Path):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("not a dict\n- a\n- b\n", encoding="utf-8")
    res = run_tool("--event", str(bad_yaml), "--summary")
    assert res.returncode == 3
    assert "ERROR event_writer checked=0 failed=0" in res.stdout
    assert "event must be a YAML mapping" in res.stderr


def test_live_write_creates_file_and_duplicate_fails(tmp_path: Path):
    # Run from tmp_path so records/events is written under tmp_path
    event_content = {
        "event_id": "evt-test-unique-001",
        "event_type": "staging_deployed",
        "occurred_at": "2026-10-22T08:00:00Z",
        "actor": "dev-tester",
        "environment": "staging",
        "product": "test-product",
        "artifact_digest": "sha256:11223344",
        "run_id": 1001,
        "correlation_id": "test-corr-001",
    }
    event_file = tmp_path / "test_event.yaml"
    event_file.write_text(yaml.safe_dump(event_content), encoding="utf-8")

    # First run: live write should succeed and create records/events/2026-10-22/evt-test-unique-001.yaml
    res = run_tool("--event", str(event_file), "--summary", cwd=tmp_path)
    assert res.returncode == 0
    assert "OK event_writer checked=9 failed=0" in res.stdout
    target_file = tmp_path / "records" / "events" / "2026-10-22" / "evt-test-unique-001.yaml"
    assert target_file.exists()

    # Second run: file already exists, live write must fail with exit 2 (one file per event rule)
    res2 = run_tool("--event", str(event_file), "--summary", cwd=tmp_path)
    assert res2.returncode == 2
    assert "FAIL event_writer checked=9 failed=1" in res2.stdout
    assert "FAIL: event file already exists" in res2.stderr


def test_validate_event_unit():
    valid_event = {
        "event_id": "evt-unit-01",
        "event_type": "production_deployed",
        "occurred_at": "2026-09-06T09:30:00Z",
        "actor": "dev-1",
        "environment": "production",
        "product": "myapp",
        "artifact_digest": "sha256:aaaa",
        "run_id": 99001,
        "correlation_id": "deploy-001",
    }
    checked, failed = validate_event(valid_event, EVENT_TYPE_TAXONOMY)
    assert checked == 9
    assert failed == 0

    # Test missing multiple fields
    invalid_event = {"event_id": "evt-01"}
    checked, failed = validate_event(invalid_event, EVENT_TYPE_TAXONOMY)
    assert checked == 9
    assert failed == 8  # 8 missing envelope fields


def test_source_code_has_no_append_mode():
    """Verify PARTITION.md rule 3: no shared mutable file / append mode (open 'a')."""
    source = (REPO_ROOT / "tools" / "evidence" / "event_writer.py").read_text(encoding="utf-8")
    assert re.search(r'open\([^)]*["\']a["\']', source) is None
