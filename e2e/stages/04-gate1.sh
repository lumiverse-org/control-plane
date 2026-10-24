#!/usr/bin/env bash
set -euo pipefail
# e2e/stages/04-gate1.sh
source e2e/lib/checkpoint.sh

# dev-a submits the plan for the pilot change. It touches schema, so it must state a rollback strategy.
cp_assert CP-0401 "plan submitted as a plan-approval request" \
  ./tools/gate1/submit-plan --product "${E2E_PRODUCT}" --author dev-a \
    --plan e2e/fixtures/pilot-one/plan-disable-customer.md \
    --change-class normal --impact-scope single-product --reversibility fully-reversible

# CP-0402 The plan-checker ACCEPTED this plan — it has verify commands, real symbols, a rollback strategy,
#         and legitimate packages (Section 30.2).
cp_assert CP-0402 "plan-checker accepts a well-formed plan" \
  ./tools/gate1/plan-check --plan-id "$(cat "${E2E_OUT}/plan-id")" --expect accepted

# CP-0403 The eligible approver is RESOLVED FROM CAPABILITY, not from a role name (invariant #11), and is
#         notified as a push event — AT-106.
cp_assert CP-0403 "approver resolved from capability and notified" \
  ./tools/gate1/verify-notification --plan-id "$(cat "${E2E_OUT}/plan-id")" \
    --expect-approver lead-1 --expect-event plan_submitted_notification_sent

# CP-0404 Approval by lead-1. Not by dev-a: Gate 1 admits no self-approval (Section 26.1).
cp_assert CP-0404 "Gate 1 approved by lead-1" \
  ./tools/gate1/approve --plan-id "$(cat "${E2E_OUT}/plan-id")" --as lead-1

# CP-0405 The event is written with the closed-enum type and the agent_authored flag (Section 97.3).
cp_assert CP-0405 "plan_approved event written with envelope and agent_authored flag" \
  ./tools/records/find-event --type plan_approved --product "${E2E_PRODUCT}" \
    --require-fields event_schema_version,event_id,occurred_at,recorded_at,actor,product,subject_ref \
    --require payload.gate=1 --require-present payload.agent_authored

# CP-0406 The computed requirement set was displayed alongside the plan (Section 24.2 / Section 26.1).
cp_assert CP-0406 "computed requirement set rendered on the Gate 1 surface" \
  ./tools/gate1/verify-requirement-set --plan-id "$(cat "${E2E_OUT}/plan-id")"
