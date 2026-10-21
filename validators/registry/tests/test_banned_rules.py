"""Tests for R-BAN-01, R-BAN-02, and R-BAN-03 (L1-803, Section 91.2;
Section 90.4 (D109); invariant 37; invariants 96-99; invariant 106;
AT-071; AT-075; AT-090).

Exercised directly against parsed YAML fixtures -- see r_svc_01.py and
test_policy_rules.py for the FD-094 Option B precedent.

18 test functions across 18 fixture cases.
"""
import json
import os

import yaml

from validators.registry.rules import r_ban_01, r_ban_02, r_ban_03

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "ban")


def _load(case, filename):
    path = os.path.join(FIXTURES_DIR, case, filename)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _findings_for(case, filename):
    doc = _load(case, filename)
    source = f"validators/registry/fixtures/ban/{case}/{filename}".replace("\\", "/")
    findings = []
    for mod in (r_ban_01, r_ban_02, r_ban_03):
        _, mod_findings = mod.check_document(doc, source=source)
        findings.extend(mod_findings)
    return findings


# ---------------------------------------------------------------------------
# valid cases (5)
# ---------------------------------------------------------------------------


def test_valid_clean_framework():
    assert _findings_for(os.path.join("valid", "clean_framework"), "framework.yaml") == []


def test_valid_clean_os_health():
    assert _findings_for(os.path.join("valid", "clean_os_health"), "os-health.yaml") == []


def test_valid_token_cost_in_tools_yaml():
    assert _findings_for(os.path.join("valid", "token_cost_in_tools_yaml"), "tools.yaml") == []


def test_valid_founder_delegate_clean_scope():
    assert _findings_for(os.path.join("valid", "founder_delegate_clean_scope"), "product.yaml") == []
    # Single-source assertion for EXCLUDED_DECISIONS
    schema_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..",
        "schemas", "registry", "common", "assignments.v1.schema.json"
    )
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    schema_decisions = schema["properties"]["scope"]["properties"]["decisions"]["not"]["contains"]["enum"]
    assert tuple(schema_decisions) == r_ban_02.EXCLUDED_DECISIONS


def test_valid_assignment_without_capabilities():
    assert _findings_for(os.path.join("valid", "assignment_without_capabilities"), "product.yaml") == []


# ---------------------------------------------------------------------------
# invalid cases (13)
# ---------------------------------------------------------------------------


def test_kpi_titled_hours_online_triggers_r_ban_01():
    findings = _findings_for("kpi_titled_hours_online", "framework.yaml")
    assert len(findings) == 1
    expected = (
        "R-BAN-01 validators/registry/fixtures/ban/kpi_titled_hours_online/framework.yaml:/kpis/0/title "
        "banned measurement 'hours-online' appears at /kpis/0/title; Section 91.2, invariants 96-99, AT-075"
    )
    assert findings[0] == expected


def test_kpi_definition_keystroke_triggers_r_ban_01():
    findings = _findings_for("kpi_definition_keystroke", "framework.yaml")
    assert len(findings) == 1
    assert "R-BAN-01" in findings[0]
    assert "keystroke" in findings[0]


def test_kpi_evidence_screenshot_triggers_r_ban_01():
    findings = _findings_for("kpi_evidence_screenshot", "framework.yaml")
    assert len(findings) == 1
    assert "R-BAN-01" in findings[0]
    assert "screenshot" in findings[0]


def test_kpi_ide_active_time_triggers_r_ban_01():
    findings = _findings_for("kpi_ide_active_time", "framework.yaml")
    assert len(findings) == 1
    assert "R-BAN-01" in findings[0]
    assert "ide-active-time" in findings[0]


def test_kpi_token_usage_as_kpi_triggers_r_ban_01():
    findings = _findings_for("kpi_token_usage_as_kpi", "framework.yaml")
    assert len(findings) == 1
    assert "R-BAN-01" in findings[0]
    assert "token-usage" in findings[0]


def test_kpi_flight_risk_triggers_r_ban_01():
    findings = _findings_for("kpi_flight_risk", "framework.yaml")
    assert len(findings) == 1
    assert "R-BAN-01" in findings[0]
    assert "flight-risk" in findings[0]


def test_kpi_engagement_inference_triggers_r_ban_01():
    findings = _findings_for("kpi_engagement_inference", "framework.yaml")
    assert len(findings) == 1
    assert "R-BAN-01" in findings[0]
    assert "engagement-score" in findings[0]


def test_kpi_leaderboard_triggers_r_ban_01():
    findings = _findings_for("kpi_leaderboard", "framework.yaml")
    assert len(findings) == 1
    assert "R-BAN-01" in findings[0]
    assert "leaderboard" in findings[0]


def test_kpi_single_productivity_score_triggers_r_ban_01():
    findings = _findings_for("kpi_single_productivity_score", "framework.yaml")
    assert len(findings) == 1
    assert "R-BAN-01" in findings[0]
    assert "productivity-score" in findings[0]


def test_signal_source_webcam_triggers_r_ban_01():
    findings = _findings_for("signal_source_webcam", "os-health.yaml")
    assert len(findings) == 1
    assert "R-BAN-01" in findings[0]
    assert "webcam" in findings[0]


def test_assignment_grants_people_intelligence_triggers_r_ban_02():
    findings = _findings_for("assignment_grants_people_intelligence", "product.yaml")
    assert len(findings) == 1
    expected = (
        "R-BAN-02 validators/registry/fixtures/ban/assignment_grants_people_intelligence/product.yaml:/assignments/0/scope/capabilities/0 "
        "assignment 'temporary_contributor' for 'dev-b' grants 'people-intelligence', which is not delegable; D109, invariant 106, AT-090"
    )
    assert findings[0] == expected


def test_founder_delegate_names_promotion_triggers_r_ban_02():
    findings = _findings_for("founder_delegate_names_promotion", "product.yaml")
    assert len(findings) == 1
    assert "R-BAN-02" in findings[0]
    assert "founder_decision_delegate" in findings[0]
    assert "'promotion'" in findings[0]


def test_field_auto_promotion_triggers_r_ban_03():
    findings = _findings_for("field_auto_promotion", "framework.yaml")
    assert len(findings) == 1
    assert "R-BAN-03" in findings[0]
    assert "auto_promotion" in findings[0]
