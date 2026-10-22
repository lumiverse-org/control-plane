#!/usr/bin/env python3
"""
tools.evidence.assert_run_conclusions
L2-T535: Run-conclusion assertor -- no `skipped`, no `neutral` (§33.2 L2854-2869)

Reads a GitHub check-runs JSON document and the required-checks registry.
Fails when any registry context is skipped, neutral, cancelled, any other
non-success conclusion, or absent from the run -- "no work was needed is an
explicit recorded success, never a skip" (§33.2). A skipped or neutral
conclusion on a required context of a merged pull request is Blocking drift
(§53).

NEVER add a mode that treats `skipped` as satisfied, whatever a downstream
workflow appears to need (this task's own STOP rule, L2-05-tasks.md L2-T535).

checked=: count of registry contexts examined
failed=:  count of contexts in a forbidden state

Exit codes per §0.4: 0=OK, 2=FAIL, 3=ERROR
"""
from __future__ import annotations

import argparse
import json
import sys

import yaml

TOOL_ID = "assert_run_conclusions"
FORBIDDEN_CONCLUSIONS = {"skipped", "neutral", "cancelled"}


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def load_registry(path: str) -> list[str]:
    """Flatten every group of the required-checks registry (phase_4/5/6/
    always) into one list of context names, in the order PyYAML yields
    them. Group membership is not otherwise significant to this tool --
    unlike check_required_contexts.py, this tool does not resolve contexts
    against different trees per group; it only asserts their conclusion."""
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    contexts = []
    groups = data.get("contexts", data) if isinstance(data, dict) else {}
    for _group, names in (groups or {}).items():
        if isinstance(names, list):
            for name in names:
                contexts.append(str(name).strip())
    return contexts


def load_check_runs(path: str) -> dict[str, str]:
    """Return {context_name: lowercased conclusion} from a GitHub
    check-runs JSON document. Accepts a bare list of run objects (the
    shape every fixture in this tree uses) or the GitHub REST
    `{"check_runs": [...]}` envelope. A run with no recorded conclusion
    (still in progress) maps to the empty string, which is non-success."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    runs = data if isinstance(data, list) else (data.get("check_runs", []) or [])
    results = {}
    for run in runs:
        name = run.get("name", "")
        conclusion = (run.get("conclusion") or "").lower()
        results[name] = conclusion
    return results


def check(checks_path: str, registry_path: str) -> tuple[int, int]:
    """Returns (checked, failed). Exits 3 (after printing the ERROR
    summary line) if either input cannot be read or parsed -- there is no
    'assume pass' branch (§0.4 fail-closed rule)."""
    try:
        contexts = load_registry(registry_path)
    except Exception as exc:  # noqa: BLE001 -- any read/parse failure is ERROR
        print(f"ERROR reading registry: {exc}", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    try:
        runs = load_check_runs(checks_path)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR reading checks JSON: {exc}", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    checked = len(contexts)
    failed = 0

    for ctx in contexts:
        conclusion = runs.get(ctx)
        if conclusion is None:
            failed += 1
            print(f"FAIL: context '{ctx}' is absent from check runs", file=sys.stderr)
        elif conclusion in FORBIDDEN_CONCLUSIONS:
            failed += 1
            print(f"FAIL: context '{ctx}' has forbidden conclusion '{conclusion}'", file=sys.stderr)
        elif conclusion != "success":
            failed += 1
            print(f"FAIL: context '{ctx}' has non-success conclusion '{conclusion}'", file=sys.stderr)

    return checked, failed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assert no skipped/neutral/cancelled/absent conclusion on any registry context (§33.2)"
    )
    parser.add_argument("--checks", required=True, help="GitHub check-runs JSON file")
    parser.add_argument("--registry", required=True, help="required-checks.yaml (or a fixture registry of the same shape)")
    parser.add_argument("--summary", action="store_true", help="Print §0.4 summary line to stdout")
    args = parser.parse_args()

    checked, failed = check(args.checks, args.registry)

    if failed == 0:
        if args.summary:
            _summary("OK", checked, 0)
        sys.exit(0)
    else:
        if args.summary:
            _summary("FAIL", checked, failed)
        sys.exit(2)


if __name__ == "__main__":
    main()
