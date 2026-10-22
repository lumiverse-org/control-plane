# File: tools/evidence/lint_workflow.py
# Created by L2-T533
# Usage: python -m tools.evidence.lint_workflow --path <file-or-dir> [--summary]
# Spec: §33.2 L2854-2869; §48.1 L4300-4308
# Prints: OK|FAIL|ERROR lint_workflow checked=<int> failed=<int>
# Exit:   0=OK, 2=FAIL, 3=ERROR

"""
Workflow lint — five rules, fail on any violation.

LW-01: a uses: of a third-party action is not @<40-hex>
LW-02: a job emitting a required context carries an if:
LW-03: the workflow carries paths: or paths-ignore:
LW-04: permissions: is absent, or grants a write scope the workflow does not use
LW-05: a step declares continue-on-error: true on a job emitting a required context
"""

import sys
import os
import re
import argparse
import yaml

# Inline TOOL_CONTRACT to avoid circular import during bootstrap
STATUS_OK, STATUS_FAIL, STATUS_ERROR = "OK", "FAIL", "ERROR"
EXIT_OK, EXIT_FAIL, EXIT_ERROR = 0, 2, 3
TOOL_ID = "lint_workflow"

# Required contexts from required-checks.yaml (§0.5; §33.2)
# These are the caller-job names that must never carry if: or path filters.
REQUIRED_CONTEXTS = {
    "unit-tests", "integration-tests", "build", "security-scan", "licence-scan",
    "slopsquat-check", "contract-validation", "registry-validation", "parity-check",
    "verification-contract", "seeded-defect-case",
    "artifact-digest-recorded", "sbom-emitted",
    "renovate-path-guard", "lane-guard",
}

WRITE_SCOPES = {
    "actions", "checks", "contents", "deployments", "id-token", "issues",
    "packages", "pages", "pull-requests", "repository-projects", "security-events",
    "statuses",
}

SHA_RE = re.compile(r'@[0-9a-f]{40}$')
THIRD_PARTY_EXCLUDE = re.compile(r'^(\.github/workflows/|\./)|(^[^/]+/[^/]+/[^/]+)')


def _is_third_party(uses_val: str) -> bool:
    """True when uses: references a GitHub Action (owner/repo@ref), not a local path."""
    if uses_val.startswith('.github/') or uses_val.startswith('./'):
        return False
    # Reusable workflow in this repo
    if uses_val.startswith('./.github/') or '/.github/workflows/' in uses_val:
        return False
    # Has the form owner/repo or owner/repo/.github/workflows/x.yml
    parts = uses_val.split('@')
    if len(parts) == 2:
        return True
    return False


