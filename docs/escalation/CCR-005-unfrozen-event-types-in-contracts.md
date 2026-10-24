TASK ID:            L0-P0-025 / L5 Notification Taxonomy Alignment
CONTRACT FILE:      contracts/event-types.yaml
CONTRACT VERSION:   C-EVT-TYPES-1 (119 identifiers)

WHAT THE CONTRACT SAYS NOW
contracts/event-types.yaml lines 116-127:
  - support_loop_closure
  - deletion_request_recorded
  - work_item_closed
  - delegation_expiry_warning_issued
  - plan_submitted_to_approver_notification_sent
  - launch_sign_off_requested
  - pending_decision_opened
  - support_first_touch_breach
  - temporary_person_expiry_warning_issued
  - verification_blocked
  - verification_unblocked

WHAT THE TASK REQUIRES
`contracts/event-types.yaml` is the canonical, frozen event type contract created under L0-P0-025 and frozen in `contracts.sha256`. Per `lanes/L0-01-phase-0-contracts.md`: "Lane files must cite this file, never invent an identifier. No lane edits it: a new identifier is a CCR filed with L0 and added here only."
In commit `d4dcc0dbf71af72b62b0aa5d92b959100153b608` (FD-138), `contracts.sha256` was frozen with checksum `1ebee5406bb231b5813bcb84c3f618248a9ebc5ac5e13be607b2e2c9557c0427`.

THE GAP, STATED AS A FACT
In commit `e836afacb64be059e50a7cccdc96d5e143b1d92e` ("fix(notify): align event taxonomy in platform registry with notification routes"), 8 new event type identifiers (`delegation_expiry_warning_issued`, `plan_submitted_to_approver_notification_sent`, `launch_sign_off_requested`, `pending_decision_opened`, `support_first_touch_breach`, `temporary_person_expiry_warning_issued`, `verification_blocked`, `verification_unblocked`) were added directly to `contracts/event-types.yaml` without an authorized Contract Change Request or re-freezing `contracts.sha256`. This caused `contracts.sha256` checksum verification to fail against the repository state.
Recipe (`make promote-check` / `make freeze`):
  `find contracts -type f -not -path 'contracts/gate/*' -not -path 'contracts/ci/*' | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1`
- Recorded in `contracts.sha256` (commit `d4dcc0db` / FD-138): `1ebee5406bb231b5813bcb84c3f618248a9ebc5ac5e13be607b2e2c9557c0427`
- Recomputed at commit `0e21095` (with 8 new event types in `contracts/event-types.yaml`): `b9a5f4225335be13f65a38b6dc1f8ba5ec75bb86e149b7f51af118277974e77e`
- Recomputed at current `HEAD` (with FD-115 `pilot_products` addition to `contracts/v1-scope.yaml` in commit `d098bf2`): `f60b583cde54fba9f26f85f68072c2511c543c31d9a9df18b30db11cdf54d6aa`

- Refrozen in `contracts.sha256` (commit `gravity/batch-4` / FD-140): `a65ae4de20763689c1f13b8ac0ee15a0288b89742acd7898834405c023e2d58f`

BLAST RADIUS I CAN OBSERVE
- contracts/event-types.yaml (canonical contract modified from 111 to 119 identifiers)
- contracts.sha256 (frozen contract checksum mismatch — refrozen per FD-140)
- registries/platform.yaml (modified in commit e836afac to mirror the 8 event types)
- notify/tools/check_push_list.py (depends on 119 event types passing TAXONOMY-RESOLUTION)
- lanes/L5-AUDIT-RESULTS.md (Subsystem K finding cites 119 event types)
- tests/integration/test_event_type_enum.py (tests canonical event-type list properties)

STATUS: RESOLVED 2026-10-24 — Founder decided: formally ratify the 8 event types per FD-140 and refreeze contracts.sha256

