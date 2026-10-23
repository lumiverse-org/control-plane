"""tools/evidence/tests/test_action_pins.py
Unit tests for action-pins ledger coverage validator (L2-T532).
"""

from pathlib import Path
from tools.evidence.check_action_pins import check_pins, get_ledger_pins, get_referenced_actions, main


def test_action_pins_ledger_covers_all_referenced_actions():
    ok, total, missing = check_pins()
    assert ok is True
    assert total >= 6
    assert len(missing) == 0


def test_ledger_has_valid_format():
    ledger_path = Path("tools/evidence/action-pins.txt")
    pins = get_ledger_pins(ledger_path)
    assert len(pins) >= 6
    for action, sha in pins:
        assert len(sha) == 40
        assert action.startswith("actions/")


def test_check_pins_negative_detects_missing_action(tmp_path):
    """Fail-closed negative test: incomplete ledger must report failure."""
    # Write an incomplete ledger containing only 1 of the >=6 required action pins
    incomplete_ledger = tmp_path / "action-pins.txt"
    incomplete_ledger.write_text(
        "actions/checkout v4.2.2 11bd71901bbe5b1630ceea73d27597364c9af683\n",
        encoding="utf-8",
    )
    ok, total, missing = check_pins(ledger_path=incomplete_ledger)
    assert ok is False
    assert total >= 6
    assert len(missing) >= 1
    # Verify that unledgered actions (such as setup-python or download-artifact) are flagged
    missing_actions = [act for act, _ in missing]
    assert any("setup-python" in act or "download-artifact" in act for act in missing_actions)


def test_cli_negative_returns_exit_code_2(tmp_path, capsys):
    """CLI negative test: CLI returns code 2 on missing action."""
    empty_ledger = tmp_path / "empty-action-pins.txt"
    empty_ledger.write_text("# empty ledger\n", encoding="utf-8")
    ret = main(["--ledger", str(empty_ledger), "--summary"])
    assert ret == 2
    captured = capsys.readouterr()
    assert "FAIL check_action_pins" in captured.out
    assert "unledgered action:" in captured.err
