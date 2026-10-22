"""Unit tests for L2-T540: timegate."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "tools" / "evidence" / "fixtures" / "timegate"


def run_tool(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tools.evidence.timegate", *args]
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def _load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _run_fixture(name: str) -> subprocess.CompletedProcess[str]:
    fx = _load_fixture(name)
    return run_tool("--at", fx["at"], "--tz", fx["tz"], "--profile", fx["profile"], "--summary")


def test_friday_1459_is_ok():
    res = _run_fixture("friday-1459.yaml")
    assert res.returncode == 0
    assert "OK timegate checked=2 failed=0" in res.stdout


def test_friday_1501_breaches_cutoff_only():
    res = _run_fixture("friday-1501.yaml")
    assert res.returncode == 2
    assert "FAIL timegate checked=2 failed=1" in res.stdout
    assert "past 15:00 Friday cutoff" in res.stderr


def test_thursday_observation_overrun_breaches_core_hours_only():
    res = _run_fixture("thursday-1700-observation-overruns.yaml")
    assert res.returncode == 2
    assert "FAIL timegate checked=2 failed=1" in res.stdout
    assert "outside core hours" in res.stderr


def test_no_timezone_is_error():
    res = _run_fixture("no-timezone.yaml")
    assert res.returncode == 3
    assert "ERROR timegate checked=0 failed=0" in res.stdout
    assert "timezone string is empty" in res.stderr


def test_unknown_timezone_name_is_error():
    """Distinct code path from the empty-string case: a non-empty but invalid IANA name."""
    res = run_tool("--at", "2026-09-11T09:31:00Z", "--tz", "Not/AZone", "--profile",
                   "business-hours", "--summary")
    assert res.returncode == 3
    assert "ERROR timegate checked=0 failed=0" in res.stdout
    assert "unknown timezone" in res.stderr


def test_weekend_start_breaches_cond_1():
    """Saturday 10:00 IST: cond-1 (weekend) breaches, observation window stays in core hours."""
    res = run_tool("--at", "2026-09-12T04:30:00Z", "--tz", "Asia/Kolkata", "--profile",
                    "business-hours", "--summary")
    assert res.returncode == 2
    assert "FAIL timegate checked=2 failed=1" in res.stdout
    assert "deploy starts on a weekend" in res.stderr


def test_progressive_exception_bypasses_both_conditions():
    """Same instant as friday-1501 (a breach), but --progressive exempts it."""
    fx = _load_fixture("friday-1501.yaml")
    res = run_tool("--at", fx["at"], "--tz", fx["tz"], "--profile", fx["profile"],
                   "--progressive", "--summary")
    assert res.returncode == 0
    assert "OK timegate checked=2 failed=0" in res.stdout


def test_out_of_hours_auth_exception_bypasses_both_conditions():
    """Same instant as friday-1501 (a breach), but --out-of-hours-auth exempts it."""
    fx = _load_fixture("friday-1501.yaml")
    res = run_tool("--at", fx["at"], "--tz", fx["tz"], "--profile", fx["profile"],
                   "--out-of-hours-auth", "--summary")
    assert res.returncode == 0
    assert "OK timegate checked=2 failed=0" in res.stdout


def test_runner_environment_timezone_never_leaks():
    """Acceptance criterion 4: TZ env var must not change the result for identical inputs."""
    import os

    base_env = dict(os.environ)
    args = ("--at", "2026-09-11T15:01:00Z", "--tz", "Asia/Kolkata", "--profile",
            "business-hours", "--summary")

    env_utc = dict(base_env); env_utc["TZ"] = "UTC"
    env_ny = dict(base_env); env_ny["TZ"] = "America/New_York"

    res_utc = run_tool(*args, env=env_utc)
    res_ny = run_tool(*args, env=env_ny)

    assert res_utc.returncode == res_ny.returncode
    assert res_utc.stdout == res_ny.stdout
