"""R-BAN-01 -- banned measurement tokens appearing in KPI/signal fields.

Section 91.2; invariants 96-99; AT-075 (task L1-803).

Standalone, directly-tested rule function -- see r_svc_01.py for the
FD-094 Option B precedent.
"""
from __future__ import annotations

import re

RULE_ID = "R-BAN-01"
SPEC = "Section 91.2"
APPLIES_TO = ["framework", "os-health"]

BANNED_TOKENS = (
    "keystroke", "keylog", "screen-monitoring", "screenshot", "screen-capture",
    "activity-surveillance", "webcam", "presence-detection", "hours-online",
    "hours-at-desk", "time-at-desk", "token-usage", "tokens-used",
    "ide-active-time", "active-editor-time", "flight-risk",
    "resignation-prediction", "attrition-prediction", "emotional-state",
    "engagement-score", "motivation-score", "wellbeing-score", "mental-health",
    "surveillance-score", "productivity-score", "employee-ranking",
    "leaderboard", "stack-rank",
)

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _normalize(value: str) -> str:
    return _NON_ALNUM.sub("-", value.casefold()).strip("-")


def check_document(doc: dict | None, source: str = "framework.yaml") -> tuple[bool, list[str]]:
    if not isinstance(doc, dict):
        return True, []
    findings = []
    # Scan kpis
    for k_idx, kpi in enumerate(doc.get("kpis") or []):
        if not isinstance(kpi, dict):
            continue
        for field in ("id", "title", "definition"):
            val = kpi.get(field)
            if isinstance(val, str):
                norm = _normalize(val)
                pointer = f"/kpis/{k_idx}/{field}"
                for token in BANNED_TOKENS:
                    if token in norm:
                        findings.append(
                            f"{RULE_ID} {source}:{pointer} banned measurement '{token}' appears at {pointer}; Section 91.2, invariants 96-99, AT-075"
                        )
        for e_idx, ev in enumerate(kpi.get("evidence_sources") or []):
            if isinstance(ev, str):
                norm = _normalize(ev)
                pointer = f"/kpis/{k_idx}/evidence_sources/{e_idx}"
                for token in BANNED_TOKENS:
                    if token in norm:
                        findings.append(
                            f"{RULE_ID} {source}:{pointer} banned measurement '{token}' appears at {pointer}; Section 91.2, invariants 96-99, AT-075"
                        )
    # Scan signals
    for s_idx, sig in enumerate(doc.get("signals") or []):
        if not isinstance(sig, dict):
            continue
        for field in ("name", "definition", "source"):
            val = sig.get(field)
            if isinstance(val, str):
                norm = _normalize(val)
                pointer = f"/signals/{s_idx}/{field}"
                for token in BANNED_TOKENS:
                    if token in norm:
                        findings.append(
                            f"{RULE_ID} {source}:{pointer} banned measurement '{token}' appears at {pointer}; Section 91.2, invariants 96-99, AT-075"
                        )
    return len(findings) == 0, findings
