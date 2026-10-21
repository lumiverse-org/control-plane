"""Tests for R-VER-01, R-VER-11, R-VER-12, R-VER-13 (L1-702, Section 60.3, Invariant 74).

Exercised by calling ``validators.registry.rules.r_ver_10``, ``r_ver_11``,
``r_ver_12``, and ``r_ver_13`` directly against parsed fixture documents,
rather than through ``cli.py`` -- see precedent in ``r_prd_11.py`` and
``test_r_ver_02.py``: FD-094 (contracts/validator-contract.md) freezes the
Option B R01..R18 dispatch engine and its CLI grammar.

Exactly 14 test functions: 5 valid, 9 invalid, matching the task's own
fixture-case table.
"""
from __future__ import annotations

import os
import yaml

from validators.registry.rules import r_ver_10, r_ver_11, r_ver_12, r_ver_13

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "ver10")
TODAY = "2026-08-27"
_RULE_MODULES = (r_ver_10, r_ver_11, r_ver_12, r_ver_13)


def _load(case: str, filename: str = "product.yaml") -> dict | None:
    path = os.path.join(FIXTURES_DIR, case, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_case(case: str) -> tuple[dict | None, dict | None]:
    return _load(case, "product.yaml"), _load(case, "platform.yaml")


def _all_findings(product_doc: dict | None, platform_doc: dict | None) -> list[str]:
    findings = []
    for mod in _RULE_MODULES:
        findings.extend(mod.check(product_doc, platform_doc, TODAY))
    return findings


# ---------------------------------------------------------------------------
# Valid (5)
# ---------------------------------------------------------------------------


def test_valid_supported_in_set():
    p, pl = _load_case(os.path.join("valid", "supported_in_set"))
    assert _all_findings(p, pl) == []


def test_valid_transitional_full_migration_block():
    p, pl = _load_case(os.path.join("valid", "transitional_full_migration_block"))
    assert _all_findings(p, pl) == []


def test_valid_transitional_deadline_today():
    p, pl = _load_case(os.path.join("valid", "transitional_deadline_today"))
    assert _all_findings(p, pl) == []


def test_valid_supported_no_platform_file():
    p, pl = _load_case(os.path.join("valid", "supported_no_platform_file"))
    assert pl is None
    assert _all_findings(p, pl) == []


def test_valid_unsupported_absent():
    p, pl = _load_case(os.path.join("valid", "unsupported_absent"))
    assert _all_findings(p, pl) == []


# ---------------------------------------------------------------------------
# Invalid (9)
# ---------------------------------------------------------------------------


def test_supported_not_in_set():
    p, pl = _load_case("supported_not_in_set")
    f = r_ver_10.check(p, pl, TODAY)
    assert len(f) == 1
    assert "product-1" in f[0]
    assert "not in the supported set" in f[0]
    assert "Section 60.3" in f[0]
    assert r_ver_11.check(p, pl, TODAY) == []
    assert r_ver_12.check(p, pl, TODAY) == []
    assert r_ver_13.check(p, pl, TODAY) == []


def test_transitional_no_migration_block():
    p, pl = _load_case("transitional_no_migration_block")
    f = r_ver_11.check(p, pl, TODAY)
    assert len(f) == 1
    assert "product-1" in f[0]
    assert "declares no platform_migration" in f[0]
    assert "Section 60.3 and invariant 74" in f[0]
    assert r_ver_10.check(p, pl, TODAY) == []
    assert r_ver_12.check(p, pl, TODAY) == []
    assert r_ver_13.check(p, pl, TODAY) == []


def test_transitional_no_owner():
    p, pl = _load_case("transitional_no_owner")
    f = r_ver_11.check(p, pl, TODAY)
    assert len(f) == 1
    assert "product-1" in f[0]
    assert "declares no owner" in f[0]
    assert "Section 60.3 and invariant 74" in f[0]
    assert r_ver_10.check(p, pl, TODAY) == []
    assert r_ver_12.check(p, pl, TODAY) == []
    assert r_ver_13.check(p, pl, TODAY) == []


def test_transitional_no_target():
    p, pl = _load_case("transitional_no_target")
    f = r_ver_11.check(p, pl, TODAY)
    assert len(f) == 1
    assert "product-1" in f[0]
    assert "declares no target_contract_version" in f[0]
    assert "Section 60.3 and invariant 74" in f[0]
    assert r_ver_10.check(p, pl, TODAY) == []
    assert r_ver_12.check(p, pl, TODAY) == []
    assert r_ver_13.check(p, pl, TODAY) == []


def test_transitional_no_deadline():
    p, pl = _load_case("transitional_no_deadline")
    f = r_ver_11.check(p, pl, TODAY)
    assert len(f) == 1
    assert "product-1" in f[0]
    assert "declares no deadline" in f[0]
    assert "Section 60.3 and invariant 74" in f[0]
    assert r_ver_10.check(p, pl, TODAY) == []
    assert r_ver_12.check(p, pl, TODAY) == []
    assert r_ver_13.check(p, pl, TODAY) == []


def test_transitional_past_deadline():
    p, pl = _load_case("transitional_past_deadline")
    f = r_ver_12.check(p, pl, TODAY)
    assert len(f) == 1
    assert "product-1" in f[0]
    assert "is past its migration deadline 2026-08-26" in f[0]
    assert "Section 60.3, SIG-10, invariant 74" in f[0]
    assert r_ver_10.check(p, pl, TODAY) == []
    assert r_ver_11.check(p, pl, TODAY) == []
    assert r_ver_13.check(p, pl, TODAY) == []


def test_unsupported_declared():
    p, pl = _load_case("unsupported_declared")
    f = r_ver_13.check(p, pl, TODAY)
    assert len(f) == 1
    assert "product-1" in f[0]
    assert "is unsupported" in f[0]
    assert "Section 60.3 blocks deployment until it migrates" in f[0]
    assert r_ver_10.check(p, pl, TODAY) == []
    assert r_ver_11.check(p, pl, TODAY) == []
    assert r_ver_12.check(p, pl, TODAY) == []


def test_transitional_missing_two_fields():
    p, pl = _load_case("transitional_missing_two_fields")
    f = r_ver_11.check(p, pl, TODAY)
    assert len(f) == 2
    assert "declares no owner" in f[0]
    assert "declares no deadline" in f[1]
    assert r_ver_10.check(p, pl, TODAY) == []
    assert r_ver_12.check(p, pl, TODAY) == []
    assert r_ver_13.check(p, pl, TODAY) == []


def test_two_products_two_offenders():
    pa = _load("two_products_two_offenders", "product_a.yaml")
    pb = _load("two_products_two_offenders", "product_b.yaml")
    pl = _load("two_products_two_offenders", "platform.yaml")
    fa = _all_findings(pa, pl)
    fb = _all_findings(pb, pl)
    total = fa + fb
    assert len(total) == 2
    assert any("product-a" in x and "not in the supported set" in x for x in total)
    assert any("product-b" in x and "is unsupported" in x for x in total)
