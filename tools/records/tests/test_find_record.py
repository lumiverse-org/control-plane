"""Unit tests for tools/records/find-record query tool (§97.2).
Exercises happy path, negative path (record absent/mismatched/out of window),
and malformed input handling (fail-closed).
"""

from __future__ import annotations

import pathlib
import subprocess
import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
FIND_RECORD_SCRIPT = REPO_ROOT / "tools" / "records" / "find-record"


def to_bash_path(path: pathlib.Path) -> str:
    p = path.resolve().as_posix()
    if len(p) >= 2 and p[1] == ":":
        return f"/mnt/{p[0].lower()}{p[2:]}"
    return p


def run_find_record(cwd: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = ["bash", to_bash_path(FIND_RECORD_SCRIPT), *args]
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_find_record_happy_path(tmp_path: pathlib.Path):
    """Happy path: matching record exists in store with matching fields."""
    store_dir = tmp_path / "records" / "uat"
    store_dir.mkdir(parents=True, exist_ok=True)
    rec_path = store_dir / "UAT-2026-10-25-001.yaml"

    record_data = {
        "record_schema_version": 1,
        "id": "UAT-2026-10-25-001",
        "product": "pilot-one",
        "timestamp": "2026-10-25T10:00:00+00:00",
        "result": "pass",
        "mechanism": "manual_uat",
        "executed_by": "qa-1",
    }
    rec_path.write_text(yaml.safe_dump(record_data), encoding="utf-8")

    res = run_find_record(
        tmp_path,
        "--store", "records/uat",
        "--product", "pilot-one",
        "--require", "result=pass",
        "--require-present", "executed_by",
        "--require-fields", "record_schema_version,id,product,timestamp",
    )
    assert res.returncode == 0
    assert "FIND-RECORD PASS: found" in res.stdout
    assert "in store 'records/uat'" in res.stdout


def test_find_record_negative_absent_store_or_record(tmp_path: pathlib.Path):
    """Negative path: store exists but holds no records for target product."""
    store_dir = tmp_path / "records" / "uat"
    store_dir.mkdir(parents=True, exist_ok=True)

    res = run_find_record(
        tmp_path,
        "--store", "records/uat",
        "--product", "pilot-one",
    )
    assert res.returncode == 1
    assert "FIND-RECORD FAIL: no matching records found in store 'records/uat'" in res.stdout


def test_find_record_negative_mismatched_require(tmp_path: pathlib.Path):
    """Negative path: record attribute does not match --require."""
    store_dir = tmp_path / "records" / "uat"
    store_dir.mkdir(parents=True, exist_ok=True)
    rec_path = store_dir / "UAT-2026-10-25-001.yaml"

    record_data = {
        "record_schema_version": 1,
        "id": "UAT-2026-10-25-001",
        "product": "pilot-one",
        "result": "fail",
    }
    rec_path.write_text(yaml.safe_dump(record_data), encoding="utf-8")

    res = run_find_record(
        tmp_path,
        "--store", "records/uat",
        "--product", "pilot-one",
        "--require", "result=pass",
    )
    assert res.returncode == 1
    assert "FIND-RECORD FAIL: no matching records found in store 'records/uat'" in res.stdout


def test_find_record_negative_older_than(tmp_path: pathlib.Path):
    """Negative path: record timestamp is older than --newer-than boundary."""
    store_dir = tmp_path / "records" / "uat"
    store_dir.mkdir(parents=True, exist_ok=True)
    rec_path = store_dir / "UAT-2026-10-20-001.yaml"

    record_data = {
        "record_schema_version": 1,
        "id": "UAT-2026-10-20-001",
        "product": "pilot-one",
        "timestamp": "2026-10-20T10:00:00+00:00",
    }
    rec_path.write_text(yaml.safe_dump(record_data), encoding="utf-8")

    res = run_find_record(
        tmp_path,
        "--store", "records/uat",
        "--product", "pilot-one",
        "--newer-than", "2026-10-24T00:00:00+00:00",
    )
    assert res.returncode == 1
    assert "FIND-RECORD FAIL: no matching records found in store 'records/uat'" in res.stdout


def test_find_record_malformed_input_fails_closed(tmp_path: pathlib.Path):
    """Malformed input: corrupt record file fails closed rather than crashing."""
    store_dir = tmp_path / "records" / "uat"
    store_dir.mkdir(parents=True, exist_ok=True)
    corrupt_file = store_dir / "broken.json"
    corrupt_file.write_text("{\"invalid_json: unclosed", encoding="utf-8")

    res = run_find_record(
        tmp_path,
        "--store", "records/uat",
    )
    assert res.returncode == 1
    assert "FIND-RECORD FAIL: no matching records found in store 'records/uat'" in res.stdout
