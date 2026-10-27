"""Runner tier for a privileged workflow.

A github-hosted runner is admitted. A self-hosted runner is admitted only when
both the privileged marker and the ephemeral marker are set. An empty
environment fails closed. Tokens are the three named by the NT-05 cases.
"""
from __future__ import annotations

import argparse
import os
import sys

TOOL_ID = "assert_runner_tier"


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def evaluate(environment: str, privileged: str, ephemeral: str) -> tuple[str, int]:
    """Return (stderr token or '', exit code)."""
    env = (environment or "").strip()
    if not env:
        return "RUNNER_TIER_UNRESOLVED", 2
    if env == "github-hosted":
        return "", 0
    if env != "self-hosted":
        return "RUNNER_TIER_UNRESOLVED", 2
    if not (privileged or "").strip():
        return "RUNNER_TIER_SHARED_POOL", 2
    if not (ephemeral or "").strip():
        return "RUNNER_TIER_NOT_EPHEMERAL", 2
    return "", 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Assert the runner tier of a privileged workflow.")
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    if not str(args.workflow).strip():
        print("RUNNER_TIER_UNRESOLVED", file=sys.stderr)
        if args.summary:
            _summary("ERROR", 0, 0)
        sys.exit(3)
    token, code = evaluate(
        os.environ.get("RUNNER_ENVIRONMENT", ""),
        os.environ.get("PRIVILEGED_RUNNER_MARKER", ""),
        os.environ.get("EPHEMERAL_RUNNER_MARKER", ""),
    )
    if token:
        print(token, file=sys.stderr)
    if args.summary:
        _summary("OK" if code == 0 else "FAIL", 1, 0 if code == 0 else 1)
    sys.exit(code)


if __name__ == "__main__":
    main()
