"""Tests for L1-705: the schema-change checklist generator."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "validators.registry.tools.schema_change", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def _git_status() -> str:
    return subprocess.run(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True
    ).stdout


def test_emits_nine_steps():
    result = _run("--kind", "product", "--from", "2", "--to", "3")
    assert result.returncode == 0, result.stderr
    assert len(result.stdout.splitlines()) == 9


def test_step_order_matches_spec():
    result = _run("--kind", "product", "--from", "2", "--to", "3")
    lines = result.stdout.splitlines()
    assert lines[0].startswith("1.")
    assert lines[1].startswith("2.") and "alongside" in lines[1]
    assert lines[2].startswith("3.") and "BOTH" in lines[2]
    assert lines[8].startswith("9.")


def test_writes_no_files():
    before = _git_status()
    result = _run("--kind", "product", "--from", "2", "--to", "3")
    assert result.returncode == 0, result.stderr
    after = _git_status()
    assert before == after


def test_unknown_kind_is_exit_2():
    result = _run("--kind", "records", "--from", "1", "--to", "2")
    assert result.returncode == 2


def test_non_adjacent_version_is_exit_2():
    result = _run("--kind", "product", "--from", "1", "--to", "3")
    assert result.returncode == 2


def test_downgrade_is_exit_2():
    result = _run("--kind", "product", "--from", "2", "--to", "1")
    assert result.returncode == 2


def test_kind_list_matches_versioning_table():
    from validators.registry.tools.schema_change import build_parser
    from validators.registry.versioning import VERSION_FIELD

    parser = build_parser()
    kind_action = next(a for a in parser._actions if a.dest == "kind")
    assert set(kind_action.choices) == set(VERSION_FIELD)
