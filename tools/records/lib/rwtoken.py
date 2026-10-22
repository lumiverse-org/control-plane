#!/usr/bin/env python3
"""tools/records/lib/rwtoken.py
Records-writer token adapter for every writer (spec §97.1 line 8841, §40.1 line 3665;
L4-06-tasks.md row L4-P4-10).

Every writer obtains its credential through rwtoken and never through a literal token.
A writer invoked with no token available exits 3 (ERROR / fail-closed), not 0.
"""
import os
import pathlib
import sys
from typing import Optional


class CredentialUnavailableError(RuntimeError):
    """Raised when no records-writer credential is available."""
    pass


def get_token(
    secrets_dir: Optional[pathlib.Path] = None,
    allow_env: bool = True
) -> str:
    """Obtain the records-writer token from environment or secrets file.
    Raises CredentialUnavailableError if not found.
    """
    # 1. Environment variables
    if allow_env:
        for env_var in ("RW_TOKEN", "RECORDS_WRITER_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
            val = os.environ.get(env_var, "").strip()
            if val:
                return val

    # 2. File in secrets_dir or standard locations
    candidate_paths = []
    if secrets_dir:
        candidate_paths.append(pathlib.Path(secrets_dir) / "records-writer.token")
        candidate_paths.append(pathlib.Path(secrets_dir) / "rw-token")
    
    env_secrets = os.environ.get("SECRETS_DIR")
    if env_secrets:
        candidate_paths.append(pathlib.Path(env_secrets) / "records-writer.token")
        candidate_paths.append(pathlib.Path(env_secrets) / "rw-token")

    for cp in candidate_paths:
        if cp.is_file():
            tok = cp.read_text(encoding="utf-8").strip()
            if tok:
                return tok

    raise CredentialUnavailableError("RWTOKEN ERROR: no credential available (exit 3 fail-closed)")


def main(argv=None):
    try:
        token = get_token()
        print("RWTOKEN OK")
        return 0
    except CredentialUnavailableError as exc:
        print(f"{exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
