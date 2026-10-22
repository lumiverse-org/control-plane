"""Tests for R-VER-03 (L1-403, Section 31.3).

Exercised by calling ``validators.registry.rules.r_ver_03`` directly
against parsed ``product.yaml`` / ``verification-contract.yaml``
fixture pairs, rather than through ``validators/registry/cli.py`` --
see the module docstring of ``r_ver_03.py`` and, for precedent,
``test_r_ver_02.py`` / ``test_r_prd_11.py``: FD-094 (contracts/
validator-contract.md) freezes the Option B R01..R18 dispatch engine
and its CLI grammar; the L1-005 discover()/RULE_ID/APPLIES_TO harness
never landed in this tree (validators/registry/rules/__init__.py is
empty), and extending the frozen catalogue for R-VER-03 is not this
task's call to make.

7 test functions: 4 valid, 3 invalid, matching the task's own
fixture-case table exactly.
"""
import os

import yaml

from validators.registry.rules import r_ver_03

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "ver03")


def _load(case, filename):
    path = os.path.join(FIXTURES_DIR, case, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _product(case):
    return _load(case, "product.yaml")


def _contract(case):
    return _load(case, "verification-contract.yaml")


def _findings(case):
    return r_ver_03.check(_product(case), _contract(case))


# ---------------------------------------------------------------------------
# valid (4)
# ---------------------------------------------------------------------------


def test_valid_high_with_performance():
    case = os.path.join("valid", "high_with_performance")
    assert _findings(case) == []


def test_valid_critical_with_performance():
    case = os.path.join("valid", "critical_with_performance")
    assert _findings(case) == []


def test_valid_medium_without_performance():
    case = os.path.join("valid", "medium_without_performance")
    assert _findings(case) == []


def test_contract_only_no_product_is_silent():
    case = os.path.join("valid", "contract_only_no_product")
    assert _product(case) is None
    assert _findings(case) == []


# ---------------------------------------------------------------------------
# invalid (3)
# ---------------------------------------------------------------------------


def test_high_performance_optional_triggers_r_ver_03():
    case = "high_performance_optional"
    findings = _findings(case)
    assert len(findings) == 1
    assert "reliability_criticality 'high'" in findings[0]
    assert "requires a declared performance mechanism" in findings[0]
    assert "Section 31.3" in findings[0]


def test_critical_performance_not_applicable_triggers_r_ver_03():
    case = "critical_performance_not_applicable"
    findings = _findings(case)
    assert len(findings) == 1
    assert "reliability_criticality 'critical'" in findings[0]
    assert "Section 31.3" in findings[0]


def test_high_required_but_profile_null_triggers_r_ver_03():
    case = "high_required_but_profile_null"
    findings = _findings(case)
    assert len(findings) == 1
    assert "reliability_criticality 'high'" in findings[0]
    assert "Section 31.3" in findings[0]
