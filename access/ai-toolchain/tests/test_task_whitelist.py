"""Unit tests for Section 37.2 Hermes task whitelist and validator."""

import importlib.util
import os
import sys
import pytest

_MOD_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "validate_task_whitelist.py")
)
_spec = importlib.util.spec_from_file_location("validate_task_whitelist", _MOD_PATH)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["validate_task_whitelist"] = _mod
_spec.loader.exec_module(_mod)

DEFAULT_WHITELIST_PATH = _mod.DEFAULT_WHITELIST_PATH
PERMITTED_TASK_CLASSES = _mod.PERMITTED_TASK_CLASSES
check = _mod.check
is_whitelisted = _mod.is_whitelisted


def test_whitelist_file_validates_cleanly():
    errors, count = check(DEFAULT_WHITELIST_PATH)
    assert errors == []
    assert count == 9


def test_all_canonical_classes_are_whitelisted():
    for tc in PERMITTED_TASK_CLASSES:
        assert is_whitelisted(tc) is True


def test_disallowed_classes_are_rejected():
    assert is_whitelisted("deploy-to-production") is False
    assert is_whitelisted("approve-pull-request") is False
    assert is_whitelisted("modify-people-registry") is False
    assert is_whitelisted("arbitrary-terminal-execution") is False
    assert is_whitelisted("") is False


def test_check_rejects_missing_class(tmp_path):
    mutated_file = tmp_path / "whitelist_missing.yaml"
    content = """schema_version: 1
spec_reference: "37.2"
tasks:
  - task_class: "Documentation and docstrings"
    spec_reference: "37.2"
"""
    mutated_file.write_text(content, encoding="utf-8")
    errors, count = check(str(mutated_file))
    assert len(errors) > 0
    assert any("expected exactly 9 task classes" in e for e in errors)


def test_check_rejects_unapproved_class(tmp_path):
    mutated_file = tmp_path / "whitelist_extra.yaml"
    items = [f'  - task_class: "{tc}"\n    spec_reference: "37.2"' for tc in list(PERMITTED_TASK_CLASSES)[:8]]
    items.append('  - task_class: "unapproved-backdoor-action"\n    spec_reference: "37.2"')
    content = "schema_version: 1\nspec_reference: \"37.2\"\ntasks:\n" + "\n".join(items)
    mutated_file.write_text(content, encoding="utf-8")
    errors, count = check(str(mutated_file))
    assert len(errors) > 0
    assert any("unapproved task classes" in e for e in errors)
