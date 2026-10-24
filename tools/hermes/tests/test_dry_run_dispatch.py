"""Unit tests for offline Hermes dry-run dispatch harness (tools/hermes/dry_run_dispatch.py)."""

import importlib.util
import os
import sys
import pytest

_MOD_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "access", "ai-toolchain", "validate_task_whitelist.py")
)
if os.path.isfile(_MOD_PATH):
    _spec = importlib.util.spec_from_file_location("validate_task_whitelist", _MOD_PATH)
    if _spec and _spec.loader:
        _mod = importlib.util.module_from_spec(_spec)
        sys.modules["validate_task_whitelist"] = _mod
        _spec.loader.exec_module(_mod)
        PERMITTED_TASK_CLASSES = _mod.PERMITTED_TASK_CLASSES
else:
    PERMITTED_TASK_CLASSES = set()

from tools.hermes.dry_run_dispatch import create_draft_dispatch_proposal


def test_all_whitelisted_classes_produce_valid_proposal():
    for tc in PERMITTED_TASK_CLASSES:
        argv = create_draft_dispatch_proposal(
            task_class=tc,
            target_repo="lumiverse-org/Product-1",
            draft_title=f"Draft proposal for {tc}",
            draft_body="Automated draft body generated for human review",
            manual_invoke=True,
            dispatch_type="pr",
        )
        assert isinstance(argv, list)
        assert argv[0] == "gh"
        assert argv[1] == "pr"
        assert argv[2] == "create"
        assert "--draft" in argv
        assert "--repo" in argv
        assert "lumiverse-org/Product-1" in argv
        assert f"Draft proposal for {tc}" in argv


def test_non_whitelisted_class_is_rejected_pre_construction():
    disallowed = "deploy-to-production-automated"
    with pytest.raises(ValueError) as excinfo:
        create_draft_dispatch_proposal(
            task_class=disallowed,
            target_repo="lumiverse-org/Product-1",
            draft_title="Unapproved proposal",
            draft_body="Body",
            manual_invoke=True,
        )
    assert "not in the permitted Section 37.2 whitelist" in str(excinfo.value)


def test_cron_mode_deny_refuses_without_manual_invoke(tmp_path):
    cage_cfg = tmp_path / "cage.yaml"
    cage_cfg.write_text("approvals:\n  cron_mode: deny\n", encoding="utf-8")

    with pytest.raises(PermissionError) as excinfo:
        create_draft_dispatch_proposal(
            task_class="Documentation and docstrings",
            target_repo="lumiverse-org/Product-1",
            draft_title="Docs update",
            draft_body="Body",
            cage_config_path=str(cage_cfg),
            manual_invoke=False,
        )
    assert "cron_mode == 'deny'" in str(excinfo.value)
    assert "Unattended dispatch is prohibited" in str(excinfo.value)


def test_cron_mode_deny_succeeds_with_manual_invoke(tmp_path):
    cage_cfg = tmp_path / "cage.yaml"
    cage_cfg.write_text("approvals:\n  cron_mode: deny\n", encoding="utf-8")

    argv = create_draft_dispatch_proposal(
        task_class="Documentation and docstrings",
        target_repo="lumiverse-org/Product-1",
        draft_title="Docs update",
        draft_body="Body",
        cage_config_path=str(cage_cfg),
        manual_invoke=True,
    )
    assert argv[0] == "gh"
    assert "--draft" in argv


def test_workflow_dispatch_type():
    argv = create_draft_dispatch_proposal(
        task_class="Lint, format and type fixes",
        target_repo="lumiverse-org/Product-2",
        draft_title="Fix formatting",
        draft_body="Body",
        manual_invoke=True,
        dispatch_type="workflow",
    )
    assert argv[:4] == ["gh", "workflow", "run", "proposal.yml"]
    assert "--repo" in argv
    assert "lumiverse-org/Product-2" in argv


def test_source_code_has_no_execution_or_disk_writes():
    src_path = os.path.join(os.path.dirname(__file__), "..", "dry_run_dispatch.py")
    with open(src_path, "r", encoding="utf-8") as f:
        src = f.read()

    # Must never import subprocess, socket, urllib, or requests
    assert "import subprocess" not in src
    assert "from subprocess" not in src
    assert "import socket" not in src
    assert "import urllib" not in src
    assert "import requests" not in src

    # Must never perform write calls to disks or directories
    assert "open(" in src  # reads only
    assert '"w"' not in src
    assert '"a"' not in src
    assert "os.remove" not in src
    assert "os.unlink" not in src
    assert "shutil" not in src
