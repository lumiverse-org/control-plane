#!/usr/bin/env python3
"""
tools.evidence.check_required_contexts
L2-T534: Required-context <-> job cross-check (§33.2, §53.1; L2-05-tasks.md §0.5)

Reads the required-checks.yaml registry and resolves each context:
  phase_4/5/6: must be emitted by a caller job in the --templates tree
  always:      must be emitted by a job in .github/workflows/

Fails on:
  - A registry context emitted by no job in its resolving tree
  - A job emitting a registry context that carries an if: or sits in a
    workflow with a path filter (PATH_FILTER_ON_REQUIRED_CONTEXT)

NOTE (known, intentional gap): the spec prose for L2-T534 names a third
failure condition -- "a caller job in the --templates tree that calls a
control-plane reusable workflow which emits a registry context, but whose
own job name is not in the registry (L2-T303-309 templates are exempt)".
No fixture, acceptance command, or published reusable-workflow-to-context
mapping exists anywhere in this repo to implement it without guessing.
Not implemented here by design; flag to L0 if a future task needs it.

Exit codes per §0.4: 0=OK, 2=FAIL, 3=ERROR
"""
from __future__ import annotations

import argparse
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required", file=sys.stderr)
    print("ERROR check_required_contexts checked=0 failed=0")
    sys.exit(3)

TOOL_ID = "check_required_contexts"

PATH_FILTER_RE = re.compile(r'^\s+paths(-ignore)?:', re.MULTILINE)


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def load_registry(path: str) -> dict[str, str]:
    """Return {context_name: group_name} from a required-checks.yaml-shaped file.

    Supports both the real file's `contexts:`-wrapped shape and the flat
    shape used by this tool's own test fixtures (no wrapper).
    """
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: not a YAML mapping")
    groups = data.get("contexts", data)
    contexts: dict[str, str] = {}
    if isinstance(groups, dict):
        for group, names in groups.items():
            if isinstance(names, list):
                for name in names:
                    contexts[str(name).strip()] = group
    return contexts


def get_job_names_from_dir(directory: str) -> set[str]:
    """Return a set of job names defined in .yml files under directory."""
    job_names: set[str] = set()
    if not os.path.isdir(directory):
        return job_names
    for fname in os.listdir(directory):
        if not (fname.endswith('.yml') or fname.endswith('.yaml')):
            continue
        fpath = os.path.join(directory, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                raw = f.read()
            clean = re.sub(r'\{\{[A-Z_]+\}\}', 'placeholder', raw)
            wf = yaml.safe_load(clean)
            if isinstance(wf, dict):
                jobs = wf.get('jobs', {}) or {}
                for jname, jdef in jobs.items():
                    if isinstance(jdef, dict):
                        job_names.add(jname)
        except Exception:
            pass
    return job_names


def get_jobs_with_if_or_filter(directory: str) -> set[str]:
    """Return set of job names that carry if: or live in a file with a path filter."""
    bad_jobs: set[str] = set()
    if not os.path.isdir(directory):
        return bad_jobs
    for fname in os.listdir(directory):
        if not (fname.endswith('.yml') or fname.endswith('.yaml')):
            continue
        fpath = os.path.join(directory, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                raw = f.read()
            clean = re.sub(r'\{\{[A-Z_]+\}\}', 'placeholder', raw)
            wf = yaml.safe_load(clean)
            has_path_filter = bool(PATH_FILTER_RE.search(raw))
            if isinstance(wf, dict):
                jobs = wf.get('jobs', {}) or {}
                for jname, jdef in jobs.items():
                    if isinstance(jdef, dict):
                        if 'if' in jdef or has_path_filter:
                            bad_jobs.add(jname)
        except Exception:
            pass
    return bad_jobs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cross-check required-checks.yaml contexts against emitting jobs"
    )
    parser.add_argument("--templates", required=True, help="templates/workflows directory")
    parser.add_argument("--registry", required=True, help="required-checks.yaml path")
    parser.add_argument("--summary", action="store_true", help="Print §0.4 summary line to stdout")
    args = parser.parse_args()

    try:
        contexts = load_registry(args.registry)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR reading registry: {exc}", file=sys.stderr)
        if args.summary:
            _summary("ERROR", 0, 0)
        sys.exit(3)

    checked = len(contexts)
    failed = 0

    template_jobs = get_job_names_from_dir(args.templates)
    template_bad = get_jobs_with_if_or_filter(args.templates)

    gha_workflows = os.path.normpath(
        os.path.join(os.path.dirname(args.templates), "..", ".github", "workflows")
    )
    gha_jobs = get_job_names_from_dir(gha_workflows)
    gha_bad = get_jobs_with_if_or_filter(gha_workflows)

    for ctx_name, group in contexts.items():
        if group == "always":
            jobs, bad, tree = gha_jobs, gha_bad, ".github/workflows/"
        else:
            jobs, bad, tree = template_jobs, template_bad, "templates/"

        if ctx_name not in jobs:
            failed += 1
            print(
                f"FAIL: context '{ctx_name}' ({group}) not emitted by any job in {tree}",
                file=sys.stderr,
            )
        elif ctx_name in bad:
            failed += 1
            print(
                f"FAIL: context '{ctx_name}' ({group}) job carries if: or path filter "
                "[PATH_FILTER_ON_REQUIRED_CONTEXT]",
                file=sys.stderr,
            )

    status = "FAIL" if failed > 0 else "OK"
    code = 2 if failed > 0 else 0

    if args.summary:
        _summary(status, checked, failed)
    sys.exit(code)


if __name__ == "__main__":
    main()
