"""Unit tests for tools/verify-surface-enumeration.sh (CP-0108, Section 19.1, AT-001)."""

from __future__ import annotations

import pathlib
import subprocess
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VERIFY_SURFACE_SCRIPT = REPO_ROOT / "tools" / "verify-surface-enumeration.sh"
SURFACES_YAML = REPO_ROOT / "tools" / "provision" / "surfaces.yaml"
FIXTURE_PRODUCT_YAML = REPO_ROOT / "e2e" / "fixtures" / "pilot-one" / "product.yaml"

_IS_WSL = None


def _check_is_wsl() -> bool:
    global _IS_WSL
    if _IS_WSL is None:
        try:
            res = subprocess.run(["bash", "-c", "uname -s"], capture_output=True, text=True, timeout=2)
            _IS_WSL = "Linux" in res.stdout
        except Exception:
            _IS_WSL = False
    return _IS_WSL


def to_bash_path(path: pathlib.Path) -> str:
    p = path.resolve().as_posix()
    if len(p) >= 2 and p[1] == ":":
        if _check_is_wsl():
            return f"/mnt/{p[0].lower()}{p[2:]}"
        else:
            return f"/{p[0].lower()}{p[2:]}"
    return p


@pytest.mark.parametrize(
    "surface",
    [
        "portfolio-board",
        "grafana",
        "scorecard",
        "devlake",
        "reviewer-matrix",
        "dependency-graph",
    ],
)
def test_surface_offline_unreachable(surface: str):
    """Without live infrastructure, all 6 surfaces honestly exit 3 and report UNREACHABLE (AT-001)."""
    script_path = to_bash_path(VERIFY_SURFACE_SCRIPT)
    surfaces_path = to_bash_path(SURFACES_YAML)
    cmd = [
        "bash",
        script_path,
        "--surface",
        surface,
        "--product",
        "pilot-one",
        "--surfaces-file",
        surfaces_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 3, f"Expected exit code 3, got {proc.returncode}. STDOUT: {proc.stdout}"
    assert f"SURFACE {surface} UNREACHABLE" in proc.stdout


def test_surface_mock_reachable_with_fixture():
    """Passes when mock reachable is enabled and product is present in fixture registry."""
    script_path = to_bash_path(VERIFY_SURFACE_SCRIPT)
    surfaces_path = to_bash_path(SURFACES_YAML)
    fixture_path = to_bash_path(FIXTURE_PRODUCT_YAML)
    cmd = [
        "bash",
        script_path,
        "--surface",
        "portfolio-board",
        "--product",
        "pilot-one",
        "--surfaces-file",
        surfaces_path,
        "--fixture-registry",
        fixture_path,
        "--mock-reachable",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "SURFACE portfolio-board OK" in proc.stdout


def test_surface_mock_reachable_missing_product():
    """Fails when mock reachable is enabled but product is missing from fixture registry."""
    script_path = to_bash_path(VERIFY_SURFACE_SCRIPT)
    surfaces_path = to_bash_path(SURFACES_YAML)
    fixture_path = to_bash_path(FIXTURE_PRODUCT_YAML)
    cmd = [
        "bash",
        script_path,
        "--surface",
        "portfolio-board",
        "--product",
        "non-existent-product",
        "--surfaces-file",
        surfaces_path,
        "--fixture-registry",
        fixture_path,
        "--mock-reachable",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "FAIL: product 'non-existent-product' not found in registry" in proc.stderr or "FAIL" in proc.stdout


def test_unknown_surface_rejection():
    """Rejects unknown surface names with exit 2."""
    script_path = to_bash_path(VERIFY_SURFACE_SCRIPT)
    cmd = [
        "bash",
        script_path,
        "--surface",
        "not-a-surface",
        "--product",
        "pilot-one",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 2
    assert "Unknown surface 'not-a-surface'" in proc.stderr
