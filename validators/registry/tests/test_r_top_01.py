"""Tests for R-TOP-01, R-TOP-02, R-TOP-03 (L1-503, Section 10.2, Section 66.2, Invariant 51, AT-016)."""
from __future__ import annotations

import os
import yaml

from validators.registry.rules import r_top_01, r_top_02, r_top_03

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "top01")


def _load(case: str, filename: str) -> dict | None:
    path = os.path.join(FIXTURES_DIR, case, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _person_ids(case: str) -> set[str] | None:
    doc = _load(case, "people.yaml")
    return None if doc is None else {p["id"] for p in doc.get("people", [])}


def _role_ids(case: str) -> set[str] | None:
    doc = _load(case, "roles.yaml")
    return None if doc is None else {r["id"] for r in doc.get("roles", [])}


def _domain_ids(case: str) -> set[str] | None:
    doc = _load(case, "topology.yaml")
    return None if doc is None else {d["id"] for d in doc.get("domains", [])}


# ---------------------------------------------------------------------------
# Valid (4)
# ---------------------------------------------------------------------------


def test_valid_at016_dormant():
    case = os.path.join("valid", "at016_dormant")
    prod = _load(case, "product.yaml")
    assert r_top_01.check(prod, _person_ids(case)) == []
    assert r_top_02.check(prod, _role_ids(case), _domain_ids(case)) == []
    assert r_top_03.check(_load(case, "topology.yaml")) == []


def test_valid_at016_activated():
    case_act = os.path.join("valid", "at016_activated")
    case_dorm = os.path.join("valid", "at016_dormant")
    prod = _load(case_act, "product.yaml")
    assert r_top_01.check(prod, _person_ids(case_act)) == []
    assert r_top_02.check(prod, _role_ids(case_act), _domain_ids(case_act)) == []
    assert r_top_03.check(_load(case_act, "topology.yaml")) == []

    p_dorm_bytes = open(os.path.join(FIXTURES_DIR, case_dorm, "product.yaml"), "rb").read()
    p_act_bytes = open(os.path.join(FIXTURES_DIR, case_act, "product.yaml"), "rb").read()
    assert p_dorm_bytes == p_act_bytes


def test_valid_dormant_resolves():
    case = os.path.join("valid", "dormant_resolves")
    prod = _load(case, "product.yaml")
    assert r_top_02.check(prod, _role_ids(case), _domain_ids(case)) == []


def test_valid_no_topology_file():
    case = os.path.join("valid", "no_topology_file")
    assert _load(case, "topology.yaml") is None
    prod = _load(case, "product.yaml")
    assert r_top_02.check(prod, _role_ids(case), _domain_ids(case)) == []


# ---------------------------------------------------------------------------
# Invalid (5)
# ---------------------------------------------------------------------------


def test_escalation_names_person_triggers_r_top_01():
    case = "escalation_names_person"
    prod = _load(case, "product.yaml")
    f = r_top_01.check(prod, _person_ids(case))
    assert len(f) == 1
    assert "R-TOP-01" in f[0]
    assert "dev-a" in f[0]
    assert "names a person" in f[0]


def test_escalation_unknown_role_triggers_r_top_02():
    case = "escalation_unknown_role"
    prod = _load(case, "product.yaml")
    f = r_top_02.check(prod, _role_ids(case), _domain_ids(case))
    assert len(f) == 1
    assert "R-TOP-02" in f[0]
    assert "architect" in f[0]
    assert "resolves to no role" in f[0]


def test_active_domain_null_lead_triggers_r_top_03():
    case = "active_domain_null_lead"
    topo = _load(case, "topology.yaml")
    f = r_top_03.check(topo)
    assert len(f) == 1
    assert "R-TOP-03" in f[0]
    assert "commerce" in f[0]
    assert "is active with no lead" in f[0]


def test_service_escalation_names_person_triggers_r_top_01():
    case = "service_escalation_names_person"
    svc = _load(case, "service.yaml")
    f = r_top_01.check(svc, {"dev-b"}, source="service.yaml")
    assert len(f) == 1
    assert "R-TOP-01" in f[0]
    assert "dev-b" in f[0]


def test_product_and_service_both_name_person_triggers_r_top_01_twice():
    case = "product_and_service_both_name_person"
    prod = _load(case, "product.yaml")
    svc = _load(case, "service.yaml")
    f1 = r_top_01.check(prod, _person_ids(case), source="product.yaml")
    f2 = r_top_01.check(svc, _person_ids(case), source="service.yaml")
    total = f1 + f2
    assert len(total) == 2
    assert all("R-TOP-01" in x and "dev-a" in x for x in total)
