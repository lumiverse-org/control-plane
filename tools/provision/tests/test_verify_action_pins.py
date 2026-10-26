"""Unit tests for tools/verify-action-pins.sh (CP-0105, Invariant #85)."""

from __future__ import annotations

import pathlib
import subprocess
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VERIFY_ACTION_PINS_SCRIPT = REPO_ROOT / "tools" / "verify-action-pins.sh"


_IS_WSL = None


def _check_is_wsl() -> bool:
    global _IS_WSL
    if _IS_WSL is None:
        try:
            res = subprocess.run(["bash", "-c", "uname -s"], capture_output=True, text=True, timeout=10)
            _IS_WSL = "Linux" in res.stdout
        except Exception:
            _IS_WSL = False
    return _IS_WSL


def to_bash_path(path: pathlib.Path) -> str:
    """Convert path for bash execution (works in Git Bash and WSL)."""
    p = path.resolve().as_posix()
    if len(p) >= 2 and p[1] == ":":
        if _check_is_wsl():
            return f"/mnt/{p[0].lower()}{p[2:]}"
        else:
            return f"/{p[0].lower()}{p[2:]}"
    return p


def test_verify_action_pins_valid_sha(tmp_path: pathlib.Path):
    """Passes when all third-party actions use 40-character commit SHAs."""
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    wf_file = wf_dir / "ci.yml"
    wf_file.write_text(
        """name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
      - uses: actions/setup-node@60edb5dd545a775178f52524783378180af0d1f8 # v4.0.2
      - run: npm test
""",
        encoding="utf-8",
    )

    bash_dir = to_bash_path(tmp_path)
    script_path = to_bash_path(VERIFY_ACTION_PINS_SCRIPT)
    cmd = ["bash", script_path, "--local-dir", bash_dir, "--require-sha"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "VERIFY-ACTION-PINS OK" in proc.stdout
    assert "2 third-party action(s)" in proc.stdout


def test_verify_action_pins_detects_unpinned_action(tmp_path: pathlib.Path):
    """Fails and reports violation when an action is pinned to tag or branch instead of SHA."""
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    wf_file = wf_dir / "build.yml"
    wf_file.write_text(
        """name: Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make build
""",
        encoding="utf-8",
    )

    bash_dir = to_bash_path(tmp_path)
    script_path = to_bash_path(VERIFY_ACTION_PINS_SCRIPT)
    cmd = ["bash", script_path, "--local-dir", bash_dir, "--require-sha"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "VERIFY-ACTION-PINS FAIL" in proc.stderr
    assert "actions/checkout@v4" in proc.stderr
    assert "invariant #85" in proc.stderr


def test_verify_action_pins_ignores_local_and_reusable_workflows(tmp_path: pathlib.Path):
    """Local actions (./.github/actions/foo) and reusable workflows (e.g. org/repo/.github/workflows/...)
    are not third-party actions subject to the 40-char SHA pin rule of Invariant #85."""
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    wf_file = wf_dir / "deploy.yml"
    wf_file.write_text(
        """name: Deploy
on: [push]
jobs:
  call-wf:
    uses: lumiverse-org/control-plane/.github/workflows/deploy.yml@workflows/v1
  local-act:
    runs-on: ubuntu-latest
    steps:
      - uses: ./.github/actions/my-action
      - uses: docker://alpine:latest
""",
        encoding="utf-8",
    )

    bash_dir = to_bash_path(tmp_path)
    script_path = to_bash_path(VERIFY_ACTION_PINS_SCRIPT)
    cmd = ["bash", script_path, "--local-dir", bash_dir, "--require-sha"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "VERIFY-ACTION-PINS OK" in proc.stdout
    assert "0 third-party action(s)" in proc.stdout
