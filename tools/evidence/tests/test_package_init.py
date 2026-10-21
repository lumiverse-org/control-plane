"""Unit tests for L2-T530: tools.evidence package skeleton."""
from __future__ import annotations

import tools.evidence as e


def test_tool_contract_grammar_string():
    assert e.TOOL_CONTRACT == "<STATUS> <tool-id> checked=<int> failed=<int>"


def test_status_constants():
    assert (e.STATUS_OK, e.STATUS_FAIL, e.STATUS_ERROR) == ("OK", "FAIL", "ERROR")


def test_exit_code_constants():
    assert (e.EXIT_OK, e.EXIT_FAIL, e.EXIT_ERROR) == (0, 2, 3)


def test_no_tools_init_namespace_marker():
    """Section 0.1: tools/ itself must stay an implicit namespace package."""
    import pathlib

    repo_root = pathlib.Path(__file__).resolve().parents[3]
    assert not (repo_root / "tools" / "__init__.py").exists()
