"""
L2-T542  Workflow-identity gate: approver ≠ deployer
§27.2 L2567-2576 — The deploy workflow itself verifies that the recorded
approving identity differs from the deploying identity and fails closed
if it cannot tell.
D73: environment required reviewers are Enterprise-only and never the
mechanism of record.

DoD-04: emits literal APPROVER_EQUALS_DEPLOYER on the equality case.

If it cannot tell — approval record absent, approver field empty, or
identity does not resolve — it fails, exit 3, never exit 0.

Exit codes:
  0  OK    checked=1 failed=0
  2  FAIL  checked=1 failed=1
  3  ERROR checked=0 failed=0
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from tools.evidence import STATUS_OK, STATUS_FAIL, STATUS_ERROR, EXIT_OK, EXIT_FAIL, EXIT_ERROR

TOOL_ID = "identity_gate"


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def _load_approval(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"approval record not found: {path}")
    if yaml is None:
        raise ImportError("pyyaml is required")
    with open(p) as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError("approval record must be a YAML mapping")
    return data


def evaluate(approval: dict, deployer: str) -> tuple[int, int]:
    """Return (checked=1, failed=0|1). Fails closed on any inability to tell."""
    approver = approval.get("approver")
    if not approver:
        raise ValueError("approval record has no resolvable approver field — fail-closed")

    if approver == deployer:
        print(f"APPROVER_EQUALS_DEPLOYER: approver={approver!r} deployer={deployer!r}",
              file=sys.stderr)
        return 1, 1

    return 1, 0


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Workflow-identity gate: approver ≠ deployer.")
    ap.add_argument("--approval", required=True, help="Path to approval record YAML")
    ap.add_argument("--deployer", required=True, help="Deploying actor login")
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args(argv)

    try:
        approval = _load_approval(args.approval)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if args.summary:
            _summary(STATUS_ERROR, 0, 0)
        sys.exit(EXIT_ERROR)

    try:
        checked, failed = evaluate(approval, args.deployer)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if args.summary:
            _summary(STATUS_ERROR, 0, 0)
        sys.exit(EXIT_ERROR)

    if args.summary:
        _summary(STATUS_OK if failed == 0 else STATUS_FAIL, checked, failed)

    sys.exit(EXIT_OK if failed == 0 else EXIT_FAIL)


if __name__ == "__main__":
    main()
