"""Unit tests for L2-T536: delta_gate."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "delta"


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.delta_gate", *args]
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def test_legacy_only_is_ok():
    res = run_tool(
        "--baseline", str(FIXTURES_DIR / "baseline.json"),
        "--current", str(FIXTURES_DIR / "legacy-only.json"),
        "--summary",
    )
    assert res.returncode == 0
    assert "OK delta_gate checked=3 failed=0" in res.stdout


def test_one_new_is_fail():
    res = run_tool(
        "--baseline", str(FIXTURES_DIR / "baseline.json"),
        "--current", str(FIXTURES_DIR / "one-new.json"),
        "--summary",
    )
    assert res.returncode == 2
    assert "FAIL delta_gate checked=4 failed=1" in res.stdout


def test_all_new_is_fail():
    res = run_tool(
        "--baseline", str(FIXTURES_DIR / "baseline.json"),
        "--current", str(FIXTURES_DIR / "all-new.json"),
        "--summary",
    )
    assert res.returncode == 2
    assert "FAIL delta_gate checked=3 failed=3" in res.stdout


def test_missing_baseline_is_error():
    res = run_tool(
        "--baseline", str(FIXTURES_DIR / "nope.json"),
        "--current", str(FIXTURES_DIR / "legacy-only.json"),
        "--summary",
    )
    assert res.returncode == 3
    assert "ERROR delta_gate checked=0 failed=0" in res.stdout
