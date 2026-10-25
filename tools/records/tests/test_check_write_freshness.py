"""Unit tests for tools/records/check-write-freshness verifier (§97.2, §53.1).
Exercises happy path, negative path (absent store, empty store, stale mtime),
and malformed input handling (fail-closed).
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import time
import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CHECK_FRESHNESS_SCRIPT = REPO_ROOT / "tools" / "records" / "check-write-freshness"

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


def run_check_freshness(cwd: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = ["bash", to_bash_path(CHECK_FRESHNESS_SCRIPT), *args]
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_check_write_freshness_happy_path(tmp_path: pathlib.Path):
    """Happy path: stores exist and hold recently-written record files."""
    dep_dir = tmp_path / "records" / "deployments"
    dep_dir.mkdir(parents=True, exist_ok=True)
    dep_file = dep_dir / "DEP-001.yaml"
    dep_file.write_text("id: DEP-001\nproduct: pilot-one\n", encoding="utf-8")

    uat_dir = tmp_path / "records" / "uat"
    uat_dir.mkdir(parents=True, exist_ok=True)
    uat_file = uat_dir / "UAT-001.yaml"
    uat_file.write_text("id: UAT-001\nproduct: pilot-one\n", encoding="utf-8")

    res = run_check_freshness(
        tmp_path,
        "--store", "records/deployments",
        "--store", "records/uat",
        "--fail-on", "blocking",
    )
    assert res.returncode == 0
    assert "CHECK-WRITE-FRESHNESS PASS: checked 2 store(s) within write-freshness window" in res.stdout


def test_check_write_freshness_negative_absent_store(tmp_path: pathlib.Path):
    """Negative path: store directory does not exist anywhere."""
    res = run_check_freshness(
        tmp_path,
        "--store", "records/nonexistent-store",
        "--fail-on", "blocking",
    )
    assert res.returncode == 1
    assert "CHECK-WRITE-FRESHNESS FAIL: 1 stores outside freshness window" in res.stdout
    assert "records/nonexistent-store: store empty or absent" in res.stdout


def test_check_write_freshness_negative_empty_store(tmp_path: pathlib.Path):
    """Negative path: store directory exists but contains zero record files."""
    empty_store = tmp_path / "records" / "empty_store"
    empty_store.mkdir(parents=True, exist_ok=True)

    res = run_check_freshness(
        tmp_path,
        "--store", "records/empty_store",
        "--fail-on", "blocking",
    )
    assert res.returncode == 1
    assert "CHECK-WRITE-FRESHNESS FAIL: 1 stores outside freshness window" in res.stdout
    assert "records/empty_store: store empty or absent" in res.stdout


def test_check_write_freshness_negative_stale_mtime(tmp_path: pathlib.Path):
    """Negative path: newest file in store exceeds 72-hour window."""
    dep_dir = tmp_path / "records" / "deployments"
    dep_dir.mkdir(parents=True, exist_ok=True)
    stale_file = dep_dir / "DEP-OLD.yaml"
    stale_file.write_text("id: DEP-OLD\n", encoding="utf-8")

    # Set mtime to 5 days ago (120 hours > 72 hours)
    old_time = time.time() - (5 * 86400)
    os.utime(stale_file, (old_time, old_time))

    res = run_check_freshness(
        tmp_path,
        "--store", "records/deployments",
        "--fail-on", "blocking",
    )
    assert res.returncode == 1
    assert "CHECK-WRITE-FRESHNESS FAIL: 1 stores outside freshness window" in res.stdout
    assert "records/deployments: last write was" in res.stdout


def test_check_write_freshness_nonrecord_files_fails_closed(tmp_path: pathlib.Path):
    """Malformed input: store contains only non-record extensions (.txt, .bak)."""
    dep_dir = tmp_path / "records" / "deployments"
    dep_dir.mkdir(parents=True, exist_ok=True)
    (dep_dir / "notes.txt").write_text("not a yaml or json record\n", encoding="utf-8")

    res = run_check_freshness(
        tmp_path,
        "--store", "records/deployments",
        "--fail-on", "blocking",
    )
    assert res.returncode == 1
    assert "CHECK-WRITE-FRESHNESS FAIL: 1 stores outside freshness window" in res.stdout
    assert "records/deployments: store empty or absent" in res.stdout
