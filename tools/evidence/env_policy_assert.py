"""Deployment-environment ref policy.

Admits refs/heads/<default> when the policy names the default branch and does
not admit every ref. Refuses a feature branch, an unprotected tag, an absent
policy, and a policy whose custom list is '*'.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOL_ID = "env_policy_assert"


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def evaluate(case: dict) -> tuple[str, int]:
    ref = str(case.get("ref") or "")
    policy = case.get("policy")
    if not isinstance(policy, dict) or not policy:
        return "ENV_POLICY_ABSENT", 2
    custom = policy.get("custom") or []
    if "*" in custom:
        return "ENV_POLICY_TOO_WIDE", 2
    if policy.get("default_branch") is True and ref == "refs/heads/main":
        return "", 0
    return "ENV_POLICY_REF_NOT_ADMITTED", 2


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Refuse a production environment on a non-admitted ref.")
    parser.add_argument("--case", required=True)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    path = Path(args.case)
    if not path.is_file():
        print("ENV_POLICY_ABSENT", file=sys.stderr)
        if args.summary:
            _summary("ERROR", 0, 0)
        sys.exit(3)
    try:
        case = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if args.summary:
            _summary("ERROR", 0, 0)
        sys.exit(3)
    if not isinstance(case, dict):
        print("ENV_POLICY_ABSENT", file=sys.stderr)
        if args.summary:
            _summary("ERROR", 0, 0)
        sys.exit(3)
    token, code = evaluate(case)
    if token:
        print(token, file=sys.stderr)
    if args.summary:
        _summary("OK" if code == 0 else "FAIL", 1, 0 if code == 0 else 1)
    sys.exit(code)


if __name__ == "__main__":
    main()
