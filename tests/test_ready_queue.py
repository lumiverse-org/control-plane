"""Unit tests for scripts/l4/ready-queue.sh (FD-091/PFD-017, MasterSpec §29.4, §97.5).
Proves both a within-window item (not flagged, exit 0) and an over-window item
(flagged, exit 1 in check mode) are handled correctly.
"""

from __future__ import annotations

import pathlib
import subprocess
import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
READY_QUEUE_SCRIPT = REPO_ROOT / "scripts" / "l4" / "ready-queue.sh"


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


def run_ready_queue(cwd: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = ["bash", to_bash_path(READY_QUEUE_SCRIPT), *args]
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_ready_queue_within_window_not_flagged(tmp_path: pathlib.Path):
    """Item placed in ready 1 day ago is within the 3-day window: not flagged, exits 0."""
    work_file = tmp_path / "open.yaml"
    data = {
        "_meta": {"schema": "urn:multiproduct:schemas:work:open:v1"},
        "items": [
            {
                "id": "ITEM-001",
                "title": "Fresh ready item",
                "column": "ready",
                "ready_at": "2026-10-24T10:00:00Z",
                "product_id": "pilot-one",
            }
        ],
    }
    work_file.write_text(yaml.safe_dump(data), encoding="utf-8")

    res = run_ready_queue(
        REPO_ROOT,
        "--work-file", to_bash_path(work_file),
        "--as-of", "2026-10-25T10:00:00Z",
        "--check",
    )
    assert res.returncode == 0
    assert "Ready items: 1" in res.stdout
    assert "PASS: all 1 ready item(s) are within the 3.0-day window" in res.stdout
    assert "FLAGGED" not in res.stdout


def test_ready_queue_over_window_flagged(tmp_path: pathlib.Path):
    """Item placed in ready 5 days ago exceeds the 3-day window: flagged, exits 1."""
    work_file = tmp_path / "open.yaml"
    data = {
        "_meta": {"schema": "urn:multiproduct:schemas:work:open:v1"},
        "items": [
            {
                "id": "ITEM-002",
                "title": "Stale ready item",
                "column": "ready",
                "ready_at": "2026-10-20T10:00:00Z",
                "product_id": "pilot-one",
            }
        ],
    }
    work_file.write_text(yaml.safe_dump(data), encoding="utf-8")

    res = run_ready_queue(
        REPO_ROOT,
        "--work-file", to_bash_path(work_file),
        "--as-of", "2026-10-25T10:00:00Z",
        "--check",
    )
    assert res.returncode == 1
    assert "Ready items: 1" in res.stdout
    assert "FLAGGED: 1 ready item(s) exceed 3.0-day window:" in res.stdout
    assert "ITEM-002: age 5.0 days" in res.stdout


def test_ready_queue_empty_items(tmp_path: pathlib.Path):
    """Empty ready queue: exits 0 cleanly."""
    work_file = tmp_path / "open.yaml"
    data = {
        "_meta": {"schema": "urn:multiproduct:schemas:work:open:v1"},
        "items": [],
    }
    work_file.write_text(yaml.safe_dump(data), encoding="utf-8")

    res = run_ready_queue(
        REPO_ROOT,
        "--work-file", to_bash_path(work_file),
        "--check",
    )
    assert res.returncode == 0
    assert "Ready items: 0" in res.stdout
    assert "No ready items — queue miss check not needed" in res.stdout
