#!/usr/bin/env python3
"""
Schema-change checklist generator — L1-705
Entry point: python -m validators.registry.tools.schema_change
Usage: python -m validators.registry.tools.schema_change --kind <kind> --from <n> --to <n>
Exit codes: 0 = checklist emitted, 2 = usage error (unknown --kind, --to != --from+1, non-positive value)

Emits the Section 60.2 nine-step schema-migration checklist on stdout and exits.
Writes nothing, ever: Section 60.2 step 2 ("do not replace") is a human, reviewed
act, and a tool that scaffolds the new schema file would make that invariant
unverifiable. See test_writes_no_files.
"""
from __future__ import annotations

import argparse
import sys

from validators.registry.versioning import VERSION_FIELD


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m validators.registry.tools.schema_change",
        description="Emit the Section 60.2 nine-step schema-change checklist.",
    )
    p.add_argument(
        "--kind",
        required=True,
        choices=sorted(VERSION_FIELD),
        help="Registry/schema kind undergoing the change (Lane 1 kinds only)",
    )
    p.add_argument("--from", dest="from_version", required=True, type=int, help="Current version")
    p.add_argument("--to", dest="to_version", required=True, type=int, help="Target version")
    return p


def checklist(from_version: int, to_version: int) -> list[str]:
    """Return the nine §60.2 steps in order, as plain strings (no trailing newline)."""
    return [
        "1. Schema change proposed",
        f"2. Write the v{to_version} schema alongside v{from_version} - do not replace",
        f"3. Validator supports BOTH v{from_version} and v{to_version}",
        "4. Write the migration - automated where possible",
        "5. Canary products migrate first",
        "6. Verify",
        "7. Fleet migrates gradually, each product on its own schedule",
        f"8. v{from_version} deprecation deadline set and published",
        f"9. v{from_version} support removed only after every product has migrated",
    ]


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.from_version <= 0 or args.to_version <= 0:
        parser.error("--from and --to must be positive integers")

    if args.to_version != args.from_version + 1:
        parser.error(
            f"--to must equal --from + 1 (got --from {args.from_version} --to {args.to_version})"
        )

    for line in checklist(args.from_version, args.to_version):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
