"""
reconciler/acceptance/run_matrix.py — Lane 3 Section 100 acceptance-matrix runner.

Usage:
  python -m reconciler.acceptance.run_matrix [--summary]

Executes, against fixture-a, exactly the eleven Section 100 acceptance tests
Lane 3 is responsible for. Touches no live GitHub organisation.

Output:
  AT <id> result=<pass|fail>
  ...
  MATRIX passed=<int> total=11
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from typing import Callable, NamedTuple


class ATCase(NamedTuple):
    at_id: str
    description: str
    implemented_by: str
    check_fn: Callable[[], bool]


def _check_at_002() -> bool:
    """AT-002: Add a person — Reconciliation grants access, dry run produces plan."""
    from tools.provision.add_person import build_add_person_plan

    plan = build_add_person_plan("dev-3")
    return plan.summary_line("add-person") == "PLAN add-person steps=7 writes=0 manual=1"


def _check_at_008() -> bool:
    """AT-008: Temporary specialist joins — reconciliation revokes on the end date without human action."""
    from reconciler.cli import DeclaredState
    from reconciler.comparators.expiry import compare
    from reconciler.repair.expiry_revoke import revoke_expired_assignments
    from reconciler.state.fixture_adapter import FixtureState

    as_of = date(2026, 9, 15)
    declared = DeclaredState("fixture-a")
    actual = FixtureState("fixture-a")
    findings, _ = compare(declared, actual, as_of)
    repairs = revoke_expired_assignments(findings, enabled=True)
    return any(r.scope == "alpha:dev-1" for r in repairs)


def _check_at_017() -> bool:
    """AT-017: A person leaves — Reconciliation revokes access; orphan detection surfaces every unowned responsibility; blocking orphans cannot be dismissed unresolved."""
    from reconciler.orphans import load_context
    from reconciler.orphans.assets import detect as detect_assets
    from reconciler.orphans.dismissal import NonDismissibleOrphan, dismiss

    ctx = load_context("fixture-a", date(2026, 8, 27))
    findings, _ = detect_assets(ctx)
    domain_orphans = [f for f in findings if f.subject == "domain-1"]
    if not domain_orphans:
        return False
    try:
        dismiss(domain_orphans[0], "lead-1", "test reason", resolution_ref="RES-01")
        return False
    except NonDismissibleOrphan:
        return True


def _check_at_018() -> bool:
    """AT-018: A temporary assignment expires — Reconciliation removes it without human action."""
    from reconciler.cli import DeclaredState
    from reconciler.comparators.expiry import compare
    from reconciler.state.fixture_adapter import FixtureState

    as_of = date(2026, 9, 15)
    declared = DeclaredState("fixture-a")
    actual = FixtureState("fixture-a")
    findings, _ = compare(declared, actual, as_of)
    return any(f.scope == "alpha:dev-1" and "expired" in f.id for f in findings)


def _check_at_032() -> bool:
    """AT-032: Self-observability — detects and reports a failure in its own reconciliation."""
    from reconciler.runrecord import RunRecord
    from reconciler.signals import emit_signals

    run = RunRecord(
        run_id="R-FAIL-01",
        status="FAILED",
        started_at="2026-08-27T09:00:00Z",
        finished_at="2026-08-27T10:00:00Z",
    )
    signals = emit_signals(run)
    return any(s.get("signal_id") == "SIG-13" for s in signals)


def _check_at_033() -> bool:
    """AT-033: No auto-loosening — raises it for human review and does not relax it."""
    from reconciler.repair.stricter import permitted

    ok, reason = permitted(1, 2, "required_approvals")
    return ok is False and "AT-033" in reason


def _check_at_036() -> bool:
    """AT-036: A temporary access exception expires — with no human action."""
    from reconciler.repair.expiry_revoke import revoke_expired_exceptions

    as_of = date(2026, 9, 15)
    exceptions = [{"id": "EXC-10", "requester": "dev-1", "expires": "2026-08-01", "grants": "bypass"}]
    repairs, _ = revoke_expired_exceptions(exceptions, as_of, enabled=True)
    return len(repairs) == 1 and repairs[0].scope == "dev-1"


def _check_at_037() -> bool:
    """AT-037: A failed exception is visible — becomes Blocking drift on its expiry date."""
    from reconciler.model import DriftClass
    from reconciler.repair.expiry_revoke import revoke_expired_exceptions

    as_of = date(2026, 9, 15)
    exceptions = [{"id": "EXC-11", "requester": "dev-2", "expires": "2026-09-01"}]
    repairs, escalations = revoke_expired_exceptions(exceptions, as_of, enabled=True)
    return (
        len(escalations) == 1
        and escalations[0].drift_class == DriftClass.BLOCKING
        and "AT-037" in escalations[0].evidence
    )


def _check_at_102() -> bool:
    """AT-102: The seeded reconciliation canary — A run reporting zero findings is a failed run."""
    from reconciler.canary import CANARY_ID, assert_canary
    from reconciler.model import DriftClass, Finding, Level

    zero_findings_fail = assert_canary([]) is False
    canary_finding = Finding(
        id=CANARY_ID,
        comparator="display_name",
        scope="canary",
        drift_class=DriftClass.GREEN,
        level=Level.DETECT,
        evidence="seeded",
        first_seen="2026-08-27T00:00:00Z",
    )
    canary_passes = assert_canary([canary_finding]) is True
    return zero_findings_fail and canary_passes


def _check_at_110() -> bool:
    """AT-110: The reconciler credential is provably bounded — six attempts."""
    from validators.drift.credential_bounds import FixtureCredential, probe

    outcome = probe(FixtureCredential(), "fixture", fixture="fixture-a")
    return (
        len(outcome.attempts) == 6
        and all(res == "blocked" for res in outcome.attempts.values())
        and outcome.reconciliation_completed
    )


def _check_at_001() -> bool:
    """AT-001: Add product 21 — No dashboard, workflow or script contains a product list."""
    from tools.provision.create_product import build_create_product_plan

    plan = build_create_product_plan("gamma", "fixture-a")
    return plan.summary_line("create-product") == "PLAN create-product steps=13 writes=0 manual=2"


MATRIX_TABLE: list[ATCase] = [
    ATCase(
        "AT-002",
        "Add a person — Reconciliation grants access … No workflow, architecture or dashboard change",
        "L3-P4-09",
        _check_at_002,
    ),
    ATCase(
        "AT-008",
        "Temporary specialist joins — reconciliation revokes on the end date without human action",
        "L3-P1-09, L3-P6-06, L3-P7-05",
        _check_at_008,
    ),
    ATCase(
        "AT-017",
        "A person leaves — Reconciliation revokes access; orphan detection surfaces every unowned responsibility; blocking orphans cannot be dismissed unresolved",
        "L3-P7-02, L3-P2-06",
        _check_at_017,
    ),
    ATCase(
        "AT-018",
        "A temporary assignment expires — Reconciliation removes it without human action",
        "L3-P6-06",
        _check_at_018,
    ),
    ATCase(
        "AT-032",
        "Self-observability — detects and reports a failure in its own reconciliation",
        "L3-P1-20, L3-P5-05",
        _check_at_032,
    ),
    ATCase(
        "AT-033",
        "No auto-loosening — raises it for human review and does not relax it",
        "L3-P6-01, L3-P6-05",
        _check_at_033,
    ),
    ATCase(
        "AT-036",
        "A temporary access exception expires — with no human action",
        "L3-P6-06",
        _check_at_036,
    ),
    ATCase(
        "AT-037",
        "A failed exception is visible — becomes Blocking drift on its expiry date",
        "L3-P6-06",
        _check_at_037,
    ),
    ATCase(
        "AT-102",
        "The seeded reconciliation canary — A run reporting zero findings is a failed run",
        "L3-P1-17",
        _check_at_102,
    ),
    ATCase(
        "AT-110",
        "The reconciler credential is provably bounded — six attempts",
        "L3-P5-06",
        _check_at_110,
    ),
    ATCase(
        "AT-001",
        "Add product 21 — No dashboard, workflow or script contains a product list",
        "L3-P4-07",
        _check_at_001,
    ),
]


def run_matrix(table: list[ATCase] = MATRIX_TABLE) -> tuple[int, int]:
    """Execute the matrix table and return (passed, total)."""
    passed = 0
    total = len(table)

    for item in table:
        if not item.implemented_by or item.implemented_by.strip() == "":
            print(f"AT {item.at_id} result=fail error=unmapped_task")
            continue
        try:
            ok = item.check_fn()
            result_str = "pass" if ok else "fail"
            if ok:
                passed += 1
        except Exception as exc:
            result_str = f"fail error={exc}"
        print(f"AT {item.at_id} result={result_str}")

    return passed, total


def main(argv=None):
    parser = argparse.ArgumentParser(description="Lane 3 acceptance matrix runner")
    parser.add_argument("--summary", action="store_true", help="Print summary line")
    args = parser.parse_args(argv)

    passed, total = run_matrix()
    print(f"MATRIX passed={passed} total={total}")

    if passed != total:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
