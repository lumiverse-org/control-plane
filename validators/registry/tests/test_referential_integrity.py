"""Tests for R-REF-01 through R-REF-06 (L1-310, Section 15.5; SIG-02;
Section 20.1; Section 60.2; SIG-05; invariant 7).

Exercised directly against parsed YAML fixtures -- see r_svc_01.py and
test_service_schema.py for the FD-094 Option B precedent.

26 test functions across 16 fixture cases.
"""
import datetime
import os

import yaml

from validators.registry.rules import (
    r_ref_01,
    r_ref_02,
    r_ref_03,
    r_ref_04,
    r_ref_05,
    r_ref_06,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "refint")
TODAY = datetime.date(2026, 8, 27)


def _load(case, filename):
    path = os.path.join(FIXTURES_DIR, case, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _product(case):
    return _load(case, "product.yaml")


def _people(case):
    return _load(case, "people.yaml")


def _platform(case):
    return _load(case, "platform.yaml")


def _known_service_ids(case):
    services_root = os.path.join(FIXTURES_DIR, case, "registries", "services")
    if not os.path.isdir(services_root):
        return None
    ids = set()
    for entry in sorted(os.listdir(services_root)):
        svc_path = os.path.join(services_root, entry, "service.yaml")
        if not os.path.isfile(svc_path):
            continue
        with open(svc_path, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        ids.add(doc["identity"]["id"])
    return ids


# ---------------------------------------------------------------------------
# Group A -- fully_resolved, one function per rule, all assert == [] (6)
# ---------------------------------------------------------------------------


def test_fully_resolved_r_ref_01_clean():
    case = os.path.join("valid", "fully_resolved")
    assert r_ref_01.check(_product(case), _people(case)) == []


def test_fully_resolved_r_ref_02_clean():
    case = os.path.join("valid", "fully_resolved")
    assert r_ref_02.check(_product(case), TODAY) == []


def test_fully_resolved_r_ref_03_clean():
    case = os.path.join("valid", "fully_resolved")
    assert r_ref_03.check(_product(case), _known_service_ids(case)) == []


def test_fully_resolved_r_ref_04_clean():
    case = os.path.join("valid", "fully_resolved")
    assert r_ref_04.check(_product(case), _platform(case)) == []


def test_fully_resolved_r_ref_05_clean():
    case = os.path.join("valid", "fully_resolved")
    assert r_ref_05.check(_product(case)) == []


def test_fully_resolved_r_ref_06_clean():
    case = os.path.join("valid", "fully_resolved")
    assert r_ref_06.check(_product(case), _people(case), TODAY) == []


# ---------------------------------------------------------------------------
# Group B -- per-rule valid boundary (3)
# ---------------------------------------------------------------------------


def test_assignment_expires_today_is_valid_boundary():
    case = os.path.join("valid", "assignment_expires_today")
    assert r_ref_02.check(_product(case), TODAY) == []


def test_residency_region_agree_is_valid():
    case = os.path.join("valid", "residency_region_agree")
    assert r_ref_05.check(_product(case)) == []


def test_owner_on_leave_still_active_is_valid():
    case = os.path.join("valid", "owner_on_leave_still_active")
    assert r_ref_06.check(_product(case), _people(case), TODAY) == []


# ---------------------------------------------------------------------------
# Group C -- silence via loader-returned-None (missing sibling file) (3)
# ---------------------------------------------------------------------------


def test_product_only_no_people_silences_r_ref_01():
    case = os.path.join("valid", "product_only_no_people")
    assert _people(case) is None
    assert r_ref_01.check(_product(case), None) == []


def test_product_only_no_people_silences_r_ref_06():
    case = os.path.join("valid", "product_only_no_people")
    assert _people(case) is None
    assert r_ref_06.check(_product(case), None, TODAY) == []


def test_product_only_no_platform_silences_r_ref_04():
    case = os.path.join("valid", "product_only_no_platform")
    assert _platform(case) is None
    assert r_ref_04.check(_product(case), None) == []


# ---------------------------------------------------------------------------
# Group D -- silence via explicit None argument, contract-level (4)
# ---------------------------------------------------------------------------


def test_r_ref_01_silent_when_people_doc_is_none():
    doc = _product(os.path.join("valid", "fully_resolved"))
    assert r_ref_01.check(doc, None) == []


def test_r_ref_03_silent_when_known_service_ids_is_none():
    doc = _product(os.path.join("valid", "fully_resolved"))
    assert r_ref_03.check(doc, None) == []


def test_r_ref_04_silent_when_platform_doc_is_none():
    doc = _product(os.path.join("valid", "fully_resolved"))
    assert r_ref_04.check(doc, None) == []


def test_r_ref_06_silent_when_people_doc_is_none():
    doc = _product(os.path.join("valid", "fully_resolved"))
    assert r_ref_06.check(doc, None, TODAY) == []


# ---------------------------------------------------------------------------
# Group E -- invalid cases, one function per fixture (10)
# ---------------------------------------------------------------------------


def test_person_missing_triggers_r_ref_01():
    case = os.path.join("invalid", "person_missing")
    findings = r_ref_01.check(_product(case), _people(case))
    assert len(findings) == 1
    assert "dev-ghost" in findings[0]
    assert "does not exist in people.yaml" in findings[0]


def test_person_departed_triggers_r_ref_01():
    case = os.path.join("invalid", "person_departed")
    findings = r_ref_01.check(_product(case), _people(case))
    assert len(findings) == 1
    assert "dev-gone" in findings[0]
    assert "which is departed" in findings[0]


def test_assignment_expired_triggers_r_ref_02():
    case = os.path.join("invalid", "assignment_expired")
    findings = r_ref_02.check(_product(case), TODAY)
    assert len(findings) == 1
    assert "expired on 2026-01-01" in findings[0]


def test_service_missing_triggers_r_ref_03():
    case = os.path.join("invalid", "service_missing")
    known = _known_service_ids(case)
    assert known == {"other-svc"}
    findings = r_ref_03.check(_product(case), known)
    assert len(findings) == 1
    assert "ghost-svc" in findings[0]


def test_contract_version_unsupported_triggers_r_ref_04():
    case = os.path.join("invalid", "contract_version_unsupported")
    findings = r_ref_04.check(_product(case), _platform(case))
    assert len(findings) == 1
    assert "contract_version 2" in findings[0]
    assert "[1]" in findings[0]


def test_residency_region_conflict_triggers_r_ref_05():
    case = os.path.join("invalid", "residency_region_conflict")
    findings = r_ref_05.check(_product(case))
    assert len(findings) == 1
    assert "eu" in findings[0]
    assert "us-east-1" in findings[0]


def test_no_primary_owner_triggers_r_ref_06():
    case = os.path.join("invalid", "no_primary_owner")
    findings = r_ref_06.check(_product(case), _people(case), TODAY)
    assert len(findings) == 1
    assert "primary_owner" in findings[0]


def test_no_cross_reviewer_triggers_r_ref_06():
    case = os.path.join("invalid", "no_cross_reviewer")
    findings = r_ref_06.check(_product(case), _people(case), TODAY)
    assert len(findings) == 1
    assert "cross_reviewer" in findings[0]


def test_no_responder_triggers_r_ref_06():
    case = os.path.join("invalid", "no_responder")
    findings = r_ref_06.check(_product(case), _people(case), TODAY)
    assert len(findings) == 1
    assert "incident_responder" in findings[0]


def test_owner_departed_so_orphan_triggers_r_ref_06():
    case = os.path.join("invalid", "owner_departed_so_orphan")
    findings = r_ref_06.check(_product(case), _people(case), TODAY)
    assert len(findings) == 1
    assert "primary_owner" in findings[0]
