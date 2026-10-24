#!/usr/bin/env bash
set -euo pipefail
# e2e/stages/12-reconcile.sh
source e2e/lib/checkpoint.sh

[ ! -x ./reconciler/run ] || ./reconciler/run --mode detect --record > "${E2E_OUT}/evidence/reconcile.json" 2>/dev/null || true

# CP-1201 AT-102. The permanent seeded canary MUST be found. Zero findings is a FAILED run.
cp_assert CP-1201 "reconciliation found the seeded canary" \
  jq -e '.findings | map(select(.canary == true)) | length == 1' "${E2E_OUT}/evidence/reconcile.json"

cp_assert CP-1202 "a zero-finding run would be classified failed, not clean" \
  jq -e '.run_verdict != "clean" or (.findings | length) > 0' "${E2E_OUT}/evidence/reconcile.json"

# CP-1203 Per-registry comparison counts recorded, so a silently narrowed comparison is itself visible
#         drift (Section 53.1).
cp_assert CP-1203 "per-registry comparison counts recorded and non-zero" \
  jq -e '.comparison_counts | to_entries | all(.value > 0)' "${E2E_OUT}/evidence/reconcile.json"

# CP-1204 The clean run is RECORDED as clean. Silent drift is not permitted (invariant #44).
cp_assert CP-1204 "run result written whether or not findings exist" \
  ./tools/records/find-record --store records/reconciliation --newer-than "${E2E_RUN_START}"

# CP-1205 AT-033. Present the reconciler with a STRICTER-than-declared production control; it must raise it
#         for human review and must NOT relax it (invariant #81).
cp_assert CP-1205 "stricter-than-declared control is raised, not relaxed" \
  ./tools/e2e-drive/stricter-control-probe --repo "${E2E_REPO}" \
    --tighten required_approving_review_count --expect raised-for-review --expect-not relaxed

# CP-1206 AT-032, self-observability: break the health job on purpose; the OS must report its own failure.
cp_assert CP-1206 "the operating system reports a failure in its own health job" \
  ./tools/e2e-drive/self-observability-probe --break health-job --expect-signal SIG-13

# CP-1207 The independent control verifier ran off the ops VM, under its own credential, and wrote to a
#         surface the ops VM cannot write to (Section 53.1).
cp_assert CP-1207 "independent control verifier result present and externally written" \
  ./tools/records/find-record --store records/control-verifier --newer-than "${E2E_RUN_START}" \
    --require writer=control-verifier --require-not writer=ops-vm

# CP-1208 AT-036 / AT-037 — an expired temporary access exception is revoked with no human action, and one
#         that cannot be auto-revoked becomes Blocking drift on its expiry date.
cp_assert CP-1208 "expired exception auto-revoked; unrevokable expiry becomes Blocking" \
  ./tools/e2e-drive/exception-expiry-probe --expect auto-revoked --expect-blocking-on-failure

# CP-1209 AT-039 — a bootstrap exception at expiry arms its gate or surfaces as Blocking drift. It cannot
#         lapse silently.
cp_assert CP-1209 "bootstrap exception at expiry arms or blocks" \
  ./tools/e2e-drive/bootstrap-expiry-probe --expect arm-or-block

# CP-1210 AT-110 — the reconciler credential is provably bounded. Executed, not asserted: six attempts,
#         all six must fail, and the credential must then still complete a normal run.
cp_assert CP-1210 "reconciler credential bounded on all six attempts, then still reconciles" \
  ./tools/e2e-drive/at-110-reconciler-bounds.sh
