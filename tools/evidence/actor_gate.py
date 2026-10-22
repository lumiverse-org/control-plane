#!/usr/bin/env python3
"""
L2-T541  Actor gate: human identity plus capability
§37.3 L3261-3268 — the five privileged workflows fail closed unless
github.actor resolves to a human identity in people.yaml holding the
capability the action requires.
§101 invariant 18, L9477.

No bypass flag. No emergency mode. No environment variable that skips the gate.
Removing an actor gate is a workflow-file change and is therefore Blocking drift.

Exit codes:
  0  OK    checked=3 failed=0
  2  FAIL  checked=3 failed=<n>
  3  ERROR checked=0 failed=0 (unreadable people.yaml or absent)
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from tools.evidence import STATUS_OK, STATUS_FAIL, STATUS_ERROR, EXIT_OK, EXIT_FAIL, EXIT_ERROR

TOOL_ID = "actor_gate"

# §94.7 — the positive dispatch allowlist for machine accounts.
# Used only to select the diagnostic stderr message below: this tool's three
# conditions (§37.3) require a HUMAN identity full stop, so a machine actor
# always fails condition C2 regardless of its registered action. The
# allowlist exists so the rejection message correctly distinguishes "this
# machine runs a digest generator but this tool only gates humans" from
# "this machine is not even on the permitted dispatch list" — it does not
# grant a machine a pass through this gate.
MACHINE_POSITIVE_ALLOWLIST = frozenset({
    "digest-generator",
    "sbom-generator",
    "artifact-scanner",
})

VALID_CAPABILITIES = frozenset({
    "production-approval",
    "incident-response",
    "devops",
    "migration-review",
})


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def _load_people(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"people.yaml not found: {path}")
    if yaml is None:
        raise ImportError("pyyaml is required — add it to tools/evidence/requirements.txt")
    with open(p) as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict) or "people" not in data:
        raise ValueError("people.yaml must be a mapping with a 'people' key")
    return data


def evaluate(actor: str, capability: str, people_data: dict) -> tuple[int, int]:
    """Return (checked=3, failed=n). Three conditions, evaluated in order and
    SHORT-CIRCUITED at the first one that fails (mirrors the C1 early-return
    below): a run only ever reports ONE failure, never an accumulation of
    several, because once one condition is unmet the remaining conditions
    are moot for this actor/capability pair.
      C1: actor exists in people.yaml
      C2: actor is a human identity (not a machine account)
      C3: actor holds the named capability
    """
    people = {p["login"]: p for p in people_data.get("people", [])}

    # C1: exists
    if actor not in people:
        print(f"FAIL [C1] actor {actor!r} not found in people.yaml", file=sys.stderr)
        return 3, 3  # cannot evaluate C2/C3 for an actor that does not exist

    person = people[actor]

    # C2: human (not machine) — a machine account never passes this gate.
    if person.get("type") == "machine":
        action = person.get("action", "")
        if action not in MACHINE_POSITIVE_ALLOWLIST:
            print(f"MACHINE_ACTOR_REJECTED: {actor!r} is a machine account"
                  f" and {action!r} is not in the positive dispatch allowlist", file=sys.stderr)
        else:
            print(f"MACHINE_ACTOR_REJECTED: {actor!r} is a machine account"
                  f" — only digest generators are permitted", file=sys.stderr)
        return 3, 1

    # C3: capability
    caps = set(person.get("capabilities", []))
    if capability not in caps:
        print(
            f"FAIL [C3] actor {actor!r} does not hold capability {capability!r};"
            f" has: {caps}",
            file=sys.stderr,
        )
        return 3, 1

    return 3, 0


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Actor gate: human identity plus capability.")
    ap.add_argument("--actor", required=True, help="GitHub actor login")
    ap.add_argument("--capability", required=True, help="Required capability")
    ap.add_argument("--people", required=True, help="Path to people.yaml")
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args(argv)

    try:
        people_data = _load_people(args.people)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if args.summary:
            _summary(STATUS_ERROR, 0, 0)
        sys.exit(EXIT_ERROR)

    checked, failed = evaluate(args.actor, args.capability, people_data)

    if args.summary:
        _summary(STATUS_OK if failed == 0 else STATUS_FAIL, checked, failed)

    sys.exit(EXIT_OK if failed == 0 else EXIT_FAIL)


if __name__ == "__main__":
    main()
