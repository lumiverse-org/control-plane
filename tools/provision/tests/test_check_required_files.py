"""Unit tests for tools/provision/check-required-files (CP-0103)."""

from __future__ import annotations

import pathlib
import subprocess
import sys
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CHECK_REQUIRED_FILES_SCRIPT = REPO_ROOT / "tools" / "provision" / "check-required-files"


def create_mock_scaffold(dir_path: pathlib.Path, items: list[str]) -> None:
    for item in items:
        target = dir_path / item
        if item.endswith("/"):
            target.mkdir(parents=True, exist_ok=True)
            # Create a placeholder file inside directory
            (target / "dummy.txt").write_text("placeholder", encoding="utf-8")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("dummy", encoding="utf-8")


def test_check_required_files_all_present(tmp_path: pathlib.Path):
    """Passes when all 8 required Section 33.1 items are present."""
    all_items = [
        ".env.example",
        "docker-compose.dev.yml",
        "Makefile",
        "seed/seed.json",
        "migrations/",
        "verification/",
        "AGENTS.md",
        "product.yaml",
    ]
    create_mock_scaffold(tmp_path, all_items)

    cmd = [sys.executable, str(CHECK_REQUIRED_FILES_SCRIPT), "--local-dir", str(tmp_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "CHECK-REQUIRED-FILES OK" in proc.stdout
    assert "all 8 Section 33.1 required items present" in proc.stdout


def test_check_required_files_missing_items(tmp_path: pathlib.Path):
    """Fails and reports missing items when required files are absent."""
    partial_items = [
        "Makefile",
        "AGENTS.md",
        "product.yaml",
    ]
    create_mock_scaffold(tmp_path, partial_items)

    cmd = [sys.executable, str(CHECK_REQUIRED_FILES_SCRIPT), "--local-dir", str(tmp_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "CHECK-REQUIRED-FILES FAIL" in proc.stderr
    assert ".env.example" in proc.stderr
    assert "docker-compose.dev.yml" in proc.stderr
    assert "seed data" in proc.stderr
    assert "migrations/" in proc.stderr
    assert "verification/" in proc.stderr


def test_check_required_files_accepts_product_pointer(tmp_path: pathlib.Path):
    """Section 33.1 permits .product-pointer in lieu of product.yaml."""
    items = [
        ".env.example",
        "docker-compose.dev.yml",
        "Makefile",
        "seed/init.sql",
        "migrations/",
        "verification/",
        "AGENTS.md",
        ".product-pointer",
    ]
    create_mock_scaffold(tmp_path, items)

    cmd = [sys.executable, str(CHECK_REQUIRED_FILES_SCRIPT), "--local-dir", str(tmp_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "CHECK-REQUIRED-FILES OK" in proc.stdout
