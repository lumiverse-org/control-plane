#!/usr/bin/env python3
"""Extract a step's shell body, or the Python heredoc inside it, from a workflow.

Used only by tools/evidence/test/phase3/run-all.sh. Extraction rather than
duplication is deliberate: a copy of a gate body in a test drifts from the gate
silently, and a drifted negative test proves nothing.
"""
from __future__ import annotations

import argparse
import sys

import yaml


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow")
    ap.add_argument("job")
    ap.add_argument("step_name")
    ap.add_argument(
        "--python",
        action="store_true",
        help="emit the PYEOF heredoc body instead of the shell body",
    )
    args = ap.parse_args()

    with open(args.workflow, "r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)

    steps = doc["jobs"][args.job]["steps"]
    body = None
    for s in steps:
        if str(s.get("name", "")).strip() == args.step_name:
            body = s.get("run")
            break
    if body is None:
        print("EXTRACT_STEP_NOT_FOUND", file=sys.stderr)
        return 2

    if args.python:
        lines = body.splitlines()
        try:
            start = next(
                i
                for i, ln in enumerate(lines)
                if "<<'PYEOF'" in ln or "<<PYEOF" in ln or "<< 'PYEOF'" in ln
            )
            end = next(
                i
                for i, ln in enumerate(lines)
                if ln.strip() == "PYEOF" and i > start
            )
        except StopIteration:
            print("EXTRACT_HEREDOC_NOT_FOUND", file=sys.stderr)
            return 2
        body = "\n".join(lines[start + 1 : end])

    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
