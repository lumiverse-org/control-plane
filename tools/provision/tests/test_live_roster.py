"""Unit tests for tools.provision.live_roster and live roster plan creation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from unittest.mock import MagicMock, patch

from tools.provision import cli
from tools.provision.create_product import build_create_product_plan_against_live_roster
from tools.provision.live_roster import live_registered_product_ids

REPO_ROOT = Path(__file__).resolve().parents[3]
ONBOARDING_ROOT = REPO_ROOT / "docs" / "onboarding" / "products"


def test_live_registered_product_ids_returns_seven_real_products():
    """Verify live_registered_product_ids returns exactly the 7 real product IDs today."""
    ids = live_registered_product_ids()
    assert isinstance(ids, tuple)
    assert len(ids) == 7
    assert ids == (
        "Product-1",
        "Product-2",
        "Product-3",
        "Product-4",
        "Product-5",
        "Product-7",
        "Product-8",
    )


def test_slot_06_is_genuinely_excluded():
    """Verify slot 06 exists on disk as a fixture/placeholder but is excluded by live_registered_product_ids."""
    slot_06_file = ONBOARDING_ROOT / "06" / "facts.tsv"
    assert slot_06_file.is_file(), "Expected docs/onboarding/products/06/facts.tsv to exist"
    assert "Product-6" in slot_06_file.read_text(encoding="utf-8")

    ids = live_registered_product_ids()
    assert "Product-6" not in ids
    assert len(ids) == 7


def test_live_roster_parsing_with_synthetic_fixtures(tmp_path: Path):
    """Verify facts.tsv extraction logic and exclusion logic against synthetic test fixtures."""
    # Slot 01: valid product
    s01 = tmp_path / "01"
    s01.mkdir()
    (s01 / "facts.tsv").write_text("product_id\tSynthetic-Alpha\nrepository\tSynthetic-Alpha\n", encoding="utf-8")

    # Slot 02: valid product
    s02 = tmp_path / "02"
    s02.mkdir()
    (s02 / "facts.tsv").write_text("product_id\tSynthetic-Beta\nteam\tplatform\n", encoding="utf-8")

    # Slot 06: excluded slot name
    s06 = tmp_path / "06"
    s06.mkdir()
    (s06 / "facts.tsv").write_text("product_id\tSynthetic-Fixture-06\n", encoding="utf-8")

    # Slot 07: product_id Product-6 is also excluded
    s07 = tmp_path / "07"
    s07.mkdir()
    (s07 / "facts.tsv").write_text("product_id\tProduct-6\n", encoding="utf-8")

    # Slot 08: valid product
    s08 = tmp_path / "08"
    s08.mkdir()
    (s08 / "facts.tsv").write_text("product_id\tSynthetic-Gamma\n", encoding="utf-8")

    # Slot 09: directory without facts.tsv
    (tmp_path / "09").mkdir()

    # Slot 10: facts.tsv without product_id line
    s10 = tmp_path / "10"
    s10.mkdir()
    (s10 / "facts.tsv").write_text("other_field\tvalue\n", encoding="utf-8")

    result = live_registered_product_ids(tmp_path)
    assert result == ("Synthetic-Alpha", "Synthetic-Beta", "Synthetic-Gamma")


def test_live_roster_plan_builder_reflects_live_count():
    """Verify build_create_product_plan_against_live_roster constructs a 13-step plan citing live counts."""
    plan = build_create_product_plan_against_live_roster("Product-9")
    assert len(plan.steps) == 13
    assert len(plan.manual_steps) == 2

    # 7 real products registered today, Product-9 makes 8
    expected_note = "7 product(s) registered today, Product-9 would make 8"
    for step_id in (
        "register_portfolio_board",
        "register_grafana_scorecard_devlake",
        "register_dependency_graph",
    ):
        step = next(s for s in plan.steps if s.id == step_id)
        assert expected_note in step.description


@patch("subprocess.run")
def test_cli_live_roster_dry_run_and_apply_rejection(mock_run: MagicMock):
    """Verify CLI behavior with --roster-source live."""
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=1, stderr="mock failure")
    # Clean dry-run
    rc = cli.main(["create-product", "--live", "--roster-source", "live", "--product", "Product-9"])
    assert rc == 0

    # Incompatible with --apply or fails closed without live authorization
    rc_apply = cli.main(["create-product", "--live", "--roster-source", "live", "--product", "Product-9", "--apply"])
    assert rc_apply == 1

    # Incompatible with --fixture
    rc_fixture = cli.main(["create-product", "--fixture", "fixture-a", "--roster-source", "live", "--product", "Product-9"])
    assert rc_fixture == 1


def test_cli_live_roster_steps_output_via_subprocess():
    """Verify subprocess output prints steps containing live roster enumeration."""
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.provision.cli",
            "create-product",
            "--live",
            "--roster-source",
            "live",
            "--product",
            "Product-9",
            "--steps",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "PLAN create-product steps=13 writes=0 manual=2" in proc.stdout
    assert "7 product(s) registered today, Product-9 would make 8" in proc.stdout
    assert "11. [write] register_portfolio_board:" in proc.stdout
    assert "12. [write] register_grafana_scorecard_devlake:" in proc.stdout
    assert "13. [write] register_dependency_graph:" in proc.stdout
