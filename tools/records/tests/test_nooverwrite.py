"""Unit tests for L4-P4-02: no-overwrite guard (tools.records.lib.nooverwrite).
Master Spec v4.0 Section 101.7 line 9516 (Invariant 48); L4-06-tasks.md row L4-P4-02; FD-131.
"""
from __future__ import annotations

import pathlib
import sys
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.records.lib.nooverwrite import assert_not_exists, safe_write


def test_assert_not_exists_passes_when_absent(tmp_path: pathlib.Path):
    target = tmp_path / "new_file.yaml"
    # Should not raise
    assert_not_exists(target)


def test_assert_not_exists_seeded_failure(tmp_path: pathlib.Path):
    target = tmp_path / "existing_file.yaml"
    target.write_text("existing content", encoding="utf-8")
    with pytest.raises(FileExistsError, match="overwrite-refused"):
        assert_not_exists(target)


def test_safe_write_creates_file(tmp_path: pathlib.Path):
    target = tmp_path / "sub" / "written.yaml"
    res = safe_write(target, "record_schema_version: 1\n")
    assert res.exists()
    assert res.read_text(encoding="utf-8") == "record_schema_version: 1\n"


def test_safe_write_seeded_failure_invariant_48(tmp_path: pathlib.Path):
    target = tmp_path / "protected.yaml"
    target.write_text("original content", encoding="utf-8")

    # Invariant 48: overwriting must be refused and original content preserved
    with pytest.raises(FileExistsError, match="overwrite-refused"):
        safe_write(target, "malicious replacement")

    assert target.read_text(encoding="utf-8") == "original content"
