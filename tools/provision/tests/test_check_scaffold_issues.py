"""Unit tests for tools/provision/check-scaffold-issues (CP-0110, Section 19.1)."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CHECK_SCAFFOLD_ISSUES_SCRIPT = REPO_ROOT / "tools" / "provision" / "check-scaffold-issues"


def test_check_scaffold_issues_all_present(tmp_path: pathlib.Path):
    """Passes when all required issues (configure-checklist, alert-channel, support-intake) exist."""
    issues_data = [
        {"title": "CONFIGURE checklist -- pilot-one", "body": "1. environments\n2. verification contract\n..."},
        {"title": "Manual step -- alert_channel", "body": "Provision alert channel for pilot-one."},
        {"title": "Manual step -- support_intake_mailbox", "body": "Provision support intake mailbox for pilot-one."},
    ]
    fixture_file = tmp_path / "issues.json"
    fixture_file.write_text(json.dumps(issues_data), encoding="utf-8")

    cmd = [
        sys.executable,
        str(CHECK_SCAFFOLD_ISSUES_SCRIPT),
        "--product",
        "pilot-one",
        "--require",
        "configure-checklist,alert-channel,support-intake",
        "--fixture-issues",
        str(fixture_file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "CHECK-SCAFFOLD-ISSUES OK" in proc.stdout
    assert "configure-checklist, alert-channel, support-intake" in proc.stdout


def test_check_scaffold_issues_missing_items(tmp_path: pathlib.Path):
    """Fails and reports missing issue keys when required items are not tracked."""
    issues_data = [
        {"title": "CONFIGURE checklist -- pilot-one", "body": "Checklist details"},
    ]
    fixture_file = tmp_path / "issues_partial.json"
    fixture_file.write_text(json.dumps(issues_data), encoding="utf-8")

    cmd = [
        sys.executable,
        str(CHECK_SCAFFOLD_ISSUES_SCRIPT),
        "--product",
        "pilot-one",
        "--require",
        "configure-checklist,alert-channel,support-intake",
        "--fixture-issues",
        str(fixture_file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "CHECK-SCAFFOLD-ISSUES FAIL" in proc.stderr
    assert "missing required issue(s) for 'pilot-one': alert-channel, support-intake" in proc.stderr


def test_check_scaffold_issues_missing_fixture(tmp_path: pathlib.Path):
    """Fails cleanly when the fixture file does not exist."""
    missing = tmp_path / "missing.json"
    cmd = [
        sys.executable,
        str(CHECK_SCAFFOLD_ISSUES_SCRIPT),
        "--product",
        "pilot-one",
        "--fixture-issues",
        str(missing),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "fixture file not found" in proc.stderr
