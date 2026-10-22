"""Unit tests for L4-P4-06: RECORD-VERIFICATION-RESULT handler (tools.records.rvr).
Master Spec v4.0 Section 97.2 line 8871; L4-06-tasks.md row L4-P4-06; FD-131.
"""
from __future__ import annotations

import pathlib
import sys
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.records.rvr import handle_rvr, main


def test_rvr_clean_manual_verification(tmp_path: pathlib.Path):
    rec_id, store, ev_type = handle_rvr(
        product="testprod",
        item="ITEM-101",
        mechanism="manual_verification",
        result="pass",
        evidence_link="https://evidence.invalid/runs/101",
        actor="qa-lead-1",
        cpr_root=str(tmp_path),
        cp_root=REPO_ROOT,
    )
    assert store == "uat"
    assert ev_type == "uat_executed"
    assert (tmp_path / "records" / "uat" / f"{rec_id}.yaml").is_file()

    # Check event was emitted
    events = list((tmp_path / "events").glob("**/*.yaml"))
    assert len(events) == 1


def test_rvr_clean_restore_test_confirmation(tmp_path: pathlib.Path):
    rec_id, store, ev_type = handle_rvr(
        product="testprod",
        item="ITEM-202",
        mechanism="restore_test_confirmation",
        result="fail",
        evidence_link="https://evidence.invalid/runs/202",
        actor="devops-eng-1",
        cpr_root=str(tmp_path),
        cp_root=REPO_ROOT,
    )
    assert store == "restore-tests"
    assert ev_type == "restore_test_executed"
    assert (tmp_path / "records" / "restore-tests" / f"{rec_id}.yaml").is_file()


def test_rvr_seeded_unknown_mechanism(tmp_path: pathlib.Path):
    with pytest.raises(ValueError, match="unknown-mechanism"):
        handle_rvr(
            product="testprod",
            item="ITEM-001",
            mechanism="fake_mechanism",
            result="pass",
            evidence_link="https://example.invalid",
            actor="tester",
            cpr_root=str(tmp_path),
            cp_root=REPO_ROOT,
        )


def test_rvr_seeded_unarmed_mechanism(tmp_path: pathlib.Path):
    # support_loop_closure is unarmed (armed: false)
    with pytest.raises(PermissionError, match="unarmed-mechanism"):
        handle_rvr(
            product="testprod",
            item="ITEM-002",
            mechanism="support_loop_closure",
            result="pass",
            evidence_link="https://example.invalid",
            actor="tester",
            cpr_root=str(tmp_path),
            cp_root=REPO_ROOT,
        )


def test_rvr_seeded_bad_result(tmp_path: pathlib.Path):
    with pytest.raises(ValueError, match="bad-result maybe"):
        handle_rvr(
            product="testprod",
            item="ITEM-003",
            mechanism="manual_verification",
            result="maybe",
            evidence_link="https://example.invalid",
            actor="tester",
            cpr_root=str(tmp_path),
            cp_root=REPO_ROOT,
        )


def test_rvr_seeded_bad_evidence_link(tmp_path: pathlib.Path):
    with pytest.raises(ValueError, match="bad-evidence-link"):
        handle_rvr(
            product="testprod",
            item="ITEM-004",
            mechanism="manual_verification",
            result="pass",
            evidence_link="not-a-url",
            actor="tester",
            cpr_root=str(tmp_path),
            cp_root=REPO_ROOT,
        )


def test_rvr_seeded_empty_input(tmp_path: pathlib.Path):
    with pytest.raises(ValueError, match="empty-input product"):
        handle_rvr(
            product="",
            item="ITEM-005",
            mechanism="manual_verification",
            result="pass",
            evidence_link="https://example.invalid",
            actor="tester",
            cpr_root=str(tmp_path),
            cp_root=REPO_ROOT,
        )


def test_rvr_cli_exit_codes(tmp_path: pathlib.Path):
    # Valid call -> exit 0
    cmd_args = [
        "testprod",
        "ITEM-CLI",
        "manual_verification",
        "pass",
        "https://example.invalid/cli",
        "lead-eng",
        "--cpr-root",
        str(tmp_path),
    ]
    assert main(cmd_args) == 0

    # Wrong arity -> exit 2
    assert main(["testprod", "ITEM-CLI"]) == 2

    # Unarmed mechanism -> exit 3
    cmd_unarmed = [
        "testprod",
        "ITEM-CLI",
        "support_loop_closure",
        "pass",
        "https://example.invalid/cli",
        "lead-eng",
        "--cpr-root",
        str(tmp_path),
    ]
    assert main(cmd_unarmed) == 3
