"""tools/evidence/check_action_pins.py
Validates that every GitHub Action SHA referenced in workflows appears in action-pins.txt.
Spec: §48.1 L4300–4308; Invariant 85 L9565; L2-T532.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys

ACTION_USES_PATTERN = re.compile(r"uses:\s+([a-zA-Z0-9._/-]+)@([0-9a-f]{40})")
LEDGER_ROW_PATTERN = re.compile(r"^([a-zA-Z0-9._/-]+)\s+(v[0-9.]+)\s+([0-9a-f]{40})$")


def get_referenced_actions(repo_root: Path) -> set[tuple[str, str]]:
    """Scan all workflows for referenced third-party action+sha pairs."""
    referenced = set()
    dirs = [repo_root / ".github" / "workflows", repo_root / "templates" / "workflows"]
    for d in dirs:
        if not d.is_dir():
            continue
        for p in d.rglob("*"):
            if p.suffix in (".yml", ".yaml") and p.is_file():
                content = p.read_text(encoding="utf-8", errors="ignore")
                for m in ACTION_USES_PATTERN.finditer(content):
                    action, sha = m.group(1), m.group(2)
                    # Ignore internal reusable workflows (e.g. ./.github/workflows/...)
                    if not action.startswith((".", "/")):
                        referenced.add((action, sha))
    return referenced


def get_ledger_pins(ledger_path: Path) -> set[tuple[str, str]]:
    """Read action-pins.txt and extract (action, sha) pairs."""
    pins = set()
    if not ledger_path.is_file():
        return pins
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = LEDGER_ROW_PATTERN.match(line)
        if m:
            action, tag, sha = m.group(1), m.group(2), m.group(3)
            pins.add((action, sha))
    return pins


def check_pins(repo_root: Path | None = None, ledger_path: Path | None = None) -> tuple[bool, int, list[tuple[str, str]]]:
    root = repo_root or Path.cwd()
    ledger_file = ledger_path or (root / "tools" / "evidence" / "action-pins.txt")
    referenced = get_referenced_actions(root)
    ledger = get_ledger_pins(ledger_file)
    missing = sorted(referenced - ledger)
    ok = len(missing) == 0
    return ok, len(referenced), missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify action pin ledger coverage")
    parser.add_argument("--summary", action="store_true", help="Print §0.4 summary line")
    parser.add_argument("--ledger", type=Path, default=None, help="Path to action-pins.txt ledger")
    args = parser.parse_args(argv)

    ok, total, missing = check_pins(ledger_path=args.ledger)
    if not ok:
        print(f"FAIL check_action_pins covered={total - len(missing)} missing={len(missing)}", file=sys.stderr)
        for act, sha in missing:
            print(f"  unledgered action: {act}@{sha}", file=sys.stderr)
        if args.summary:
            print(f"FAIL check_action_pins checked={total} failed={len(missing)}")
        return 2

    if args.summary:
        print(f"OK check_action_pins checked={total} failed=0")
    else:
        print(f"ACTION-PINS OK: all {total} action-sha pairs covered in ledger")
    return 0


if __name__ == "__main__":
    sys.exit(main())
