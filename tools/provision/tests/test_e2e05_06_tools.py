"""Unit tests for E2E-05 and E2E-06 tools."""

from __future__ import annotations

import json
import types
from importlib.machinery import SourceFileLoader
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_tool(rel_path: str):
    path = REPO_ROOT / rel_path
    loader = SourceFileLoader(path.name.replace("-", "_"), str(path))
    mod = types.ModuleType(loader.name)
    mod.__file__ = str(path)
    loader.exec_module(mod)
    return mod


open_pr = _load_tool("tools/e2e-drive/open-pr")
check_conclusions = _load_tool("tools/evidence/check-conclusions")
check_job = _load_tool("tools/evidence/check-job")
approve_pr = _load_tool("tools/e2e-drive/approve-pr")
merge_pr = _load_tool("tools/e2e-drive/merge-pr")
wait_workflow = _load_tool("tools/e2e-drive/wait-workflow")
read_digest = _load_tool("tools/evidence/read-digest")
check_sbom = _load_tool("tools/evidence/check-sbom")
attempt_tag_overwrite = _load_tool("tools/e2e-drive/attempt-tag-overwrite")


def test_open_pr_parser():
    parser = open_pr.build_parser()
    args = parser.parse_args([
        "--repo", "lumiverse-org/pilot-one-api",
        "--as", "dev-a",
        "--branch", "pilot/test-branch",
        "--fixture", "e2e/fixtures/pilot-one/change",
    ])
    assert args.repo == "lumiverse-org/pilot-one-api"
    assert args.author == "dev-a"
    assert args.branch == "pilot/test-branch"


def test_check_conclusions_parser():
    parser = check_conclusions.build_parser()
    args = parser.parse_args([
        "--pr", "12",
        "--required-from", "templates/protection/service.json",
        "--forbid", "skipped,neutral",
    ])
    assert args.pr == "12"
    assert args.forbid == "skipped,neutral"


def test_check_job_parser():
    parser = check_job.build_parser()
    args = parser.parse_args([
        "--pr", "12",
        "--job", "unit",
        "--expect", "success",
    ])
    assert args.pr == "12"
    assert args.job == "unit"
    assert args.expect == "success"


def test_approve_pr_parser():
    parser = approve_pr.build_parser()
    args = parser.parse_args([
        "--pr", "12",
        "--as", "dev-b",
    ])
    assert args.pr == "12"
    assert args.reviewer == "dev-b"


def test_merge_pr_parser():
    parser = merge_pr.build_parser()
    args = parser.parse_args([
        "--pr", "12",
    ])
    assert args.pr == "12"
    assert args.squash is True


def test_wait_workflow_parser():
    parser = wait_workflow.build_parser()
    args = parser.parse_args([
        "--repo", "lumiverse-org/pilot-one-api",
        "--workflow", "build.yml",
        "--sha", "abcdef123456",
        "--expect", "success",
    ])
    assert args.repo == "lumiverse-org/pilot-one-api"
    assert args.sha == "abcdef123456"


def test_read_digest_parser():
    parser = read_digest.build_parser()
    args = parser.parse_args([
        "--repo", "lumiverse-org/pilot-one-api",
        "--sha", "abcdef123456",
    ])
    assert args.repo == "lumiverse-org/pilot-one-api"
    assert args.sha == "abcdef123456"


def test_check_sbom_valid(tmp_path: Path):
    digest = "sha256:" + "a" * 64
    sbom_file = tmp_path / "sbom.spdx.json"
    sbom_file.write_text(json.dumps({
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "pilot-one-api",
    }), encoding="utf-8")

    code = check_sbom.main([
        "--digest", digest,
        "--file", str(sbom_file),
    ])
    assert code == 0


def test_check_sbom_malformed_digest():
    code = check_sbom.main([
        "--digest", "bad-digest",
    ])
    assert code == 1


def test_attempt_tag_overwrite_refusal():
    # CP-0605 requires that attempt-tag-overwrite fails and prints refusal
    digest = "sha256:" + "b" * 64
    code = attempt_tag_overwrite.main([
        "--registry", "ghcr.io/lumiverse-org/pilot-one-api",
        "--digest", digest,
    ])
    assert code == 1
