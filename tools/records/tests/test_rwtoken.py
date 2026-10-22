"""Unit tests for L4-P4-10: records-writer token adapter (tools.records.lib.rwtoken).
Master Spec v4.0 Section 97.1 line 8841, Section 40.1 line 3665; L4-06-tasks.md row L4-P4-10; FD-131.
"""
from __future__ import annotations

import os
import pathlib
import sys
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.records.lib.rwtoken import CredentialUnavailableError, get_token, main


def test_get_token_from_env(monkeypatch):
    monkeypatch.setenv("RW_TOKEN", "secret-token-xyz")
    tok = get_token()
    assert tok == "secret-token-xyz"


def test_get_token_from_file(tmp_path: pathlib.Path, monkeypatch):
    for var in ("RW_TOKEN", "RECORDS_WRITER_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        monkeypatch.delenv(var, raising=False)

    token_file = tmp_path / "records-writer.token"
    token_file.write_text("file-secret-token\n", encoding="utf-8")

    tok = get_token(secrets_dir=tmp_path, allow_env=False)
    assert tok == "file-secret-token"


def test_get_token_seeded_failure_absent(monkeypatch):
    for var in ("RW_TOKEN", "RECORDS_WRITER_TOKEN", "GH_TOKEN", "GITHUB_TOKEN", "SECRETS_DIR"):
        monkeypatch.delenv(var, raising=False)

    # Invariant: absent credential raises CredentialUnavailableError
    with pytest.raises(CredentialUnavailableError):
        get_token(allow_env=True)


def test_rwtoken_cli_fail_closed_exit_3(monkeypatch):
    for var in ("RW_TOKEN", "RECORDS_WRITER_TOKEN", "GH_TOKEN", "GITHUB_TOKEN", "SECRETS_DIR"):
        monkeypatch.delenv(var, raising=False)

    # CLI exits 3 (fail-closed) when token is unavailable
    exit_code = main([])
    assert exit_code == 3
