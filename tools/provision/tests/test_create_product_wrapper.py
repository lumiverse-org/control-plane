"""Unit tests for tools/provision/create-product wrapper (CP-0101)."""

from __future__ import annotations

import pathlib
import subprocess
import sys
import types
from importlib.machinery import SourceFileLoader
import pytest
import yaml

from tools.provision.executors import get_executor

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CREATE_PRODUCT_SCRIPT = REPO_ROOT / "tools" / "provision" / "create-product"
CONTRACT_FIXTURE = REPO_ROOT / "e2e" / "fixtures" / "pilot-one" / "product.yaml"


def _load_create_product_module():
    loader = SourceFileLoader("create_product_bin", str(CREATE_PRODUCT_SCRIPT))
    mod = types.ModuleType(loader.name)
    mod.__file__ = str(CREATE_PRODUCT_SCRIPT)
    loader.exec_module(mod)
    return mod


def test_create_product_wrapper_happy_path():
    """Wrapper translates spec flags and outputs the 13 automated + 2 manual steps plan."""
    cmd = [
        sys.executable,
        str(CREATE_PRODUCT_SCRIPT),
        "--id",
        "pilot-one",
        "--contract",
        str(CONTRACT_FIXTURE),
        "--template",
        "product-template",
        "--executor",
        "devops-1",
    ]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "PLAN create-product steps=13 writes=0 manual=2" in proc.stdout
    assert "1. [write] repo_from_template:" in proc.stdout
    assert "13. [write] register_dependency_graph:" in proc.stdout
    assert "14. [manual] alert_channel:" in proc.stdout
    assert "15. [manual] support_intake_mailbox:" in proc.stdout

    # Test executor provenance is recorded when invoked in Python
    mod = _load_create_product_module()
    res = mod.main([
        "--id",
        "pilot-one",
        "--contract",
        str(CONTRACT_FIXTURE),
        "--template",
        "product-template",
        "--executor",
        "devops-1",
    ])
    assert res == 0
    assert get_executor("pilot-one") == "devops-1"


def test_create_product_wrapper_rejects_wrong_template():
    """Wrapper errors loudly if template is not 'product-template'."""
    cmd = [
        sys.executable,
        str(CREATE_PRODUCT_SCRIPT),
        "--id",
        "pilot-one",
        "--contract",
        str(CONTRACT_FIXTURE),
        "--template",
        "some-other-template",
        "--executor",
        "devops-1",
    ]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "invalid template 'some-other-template'" in proc.stderr


def test_create_product_wrapper_rejects_missing_contract(tmp_path: pathlib.Path):
    """Wrapper errors loudly if contract file does not exist."""
    missing = tmp_path / "does-not-exist.yaml"
    cmd = [
        sys.executable,
        str(CREATE_PRODUCT_SCRIPT),
        "--id",
        "pilot-one",
        "--contract",
        str(missing),
        "--template",
        "product-template",
        "--executor",
        "devops-1",
    ]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "contract file not found" in proc.stderr


def test_create_product_wrapper_rejects_malformed_contract(tmp_path: pathlib.Path):
    """Wrapper errors loudly if contract file is not valid YAML."""
    bad_contract = tmp_path / "bad.yaml"
    bad_contract.write_text("::: bad yaml content :::", encoding="utf-8")
    cmd = [
        sys.executable,
        str(CREATE_PRODUCT_SCRIPT),
        "--id",
        "pilot-one",
        "--contract",
        str(bad_contract),
        "--template",
        "product-template",
        "--executor",
        "devops-1",
    ]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "failed to parse contract" in proc.stderr
