"""Unit tests for tools/records/lib/mint_token.py.
Covers RS256 JWT creation, PEM path resolution, token exchange, and error handling.
"""
import io
import json
import os
import pathlib
import sys
import time
import urllib.error
from unittest import mock

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.records.lib import mint_token


@pytest.fixture(scope="session")
def test_rsa_pem():
    """Generate a valid RSA 2048 private key for testing."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def test_create_jwt_valid(test_rsa_pem):
    """Verify JWT creation produces valid RS256 token with expected claims."""
    jwt_tok = mint_token.create_jwt(test_rsa_pem, app_id="5422825", lifetime_seconds=300)
    parts = jwt_tok.split(".")
    assert len(parts) == 3

    # Decode payload
    import base64
    payload_raw = base64.urlsafe_b64decode(parts[1] + "==")
    claims = json.loads(payload_raw.decode("utf-8"))
    assert claims["iss"] == "5422825"
    assert claims["exp"] > claims["iat"]


def test_resolve_pem_path_cli(tmp_path):
    pem = tmp_path / "custom.pem"
    resolved = mint_token.resolve_pem_path(str(pem))
    assert resolved == pem


def test_resolve_pem_path_rw_pem(tmp_path, monkeypatch):
    pem = tmp_path / "from_env.pem"
    monkeypatch.setenv("RW_PEM", str(pem))
    monkeypatch.delenv("SECRETS_DIR", raising=False)
    assert mint_token.resolve_pem_path() == pem


def test_resolve_pem_path_secrets_dir(tmp_path, monkeypatch):
    monkeypatch.delenv("RW_PEM", raising=False)
    monkeypatch.setenv("SECRETS_DIR", str(tmp_path))
    assert mint_token.resolve_pem_path() == tmp_path / "records-writer.pem"


def test_resolve_pem_path_missing(monkeypatch):
    monkeypatch.delenv("RW_PEM", raising=False)
    monkeypatch.delenv("SECRETS_DIR", raising=False)
    with pytest.raises(RuntimeError, match="Private key path not specified"):
        mint_token.resolve_pem_path()


def test_mint_token_missing_file(tmp_path):
    missing_key = tmp_path / "nonexistent.pem"
    with pytest.raises(FileNotFoundError):
        mint_token.mint_installation_token(pem_path=missing_key)


def test_exchange_jwt_for_token_success():
    fake_response = json.dumps({"token": "ghs_mocked_token_xyz"}).encode("utf-8")
    mock_resp = mock.MagicMock()
    mock_resp.read.return_value = fake_response
    mock_resp.__enter__.return_value = mock_resp

    with mock.patch("urllib.request.urlopen", return_value=mock_resp):
        token = mint_token.exchange_jwt_for_token("fake.jwt.token", "174038206")
        assert token == "ghs_mocked_token_xyz"


def test_exchange_jwt_for_token_http_error():
    err_body = json.dumps({"message": "Bad credentials"}).encode("utf-8")
    http_err = urllib.error.HTTPError(
        url="https://api.github.com/app/installations/123/access_tokens",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=io.BytesIO(err_body),
    )
    with mock.patch("urllib.request.urlopen", side_effect=http_err):
        with pytest.raises(RuntimeError, match="GitHub API error 401.*Bad credentials"):
            mint_token.exchange_jwt_for_token("fake.jwt.token", "123")


def test_main_cli_success_and_cache(tmp_path, test_rsa_pem, capsys):
    pem_path = tmp_path / "key.pem"
    pem_path.write_bytes(test_rsa_pem)
    cache_path = tmp_path / "cached_token"

    fake_response = json.dumps({"token": "ghs_cli_test_token"}).encode("utf-8")
    mock_resp = mock.MagicMock()
    mock_resp.read.return_value = fake_response
    mock_resp.__enter__.return_value = mock_resp

    with mock.patch("urllib.request.urlopen", return_value=mock_resp):
        exit_code = mint_token.main(["--pem", str(pem_path), "--cache-to", str(cache_path)])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "ghs_cli_test_token"
        assert cache_path.read_text(encoding="utf-8").strip() == "ghs_cli_test_token"


def test_main_cli_missing_pem(tmp_path, capsys):
    missing_key = tmp_path / "absent.pem"
    exit_code = mint_token.main(["--pem", str(missing_key)])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "Error:" in captured.err
