"""tests/test_provision_sh_safety.py

Unit and regression tests for scripts/provision/provision.sh.

Verifies:
- PROBLEM 1: Command injection via eval is eliminated; commands execute via array "$@"
  so shell metacharacters in arguments (like product names) are never re-evaluated.
- PROBLEM 2: Input validation for --product-id and --repo rejects path traversal
  (e.g., ../x) and shell metacharacters before any file write or command execution.
- PROBLEM 3: Under --mode apply, --org must be passed explicitly on the CLI;
  it cannot be silently inherited from the environment.
- PROBLEM 4: gh repo create receives --private (not --public).
- Mode dry: Dry-run planning remains safe, functional, and unregressed.
"""

from __future__ import annotations

import pathlib
import subprocess
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
TEST_SH = REPO_ROOT / "tests" / "test_provision_sh_safety.sh"

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


def run_safety_test(target: str) -> subprocess.CompletedProcess[str]:
    cmd = ["bash", to_bash_path(TEST_SH), target]
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_problem_1_injection_neutralized():
    """Verify command injection payload is passed as literal argument and not evaluated."""
    res = run_safety_test("1")
    assert res.returncode == 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    assert "PASS: Command injection blocked; INJECTED_PROOF was not created." in res.stdout
    assert "PASS: Injection payload passed as literal description argument to gh." in res.stdout


def test_problem_2_product_id_validation_rejects_malicious_inputs():
    """Verify --product-id is validated against alphanumeric/dash/underscore regex."""
    res = run_safety_test("2")
    assert res.returncode == 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    assert "PASS: All 9 invalid product-id variants rejected with exit code 2." in res.stdout


def test_problem_2_repo_name_validation_rejects_malicious_inputs():
    """Verify --repo is validated against alphanumeric/dash/underscore regex."""
    res = run_safety_test("3")
    assert res.returncode == 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    assert "PASS: All 6 invalid repo variants rejected with exit code 2." in res.stdout


def test_problem_3_apply_requires_explicit_cli_org():
    """Verify --mode apply requires explicit --org on the CLI."""
    res = run_safety_test("4")
    assert res.returncode == 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    assert "PASS: Omission of literal --org under apply rejected with exit code 2." in res.stdout


def test_problem_4_repo_created_private():
    """Verify repository creation uses --private by default (never --public)."""
    res = run_safety_test("5")
    assert res.returncode == 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    assert "PASS: Repository created with --private by default." in res.stdout


def test_dry_run_mode_preserved_and_safe():
    """Verify dry-run planning mode does not write anything and functions cleanly."""
    res = run_safety_test("6")
    assert res.returncode == 0, f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    assert "PASS: Dry-run planning mode completely functional and unregressed." in res.stdout
