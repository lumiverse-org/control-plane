"""
assert_actor_gate_first — posture assertion that the actor gate is step 0
of every privileged workflow (spec §37.3 L3261-3268; DoD-05; invariant 18).

Usage:
  python -m tools.evidence.assert_actor_gate_first --path .github/workflows [--rollback-workflow rollback.yml] [--summary]

Exit codes per §0.4:
  0 = OK   (all five workflows present, gate at step 0)
  2 = FAIL (one or more workflows missing gate at step 0, or workflow absent)
  3 = ERROR (cannot determine — manifest unreadable, rollback name unknown)
"""

import argparse
import sys
import os
import yaml
from pathlib import Path

import tools.evidence as e

# The four named privileged workflows whose filenames are fixed.
FIXED_PRIVILEGED = [
    "deploy-staging.yml",
    "deploy-production.yml",
    "migrate.yml",
    "restore-test.yml",
]
MANIFEST_PATH = "templates/workflows/MANIFEST.yaml"
ACTOR_GATE_MARKERS = ["actor_gate", "assert_actor_gate", "ACTOR_GATE", "actor-gate"]


def _resolve_rollback_name(workflow_dir: Path, rollback_arg: str | None) -> str | None:
    """Read rollback filename from MANIFEST.yaml or --rollback-workflow arg."""
    if rollback_arg:
        return rollback_arg
    manifest = Path(MANIFEST_PATH)
    if manifest.exists():
        try:
            data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
            if "rollback_workflow" in data:
                return data["rollback_workflow"]
            for row in data.get("templates", []):
                if "rollback" in row.get("template", "").lower():
                    dest = row.get("destination", "")
                    if dest:
                        return Path(dest).name
                    return row["template"]
        except Exception as exc:
            print(f"WARN: cannot parse {MANIFEST_PATH}: {exc}", file=sys.stderr)
    return None


def _first_step_invokes_gate(workflow_path: Path) -> bool:
    """Return True if the entry job's first step references the actor gate."""
    try:
        data = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: cannot parse {workflow_path}: {exc}", file=sys.stderr)
        return False
    jobs = data.get("jobs", {})
    if not jobs:
        return False
    # Entry job is the first declared job.
    first_job = next(iter(jobs.values()))
    steps = first_job.get("steps", [])
    if not steps:
        # Reusable workflow caller job (e.g. jobs.actor-gate.uses: .../actor-gate.yml)
        uses = str(first_job.get("uses", ""))
        name = str(first_job.get("name", ""))
        return any(marker in uses or marker in name for marker in ACTOR_GATE_MARKERS)
    first_step = steps[0]
    # Check run: or uses: or name: for any actor gate marker.
    step_text = str(first_step.get("run", "")) + str(first_step.get("uses", "")) + str(first_step.get("name", ""))
    return any(marker in step_text for marker in ACTOR_GATE_MARKERS)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="Directory containing workflow files")
    parser.add_argument("--rollback-workflow", default=None,
                        help="Filename (basename) of the rollback workflow; falls back to MANIFEST.yaml")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    wf_dir = Path(args.path)
    if not wf_dir.is_dir():
        if args.summary:
            print(f"{e.STATUS_ERROR} assert_actor_gate_first checked=0 failed=0")
        sys.exit(e.EXIT_ERROR)

    rollback_name = _resolve_rollback_name(wf_dir, args.rollback_workflow)
    if rollback_name is None:
        print("ERROR: rollback workflow name unknown — pass --rollback-workflow or wait for L2-T311", file=sys.stderr)
        if args.summary:
            print(f"{e.STATUS_ERROR} assert_actor_gate_first checked=0 failed=0")
        sys.exit(e.EXIT_ERROR)

    privileged = FIXED_PRIVILEGED + [rollback_name]
    checked = len(privileged)  # always 5
    failed = 0

    for name in privileged:
        wf_path = wf_dir / name
        if not wf_path.exists():
            print(f"FAIL: privileged workflow missing: {name}", file=sys.stderr)
            failed += 1
            continue
        if not _first_step_invokes_gate(wf_path):
            print(f"FAIL: actor gate is not step 0 in {name}", file=sys.stderr)
            failed += 1

    status = e.STATUS_OK if failed == 0 else e.STATUS_FAIL
    exit_code = e.EXIT_OK if failed == 0 else e.EXIT_FAIL
    if args.summary:
        print(f"{status} assert_actor_gate_first checked={checked} failed={failed}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
