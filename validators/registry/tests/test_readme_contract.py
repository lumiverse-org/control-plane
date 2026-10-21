"""Tests for validators/registry/README.md (L1-903), the one published interface
Lane 2 is allowed to call (PARTITION rule 4).

Checks the README's prose against the live Option B validators/registry/cli.py
(FD-094, DECIDED, _FOUNDER_DECISIONS.md) directly -- subprocess `--help` and real
runs against task-local fixtures -- rather than against a `report` module.
`validators/registry/report.py` does not exist in this repository and must not be
built for this task: the "OK: <n> file(s) validated" success line, the four-exit-code
table (0/1/2/3) and the `--today` flag it would imply all belonged to the pre-FD-094
design, superseded before it was ever built -- the same adaptation already made by
test_owners_manifest.py, test_framework_rules.py, test_exceptions_minimal.py and
test_r_prd_11.py in this same directory.

Two function names below (`test_success_line_matches_report_module`,
`test_failure_line_matches_report_module`) are kept from L1-903's own task table in
lanes/L1-05-tasks.md even though no `report` module exists; only their bodies are
adapted to check cli.py directly.

6 test functions, matching the task's own six-row table exactly.
"""
import json
import os
import re
import subprocess
import sys

TESTS_DIR = os.path.dirname(__file__)
REGISTRY_DIR = os.path.join(TESTS_DIR, "..")
REPO_ROOT = os.path.join(TESTS_DIR, "..", "..", "..")
README_PATH = os.path.join(REGISTRY_DIR, "README.md")
FIXTURES_DIR = os.path.join(REGISTRY_DIR, "fixtures", "readme_contract")
PASS_FIXTURE = os.path.join(FIXTURES_DIR, "pass")
FAIL_FIXTURE = os.path.join(FIXTURES_DIR, "fail")

ALLOWED_PREFIXES = (
    "schemas/registry/",
    "schemas/product/",
    "registries/",
    "validators/registry/",
)


def _readme_text():
    with open(README_PATH, encoding="utf-8") as f:
        return f.read()


def _run_cli(*args):
    cmd = [sys.executable, "-m", "validators.registry.cli"] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)


def _help_flags():
    result = _run_cli("--help")
    return set(re.findall(r"--[a-z][a-z-]*", result.stdout))


def test_documents_all_four_exit_codes():
    text = _readme_text()
    for code in ("exit 0", "exit 1", "exit 2", "exit 3"):
        assert code in text, f"README must document {code!r}"


def test_success_line_matches_report_module():
    result = _run_cli(
        "--root", PASS_FIXTURE, "--as-of", "2026-09-09",
        "--format", "json", "--rule", "R01",
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == {"status": "PASS", "rules_run": 1, "findings": []}

    text = _readme_text()
    assert '"status": "PASS" | "FAIL"' in text
    assert "rules_run" in text and "findings" in text


def test_failure_line_matches_report_module():
    result = _run_cli(
        "--root", FAIL_FIXTURE, "--as-of", "2026-09-09",
        "--format", "json", "--rule", "R01",
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == {
        "status": "FAIL",
        "rules_run": 1,
        "findings": ["R01: duplicate id 'fixture-readme-dup' in bob.yaml and alice.yaml"],
    }

    text = _readme_text()
    assert "R01:" in text


def test_lists_every_flag_of_the_frozen_grammar():
    text = _readme_text()
    frozen_flags = _help_flags() - {"--help"}
    assert frozen_flags, "no flags discovered from --help; is cli.py broken?"
    for flag in sorted(frozen_flags):
        assert flag in text, f"README omits {flag}"


def test_claims_no_flag_the_cli_lacks():
    text = _readme_text()
    accepted = _help_flags()
    m = re.search(r"^python -m validators\.registry\.cli.*$", text, re.MULTILINE)
    assert m, "README must show the literal invocation line"
    claimed = set(re.findall(r"--[a-z][a-z-]*", m.group(0)))
    assert claimed, "invocation line names no flags"
    assert claimed <= accepted, (
        "README's invocation line claims flags the CLI does not accept: "
        f"{sorted(claimed - accepted)}"
    )


def test_names_no_path_outside_the_owned_trees():
    text = _readme_text()
    for span in re.findall(r"`([a-z0-9_.\-]+(?:/[a-z0-9_.\-]+)+)`", text):
        assert span.startswith(ALLOWED_PREFIXES), f"README names an out-of-tree path: {span}"
