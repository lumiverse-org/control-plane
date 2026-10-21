"""L3-P8-05: tests for lane acceptance-matrix runner (spec §100)."""

from __future__ import annotations

import subprocess
import sys
import pytest

from reconciler.acceptance.run_matrix import MATRIX_TABLE, ATCase, run_matrix


def test_matrix_has_exactly_eleven_tests():
    assert len(MATRIX_TABLE) == 11


def test_every_matrix_row_names_implementing_task():
    for item in MATRIX_TABLE:
        assert item.implemented_by, f"{item.at_id} is missing implementing task"
        assert item.implemented_by.strip() != ""


def test_all_eleven_tests_pass_against_fixture_a():
    passed, total = run_matrix()
    assert total == 11
    assert passed == 11


def test_unmapped_task_fails_row(capsys):
    dummy_table = [
        ATCase("AT-999", "Dummy test", "", lambda: True)
    ]
    passed, total = run_matrix(dummy_table)
    assert passed == 0
    assert total == 1
    captured = capsys.readouterr()
    assert "error=unmapped_task" in captured.out


def test_summary_cli_output():
    cmd = [sys.executable, "-m", "reconciler.acceptance.run_matrix", "--summary"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    lines = proc.stdout.strip().splitlines()
    assert lines[-1] == "MATRIX passed=11 total=11"
    assert len(lines) == 12  # 11 AT lines + 1 MATRIX summary line
