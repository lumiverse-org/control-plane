"""tools/evidence/tests/test_action_pins.py
Unit tests for action-pins ledger coverage validator (L2-T532).
"""

from pathlib import Path
from tools.evidence.check_action_pins import check_pins, get_ledger_pins, get_referenced_actions


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
