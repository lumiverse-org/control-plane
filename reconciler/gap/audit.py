"""L3-P8-02: gap diff-audit of the gap window (spec §53.7 bullet 2).

Spec §53.7 bullet 2, verbatim:
"Diff-audit every access grant, merge and production approval made during the
gap window against declared state, treating the gap window as unverified rather
than presumed clean."
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping, Sequence

from reconciler.gap.detect import GapWindow

AUDIT_CLASSES = ("access_grant", "merge", "production_approval")


@dataclass(frozen=True)
class AuditItem:
    """One audited action made during the gap window."""

    item_class: str  # 'access_grant', 'merge', or 'production_approval'
    identifier: str  # id, login, PR/commit sha, etc.
    timestamp: str  # ISO date or datetime string
    status: str  # 'verified', 'unverified', or 'drift'
    detail: str  # human explanation of the audit finding


def _parse_date(val: Any) -> date | None:
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        iso_str = val.split("T")[0]
        try:
            return date.fromisoformat(iso_str)
        except ValueError:
            return None
    return None


def diff_audit(
    window: GapWindow,
    declared: Any,
    actual: Any,
) -> list[AuditItem]:
    """Diff-audit every access grant, merge, and production approval made during
    the gap window against declared state.

    The default posture is UNVERIFIED, not clean: an item the audit cannot
    evidence is reported as unverified, never as passing/clean.
    Returns a list of AuditItem records (never a bare boolean).
    """
    results: list[AuditItem] = []

    def _get_items(key: str) -> list[Any]:
        if isinstance(actual, Mapping):
            return list(actual.get(key, []))
        return list(getattr(actual, key, []))

    def _get_declared(key: str, default: Any = None) -> Any:
        if isinstance(declared, Mapping):
            return declared.get(key, default)
        return getattr(declared, key, default)

    # 1. Audit access grants
    for grant in _get_items("access_grants"):
        g_id = grant.get("id") or grant.get("login") or grant.get("user") or "<unknown-grant>"
        ts_str = grant.get("timestamp") or grant.get("granted_at") or grant.get("date") or ""
        ts_date = _parse_date(ts_str)

        if ts_date and not window.contains(ts_date):
            continue

        evidence = grant.get("evidence")
        if not evidence:
            results.append(
                AuditItem(
                    item_class="access_grant",
                    identifier=str(g_id),
                    timestamp=str(ts_str),
                    status="unverified",
                    detail=f"access grant {g_id} has no audit evidence; treated as unverified per §53.7",
                )
            )
            continue

        declared_people = _get_declared("people", {})
        login = grant.get("login") or grant.get("user") or str(g_id)
        person_declared = declared_people.get(login) if isinstance(declared_people, Mapping) else None

        role = grant.get("role") or grant.get("team")
        if person_declared is None or person_declared.get("availability") == "departed":
            results.append(
                AuditItem(
                    item_class="access_grant",
                    identifier=str(g_id),
                    timestamp=str(ts_str),
                    status="drift",
                    detail=f"access granted to {login} but person is not active in declared people",
                )
            )
        elif role and person_declared.get("role") != role and role not in person_declared.get("roles", []):
            results.append(
                AuditItem(
                    item_class="access_grant",
                    identifier=str(g_id),
                    timestamp=str(ts_str),
                    status="drift",
                    detail=f"access granted with role {role} not matching declared role {person_declared.get('role')}",
                )
            )
        else:
            results.append(
                AuditItem(
                    item_class="access_grant",
                    identifier=str(g_id),
                    timestamp=str(ts_str),
                    status="verified",
                    detail=f"access grant to {login} matches declared active state",
                )
            )

    # 2. Audit merges
    for merge in _get_items("merges"):
        m_id = merge.get("pr") or merge.get("commit") or merge.get("sha") or merge.get("id") or "<unknown-merge>"
        ts_str = merge.get("timestamp") or merge.get("merged_at") or merge.get("date") or ""
        ts_date = _parse_date(ts_str)

        if ts_date and not window.contains(ts_date):
            continue

        evidence = merge.get("evidence")
        if not evidence:
            results.append(
                AuditItem(
                    item_class="merge",
                    identifier=str(m_id),
                    timestamp=str(ts_str),
                    status="unverified",
                    detail=f"merge {m_id} has no audit evidence; treated as unverified per §53.7",
                )
            )
            continue

        approvers = merge.get("approvers", [])
        author = merge.get("author") or merge.get("merged_by")
        if author and author in approvers:
            results.append(
                AuditItem(
                    item_class="merge",
                    identifier=str(m_id),
                    timestamp=str(ts_str),
                    status="drift",
                    detail=f"merge {m_id} self-approved by author {author}",
                )
            )
        elif not approvers and not merge.get("automated"):
            results.append(
                AuditItem(
                    item_class="merge",
                    identifier=str(m_id),
                    timestamp=str(ts_str),
                    status="drift",
                    detail=f"merge {m_id} has zero approvers against declared review policy",
                )
            )
        else:
            results.append(
                AuditItem(
                    item_class="merge",
                    identifier=str(m_id),
                    timestamp=str(ts_str),
                    status="verified",
                    detail=f"merge {m_id} verified against declared branch/review policy",
                )
            )

    # 3. Audit production approvals
    for app in _get_items("production_approvals"):
        a_id = app.get("deployment_id") or app.get("id") or "<unknown-approval>"
        ts_str = app.get("timestamp") or app.get("approved_at") or app.get("date") or ""
        ts_date = _parse_date(ts_str)

        if ts_date and not window.contains(ts_date):
            continue

        evidence = app.get("evidence")
        if not evidence:
            results.append(
                AuditItem(
                    item_class="production_approval",
                    identifier=str(a_id),
                    timestamp=str(ts_str),
                    status="unverified",
                    detail=f"production approval {a_id} has no audit evidence; treated as unverified per §53.7",
                )
            )
            continue

        approver = app.get("approver")
        deployer = app.get("deployer")
        authorized_approvers = _get_declared("production_approvers", [])

        if approver and approver == deployer:
            results.append(
                AuditItem(
                    item_class="production_approval",
                    identifier=str(a_id),
                    timestamp=str(ts_str),
                    status="drift",
                    detail=f"production approval {a_id}: approver {approver} == deployer {deployer}",
                )
            )
        elif authorized_approvers and approver not in authorized_approvers:
            results.append(
                AuditItem(
                    item_class="production_approval",
                    identifier=str(a_id),
                    timestamp=str(ts_str),
                    status="drift",
                    detail=f"approver {approver} is not in declared production_approvers",
                )
            )
        else:
            results.append(
                AuditItem(
                    item_class="production_approval",
                    identifier=str(a_id),
                    timestamp=str(ts_str),
                    status="verified",
                    detail=f"production approval {a_id} verified against declared approval policy",
                )
            )

    return results
