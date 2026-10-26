"""Unit tests for tools/e2e-drive/compat-probe (CP-0702 / CCR-007)."""

from __future__ import annotations

import types
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_tool(rel_path: str):
    path = REPO_ROOT / rel_path
    loader = SourceFileLoader(path.name.replace("-", "_"), str(path))
    mod = types.ModuleType(loader.name)
    mod.__file__ = str(path)
    loader.exec_module(mod)
    return mod


compat_probe = _load_tool("tools/e2e-drive/compat-probe")

VALID_DIGEST = "sha256:" + "a" * 64


def test_no_predecessor_empty_digest(capsys):
    rc = compat_probe.main(["--digest", ""])
    captured = capsys.readouterr()
    assert rc == 0
    assert "COMPAT-PROBE EXEMPT (PASS/SKIP)" in captured.out
    assert "No predecessor release exists" in captured.out


def test_no_predecessor_explicit_none_digest(capsys):
    for val in ["none", "<none>", "absent", "null", "no-predecessor"]:
        rc = compat_probe.main(["--digest", val])
        captured = capsys.readouterr()
        assert rc == 0
        assert "COMPAT-PROBE EXEMPT (PASS/SKIP)" in captured.out


def test_no_predecessor_flag(capsys):
    rc = compat_probe.main(["--no-predecessor"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "COMPAT-PROBE EXEMPT (PASS/SKIP)" in captured.out


def test_no_predecessor_missing_file(tmp_path, capsys):
    missing_file = tmp_path / "prev-digest"
    rc = compat_probe.main(["--prev-digest-file", str(missing_file)])
    captured = capsys.readouterr()
    assert rc == 0
    assert "COMPAT-PROBE EXEMPT (PASS/SKIP)" in captured.out


def test_no_predecessor_file_with_none_or_empty(tmp_path, capsys):
    empty_file = tmp_path / "empty-prev-digest"
    empty_file.write_text("none\n", encoding="utf-8")
    rc = compat_probe.main(["--prev-digest-file", str(empty_file)])
    captured = capsys.readouterr()
    assert rc == 0
    assert "COMPAT-PROBE EXEMPT (PASS/SKIP)" in captured.out


def test_predecessor_invalid_digest_fails_closed(capsys):
    for bad_digest in ["malformed-digest", "sha256:tooshort", "cat: /path: No such file"]:
        rc = compat_probe.main(["--digest", bad_digest])
        captured = capsys.readouterr()
        assert rc == 1
        assert "COMPAT-PROBE FAIL" in captured.err
        assert "invalid" in captured.err


def test_predecessor_compatible_pass(capsys):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        rc = compat_probe.main([
            "--digest", VALID_DIGEST,
            "--endpoint", "http://127.0.0.1:8080/health",
        ])
        captured = capsys.readouterr()
        assert rc == 0
        assert "COMPAT-PROBE PASS" in captured.out
        assert "verified compatible" in captured.out


def test_predecessor_incompatible_endpoint_error_fails_closed(capsys):
    mock_resp = MagicMock()
    mock_resp.status = 500
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        rc = compat_probe.main([
            "--digest", VALID_DIGEST,
            "--endpoint", "http://127.0.0.1:8080/health",
        ])
        captured = capsys.readouterr()
        assert rc == 1
        assert "COMPAT-PROBE FAIL" in captured.err
        assert "returned status 500" in captured.err


def test_predecessor_incompatible_connection_refused_fails_closed(capsys):
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
        rc = compat_probe.main([
            "--digest", VALID_DIGEST,
            "--endpoint", "http://127.0.0.1:8080/health",
        ])
        captured = capsys.readouterr()
        assert rc == 1
        assert "COMPAT-PROBE FAIL" in captured.err
        assert "unreachable or incompatible" in captured.err
