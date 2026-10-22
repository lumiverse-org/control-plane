#!/usr/bin/env python3
"""
tools.evidence.delta_gate
L2-T536: Delta-gate engine (§33.2 L2854-2869; §48.2 L4309-4316)

Reads a baseline findings JSON and a current findings JSON. Computes the set
difference by finding identity. Fails only on findings present in current and
absent from baseline — a legacy backlog never blocks a merge, but a new
finding always does.

A missing or unreadable baseline is ERROR, exit 3. An absent baseline never
means "everything is new" and never means "nothing is new" (§0.4 fail-closed
rule, invariant 80).

Exit codes per §0.4: 0=OK, 2=FAIL, 3=ERROR
"""
from __future__ import annotations

import argparse
import json
import os
import sys

TOOL_ID = "delta_gate"


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def load_findings(path: str) -> list[dict]:
    """Load a findings JSON file: a bare list, or {"findings": [...]}."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, list):
        return data
    return data.get("findings", [])


def finding_identity(f: dict) -> str:
    """Canonical identity of a finding for the set-difference computation."""
    if "id" in f:
        return str(f["id"])
    return "|".join([
        str(f.get("rule", "")),
        str(f.get("location", "")),
        str(f.get("package", "")),
    ])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delta-gate: fail only on findings new since baseline (§33.2, §48.2)"
    )
    parser.add_argument("--baseline", required=True, help="Path to baseline findings JSON")
    parser.add_argument("--current", required=True, help="Path to current findings JSON")
    parser.add_argument("--summary", action="store_true", help="Print summary line per §0.4")
    args = parser.parse_args()

    if not os.path.isfile(args.baseline):
        print(f"ERROR: baseline not found: {args.baseline}", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    try:
        baseline_findings = load_findings(args.baseline)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot parse baseline: {exc}", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    if not os.path.isfile(args.current):
        print(f"ERROR: current not found: {args.current}", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    try:
        current_findings = load_findings(args.current)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot parse current: {exc}", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    baseline_ids = {finding_identity(f) for f in baseline_findings}
    current_ids = [finding_identity(f) for f in current_findings]

    checked = len(current_findings)
    new_ids = [fid for fid in current_ids if fid not in baseline_ids]
    failed = len(new_ids)

    if failed > 0:
        for fid in new_ids:
            print(f"FAIL: new finding: {fid}", file=sys.stderr)
        _summary("FAIL", checked, failed)
        sys.exit(2)

    _summary("OK", checked, 0)
    sys.exit(0)


if __name__ == "__main__":
    main()
