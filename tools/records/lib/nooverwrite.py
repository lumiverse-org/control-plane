#!/usr/bin/env python3
"""tools/records/lib/nooverwrite.py
No-overwrite guard (invariant 48, spec §101 line 9529; L4-06-tasks.md row L4-P4-02).
Writing to a path that already exists is refused with exit 1 and no file is modified.
"""
import os
import pathlib
import sys
from typing import Union


def assert_not_exists(target_path: Union[str, pathlib.Path]) -> None:
    """Check if target_path exists. Raises FileExistsError if it does."""
    p = pathlib.Path(target_path)
    if p.exists():
        raise FileExistsError(f"overwrite-refused: {target_path}")


def safe_write(
    target_path: Union[str, pathlib.Path],
    content: str,
    encoding: str = "utf-8"
) -> pathlib.Path:
    """Safely write content to target_path, refusing to overwrite an existing file.
    Creates parent directories if necessary.
    Raises FileExistsError if the file already exists.
    """
    p = pathlib.Path(target_path)
    if p.exists():
        raise FileExistsError(f"overwrite-refused: {target_path}")
    p.parent.mkdir(parents=True, exist_ok=True)
    # Write using exclusive creation mode 'x' to prevent race conditions
    with open(p, "x", encoding=encoding) as f:
        f.write(content)
    return p


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print("Usage: python -m tools.records.lib.nooverwrite <path>", file=sys.stderr)
        return 2
    path = argv[0]
    try:
        assert_not_exists(path)
        print(f"NOOVERWRITE OK {path}")
        return 0
    except FileExistsError as exc:
        print(f"NOOVERWRITE REFUSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
