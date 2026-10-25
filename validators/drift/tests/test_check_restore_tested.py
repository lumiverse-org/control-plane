"""Unit tests for validators/drift/check-restore-tested verifier (Invariant #4, CP-1107).
Exercises happy path, negative path (absent record, failing record, wrong product),
and malformed input handling (fail-closed).
"""

from __future__ import annotations

import pathlib
import subprocess
import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CHECK_RESTORE_SCRIPT = REPO_ROOT / "validators" / "drift" / "check-restore-tested"

_IS_WSL = None


def _check_is_wsl() -> bool:
    global _IS_WSL
    if _IS_WSL is None:
        try:
            res = subprocess.run(["bash", "-c", "uname -s"], capture_output=True, text=True, timeout=2)
            _IS_WSL = "Linux" in res.stdout
        except Exception:
            _IS_WSL = False
    return _IS_WSL


def to_bash_path(path: pathlib.Path) -> str:
    p = path.resolve().as_posix()
    if len(p) >= 2 and p[1] == ":":
        if _check_is_wsl():
            return f"/mnt/{p[0].lower()}{p[2:]}"
        else:
            return f"/{p[0].lower()}{p[2:]}"
    return p


def run_check_restore_tested(cwd: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = ["bash", to_bash_path(CHECK_RESTORE_SCRIPT), *args]
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_check_restore_tested_happy_path(tmp_path: pathlib.Path):
    """Happy path: a passing restore-test record exists for the product."""
    restore_dir = tmp_path / "records" / "restore-tests"
    restore_dir.mkdir(parents=True, exist_ok=True)
    rec_file = restore_dir / "RESTORE-001.yaml"

    record_data = {
        "record_schema_version": 1,
        "id": "RESTORE-001",
        "product": "pilot-one",
        "result": "pass",
        "timestamp": "2026-10-25T10:00:00+00:00",
        "integrity_check": "sha256-verified",
        "verified_by": "qa-1",
    }
    rec_file.write_text(yaml.safe_dump(record_data), encoding="utf-8")

    res = run_check_restore_tested(
        tmp_path,
        "--product", "pilot-one",
        "--fail-on-unevidenced",
    )
    assert res.returncode == 0
    assert "CHECK-RESTORE-TESTED PASS: restore_tested verified against passing record for product 'pilot-one'" in res.stdout


def test_check_restore_tested_negative_no_passing_record(tmp_path: pathlib.Path):
    """Negative path: restore-test record exists for product but result is not 'pass'."""
    restore_dir = tmp_path / "records" / "restore-tests"
    restore_dir.mkdir(parents=True, exist_ok=True)
    rec_file = restore_dir / "RESTORE-001.yaml"

    record_data = {
        "record_schema_version": 1,
        "id": "RESTORE-001",
        "product": "pilot-one",
        "result": "fail",
    }
    rec_file.write_text(yaml.safe_dump(record_data), encoding="utf-8")

    res = run_check_restore_tested(
        tmp_path,
        "--product", "pilot-one",
        "--fail-on-unevidenced",
    )
    assert res.returncode == 1
    assert "CHECK-RESTORE-TESTED FAIL: unevidenced restore_tested date" in res.stdout


def test_check_restore_tested_negative_wrong_product(tmp_path: pathlib.Path):
    """Negative path: passing restore-test record exists but for a different product."""
    restore_dir = tmp_path / "records" / "restore-tests"
    restore_dir.mkdir(parents=True, exist_ok=True)
    rec_file = restore_dir / "RESTORE-001.yaml"

    record_data = {
        "record_schema_version": 1,
        "id": "RESTORE-001",
        "product": "other-product",
        "result": "pass",
    }
    rec_file.write_text(yaml.safe_dump(record_data), encoding="utf-8")

    res = run_check_restore_tested(
        tmp_path,
        "--product", "pilot-one",
        "--fail-on-unevidenced",
    )
    assert res.returncode == 1
    assert "CHECK-RESTORE-TESTED FAIL: unevidenced restore_tested date" in res.stdout


def test_check_restore_tested_malformed_input_fails_closed(tmp_path: pathlib.Path):
    """Malformed input: corrupt YAML record file fails closed rather than crashing."""
    restore_dir = tmp_path / "records" / "restore-tests"
    restore_dir.mkdir(parents=True, exist_ok=True)
    (restore_dir / "corrupt.yaml").write_text("product: [broken {yaml", encoding="utf-8")

    res = run_check_restore_tested(
        tmp_path,
        "--product", "pilot-one",
        "--fail-on-unevidenced",
    )
    assert res.returncode == 1
    assert "CHECK-RESTORE-TESTED FAIL: unevidenced restore_tested date" in res.stdout
