"""Unit tests proving caller-callee input concordance between
templates/workflows/ci.yml and .github/workflows/ci.yml (MasterSpec §33.2, L2-T301)."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATES_CI = REPO_ROOT / "templates" / "workflows" / "ci.yml"
REUSABLE_CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"
REUSABLE_BUILD = REPO_ROOT / ".github" / "workflows" / "build.yml"


def _load_yaml_with_placeholders(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    clean = re.sub(r"\{\{[A-Za-z0-9_]+\}\}", "placeholder", raw)
    return yaml.safe_load(clean)


def _get_on_block(data: dict) -> dict:
    """Handle PyYAML 1.1 quirk where unquoted `on:` parses as boolean True."""
    on_block = data.get("on")
    if on_block is None:
        on_block = data.get(True, {})
    return on_block if isinstance(on_block, dict) else {}


def test_ci_template_inputs_declared_in_reusable_ci():
    template_data = _load_yaml_with_placeholders(TEMPLATES_CI)
    reusable_data = _load_yaml_with_placeholders(REUSABLE_CI)

    declared_inputs = _get_on_block(reusable_data).get("workflow_call", {}).get("inputs", {})
    assert "job" in declared_inputs, "job input missing from .github/workflows/ci.yml"
    assert "conformance_profile" in declared_inputs, "conformance_profile input missing from .github/workflows/ci.yml"
    assert "product_name" in declared_inputs, "product_name input missing from .github/workflows/ci.yml"

    for job_name, job_def in template_data.get("jobs", {}).items():
        with_inputs = job_def.get("with", {})
        for input_name in with_inputs:
            assert input_name in declared_inputs, (
                f"Job '{job_name}' passes input '{input_name}' which is NOT declared in "
                f".github/workflows/ci.yml on.workflow_call.inputs"
            )


def test_ci_caller_jobs_match_reusable_ci_jobs():
    template_data = _load_yaml_with_placeholders(TEMPLATES_CI)
    reusable_data = _load_yaml_with_placeholders(REUSABLE_CI)

    template_jobs = set(template_data.get("jobs", {}).keys())
    reusable_jobs = set(reusable_data.get("jobs", {}).keys())

    expected_contexts = {
        "unit-tests",
        "integration-tests",
        "build",
        "security-scan",
        "licence-scan",
        "slopsquat-check",
        "contract-validation",
        "registry-validation",
        "parity-check",
        "verification-contract",
        "seeded-defect-case",
    }

    assert expected_contexts.issubset(template_jobs), f"Template missing contexts: {expected_contexts - template_jobs}"
    assert expected_contexts.issubset(reusable_jobs), f"Reusable ci.yml missing contexts: {expected_contexts - reusable_jobs}"


def test_build_workflow_declares_job_input():
    build_data = _load_yaml_with_placeholders(REUSABLE_BUILD)
    declared_inputs = _get_on_block(build_data).get("workflow_call", {}).get("inputs", {})
    assert "job" in declared_inputs, "job input missing from .github/workflows/build.yml"


def test_no_required_job_carries_top_level_if():
    reusable_data = _load_yaml_with_placeholders(REUSABLE_CI)
    for job_name, job_def in reusable_data.get("jobs", {}).items():
        assert "if" not in job_def, f"Job '{job_name}' in .github/workflows/ci.yml carries top-level if: (LW-02 violation)"

    build_data = _load_yaml_with_placeholders(REUSABLE_BUILD)
    for job_name, job_def in build_data.get("jobs", {}).items():
        assert "if" not in job_def, f"Job '{job_name}' in .github/workflows/build.yml carries top-level if:"


def test_lint_workflow_passes_on_both_files():
    for rel_path in [".github/workflows/ci.yml", ".github/workflows/build.yml"]:
        cmd = [sys.executable, "-m", "tools.evidence.lint_workflow", "--path", rel_path, "--summary"]
        proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        assert proc.returncode == 0, f"lint_workflow failed on {rel_path}: {proc.stderr}"
        assert "failed=0" in proc.stdout, f"lint_workflow reported failures on {rel_path}: {proc.stdout}"