def lint_file(path: str, violations: list) -> int:
    """Lint one workflow file. Returns number of violations found."""
    found = 0
    try:
        with open(path, 'r', encoding='utf-8') as f:
            raw = f.read()
        # Pre-process template tokens like {{TOKEN}} to avoid PyYAML flow-mapping syntax errors
        clean_raw = re.sub(r'\{\{[A-Za-z0-9_]+\}\}', 'placeholder', raw)
        wf = yaml.safe_load(clean_raw)
    except Exception as e:
        print(f"ERROR reading {path}: {e}", file=sys.stderr)
        violations.append(('ERROR', path, str(e)))
        return -1  # signal ERROR

    if not isinstance(wf, dict):
        return 0

    # A GitHub Actions workflow must have top-level 'on' (or boolean True) and 'jobs' mapping
    has_on = 'on' in wf or True in wf
    has_jobs = 'jobs' in wf and isinstance(wf.get('jobs'), dict)
    if not (has_on and has_jobs):
        return 0  # not a workflow file (e.g. template metadata or fragment)

    # LW-03: no paths: or paths-ignore: at any level
    if re.search(r'^\s+paths(-ignore)?:', raw, re.MULTILINE):
        found += 1
        print(f"LW-03 {path}: contains paths: or paths-ignore: filter", file=sys.stderr)
        violations.append(('LW-03', path, 'path filter present'))

    # LW-04: permissions: absent or grants unused write scope
    top_perms = wf.get('permissions', None)
    if top_perms is None:
        found += 1
        print(f"LW-04 {path}: permissions: block is absent", file=sys.stderr)
        violations.append(('LW-04', path, 'permissions absent'))
    elif isinstance(top_perms, dict):
        for scope, access in top_perms.items():
            if access == 'write' and scope in WRITE_SCOPES:
                # Check if any step references this scope via github.token or GITHUB_TOKEN
                scope_used = scope.replace('-', '_').upper()
                if scope_used not in raw and scope not in raw:
                    found += 1
                    print(f"LW-04 {path}: write scope '{scope}' declared but not referenced", file=sys.stderr)
                    violations.append(('LW-04', path, f'unused write scope: {scope}'))

    jobs = wf.get('jobs', {}) or {}
    for job_name, job_def in jobs.items():
        if not isinstance(job_def, dict):
            continue

        is_required = job_name in REQUIRED_CONTEXTS

        # LW-02: required-context job must not carry if:
        if is_required and 'if' in job_def:
            found += 1
            print(f"LW-02 {path}: job '{job_name}' (required context) carries if:", file=sys.stderr)
            violations.append(('LW-02', path, f"required job '{job_name}' has if:"))

        # Scan steps
        steps = job_def.get('steps', []) or []
        for step in steps:
            if not isinstance(step, dict):
                continue

            # LW-01: third-party uses: must be @<40-hex>
            uses_val = step.get('uses', '')
            if uses_val and _is_third_party(uses_val):
                ref = uses_val.split('@', 1)[-1] if '@' in uses_val else ''
                if not re.match(r'^[0-9a-f]{40}', ref):
                    found += 1
                    print(f"LW-01 {path}: job '{job_name}' step uses '{uses_val}' — not pinned to full SHA", file=sys.stderr)
                    violations.append(('LW-01', path, f"unpinned uses: {uses_val}"))

            # LW-05: continue-on-error: true on a required-context job
            if is_required and step.get('continue-on-error') is True:
                found += 1
                print(f"LW-05 {path}: job '{job_name}' (required context) step has continue-on-error: true", file=sys.stderr)
                violations.append(('LW-05', path, f"required job '{job_name}' has continue-on-error"))

    return found


def main():
    parser = argparse.ArgumentParser(description='Workflow lint — LW-01 through LW-05')
    parser.add_argument('--path', required=True, help='Workflow file or directory')
    parser.add_argument('--summary', action='store_true', help='Print §0.4 summary line to stdout')
    args = parser.parse_args()

    target = args.path
    violations = []
    files = []

    if os.path.isfile(target):
        files = [target]
    elif os.path.isdir(target):
        files = [
            os.path.join(target, f)
            for f in sorted(os.listdir(target))
            if f.endswith('.yml') or f.endswith('.yaml')
        ]
    else:
        if args.summary:
            print(f"{STATUS_ERROR} {TOOL_ID} checked=0 failed=0")
        print(f"ERROR: path does not exist: {target}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    if not files:
        if args.summary:
            print(f"{STATUS_OK} {TOOL_ID} checked=0 failed=0")
        sys.exit(EXIT_OK)

    checked = 0
    failed = 0
    error_reading = False

    for fpath in files:
        result = lint_file(fpath, violations)
        if result == -1:
            error_reading = True
        else:
            checked += 1
            failed += result

    if error_reading and checked == 0:
        if args.summary:
            print(f"{STATUS_ERROR} {TOOL_ID} checked=0 failed=0")
        sys.exit(EXIT_ERROR)

    if failed > 0:
        status = STATUS_FAIL
        code = EXIT_FAIL
    else:
        status = STATUS_OK
        code = EXIT_OK

    if args.summary:
        print(f"{status} {TOOL_ID} checked={checked} failed={failed}")

    sys.exit(code)


if __name__ == '__main__':
    main()
