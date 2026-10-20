from pathlib import Path

from reconciler.contracts_map import CONTRACTS, load

EXPECTED_KEYS = {
    "drift_finding",
    "run_record",
    "repair_record",
    "branch_protection_template",
    "environment_template",
}


def test_exactly_five_keys_no_sixth():
    assert set(CONTRACTS.keys()) == EXPECTED_KEYS


def test_every_value_starts_with_contracts():
    for key, path in CONTRACTS.items():
        assert path.startswith("contracts/"), f"{key} -> {path!r} does not start with contracts/"


def test_every_value_exists_on_disk():
    for key, path in CONTRACTS.items():
        assert Path(path).exists(), f"{key} -> {path!r} does not exist on disk"


def test_load_returns_dict_for_each_key():
    for key in CONTRACTS:
        assert isinstance(load(key), dict), f"load({key!r}) did not return a dict"
