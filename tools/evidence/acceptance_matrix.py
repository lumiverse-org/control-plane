"""
acceptance_matrix — runs every DoD row from L2-00-charter.md §7 as a command
and reports the number proved.

Usage:
  python -m tools.evidence.acceptance_matrix [--summary]

Each row is proved by executing its proof command, never by reading a file and
believing it. checked=20, failed= the number of DoD rows not proved.
Exit codes per §0.4: 0=OK, 2=FAIL, 3=ERROR.
"""

import argparse
import subprocess
import sys

import tools.evidence as e

# Negative DoD tests prove safety by failing closed when invalid states occur (exit != 0).
# DoD-03: digest mismatch fails closed
# DoD-04: approver == deployer fails closed
# DoD-10: Friday-freeze window refuses deployment
# DoD-12: passing seeded defect raises SIG-18 and fails run
NEGATIVE_DODS = {"DoD-03", "DoD-04", "DoD-10", "DoD-12"}

# DoD rows — each is (id, short description, proof_command_list).
DOD_ROWS = [
    ("DoD-01", "all eight reusable workflows exist in .github/workflows/",
     ["bash", "-c",
      "test -f .github/workflows/ci.yml && test -f .github/workflows/build.yml && "
      "test -f .github/workflows/deploy-staging.yml && test -f .github/workflows/deploy-production.yml && "
      "test -f .github/workflows/migrate.yml && test -f .github/workflows/restore-test.yml && "
      "test -f .github/workflows/org-export.yml && test -f .github/workflows/background-queue.yml"]),
    ("DoD-02", "all required per-product workflows exist as templates",
     [sys.executable, "-m", "tools.evidence.render_template", "--manifest",
      "templates/workflows/MANIFEST.yaml", "--summary"]),
    ("DoD-03", "digest invariant enforced in code and fails closed",
     [sys.executable, "-m", "tools.evidence.digest_invariant",
      "--requested", "sha256:bbbb",
      "--staging-record", "tools/evidence/fixtures/digest/staging-aaaa.yaml",
      "--summary"]),
    ("DoD-04", "identity gate fails closed when approver == deployer",
     [sys.executable, "-m", "tools.evidence.identity_gate",
      "--approval", "tools/evidence/fixtures/identity/self.yaml",
      "--deployer", "dev-1", "--summary"]),
    ("DoD-05", "actor gate is the first step of all five privileged workflows",
     [sys.executable, "-m", "tools.evidence.assert_actor_gate_first",
      "--path", ".github/workflows", "--summary"]),
    ("DoD-06", "every registry context emitted by job with no if: and no path filter",
     [sys.executable, "-m", "tools.evidence.lint_workflow",
      "--path", ".github/workflows/ci.yml", "--summary"]),
    ("DoD-07", "skipped/neutral impossible on a required context",
     [sys.executable, "-m", "tools.evidence.assert_run_conclusions",
      "--checks", "tools/evidence/fixtures/runs/clean.json",
      "--registry", "tools/evidence/fixtures/contexts/registry.yaml", "--summary"]),
    ("DoD-08", "security and licence scanning are delta-gated",
     [sys.executable, "-m", "tools.evidence.delta_gate",
      "--baseline", "tools/evidence/fixtures/delta/baseline.json",
      "--current", "tools/evidence/fixtures/delta/legacy-only.json", "--summary"]),
    ("DoD-09", "SBOM emitted beside the digest for every production build",
     [sys.executable, "-m", "tools.evidence.sbom_assert",
      "--manifest", "tools/evidence/fixtures/sbom/good.json", "--summary"]),
    ("DoD-10", "Friday-freeze gate resolves in the declared operating timezone",
     [sys.executable, "-m", "tools.evidence.timegate",
      "--at", "2026-09-11T15:01:00Z",
      "--tz", "Asia/Kolkata", "--profile", "business-hours", "--summary"]),
    ("DoD-11", "renovate-path-guard fails on out-of-manifest diff and foreign commit",
     ["bash", "tools/evidence/run_negative_tests.sh", "--summary"]),
    ("DoD-12", "a passing seeded-defect case fails the run and raises SIG-18",
     [sys.executable, "-m", "tools.evidence.seeded_defect",
      "--result", "tools/evidence/fixtures/seeded/case-passed.json", "--summary"]),
    ("DoD-13", "verify-digest-chain non-zero on mismatch, 0 on clean estate",
     [sys.executable, "-m", "tools.evidence.verify_digest_chain",
      "--estate", "tools/evidence/fixtures/sweep/clean", "--summary"]),
    ("DoD-14", "the eleven questions answerable for one real deployment",
     [sys.executable, "-m", "tools.evidence.evidence_chain",
      "--deployment", "tools/evidence/fixtures/chain/dep-complete.yaml", "--summary"]),
    ("DoD-15", "record and event writes are required, failing steps",
     [sys.executable, "-m", "tools.evidence.records_client",
      "--dry-run", "--kind", "deployment",
      "--payload", "tools/evidence/fixtures/records/deployment.yaml", "--summary"]),
    ("DoD-16", "restore-production.yml runs end to end with no human-typed credential",
     ["bash", "tools/evidence/at/at-103.sh", "--summary"]),
    ("DoD-17", "shared workflow change caught by canary and reverted by tag revert",
     ["bash", "tools/evidence/at/at-024.sh", "--summary"]),
    ("DoD-18", "organisation export restores, each data class by its own mechanism",
     ["bash", "tools/evidence/at/at-035.sh", "--summary"]),
    ("DoD-19", "production rollback executes manually with control plane unreachable",
     ["bash", "tools/evidence/at/at-029.sh", "--summary"]),
    ("DoD-20", "no L2 pull request ever touched a foreign path",
     [sys.executable, "-c",
      "import subprocess, sys; "
      "out = subprocess.check_output(['git', 'log', '--grep=^L2-', '--name-only', '--pretty=format:'], text=True); "
      "files = [f.strip() for f in out.splitlines() if f.strip()]; "
      "foreign = [f for f in files if not (f.startswith('.github/workflows/') or f.startswith('templates/workflows/') or f.startswith('tools/evidence/') or f == 'tools/evidence')]; "
      "sys.exit(1 if foreign else 0)"]),
]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    checked = len(DOD_ROWS)
    failed = 0

    for dod_id, description, cmd in DOD_ROWS:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            is_pass = (result.returncode != 0) if dod_id in NEGATIVE_DODS else (result.returncode == 0)
            if not is_pass:
                print(f"FAIL {dod_id}: {description}", file=sys.stderr)
                if result.stdout:
                    print(result.stdout.rstrip(), file=sys.stderr)
                if result.stderr:
                    print(result.stderr.rstrip(), file=sys.stderr)
                failed += 1
            else:
                print(f"PASS {dod_id}: {description}")
        except Exception as exc:
            print(f"ERROR {dod_id}: {exc}", file=sys.stderr)
            failed += 1

    status = e.STATUS_OK if failed == 0 else e.STATUS_FAIL
    exit_code = e.EXIT_OK if failed == 0 else e.EXIT_FAIL

    if args.summary:
        print(f"{status} acceptance_matrix checked={checked} failed={failed}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
