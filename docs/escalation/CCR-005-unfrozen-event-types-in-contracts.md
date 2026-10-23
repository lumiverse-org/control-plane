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
In commit `e836afacb64be059e50a7cccdc96d5e143b1d92e` ("fix(notify): align event taxonomy in platform registry with notification routes"), 8 new event type identifiers (`delegation_expiry_warning_issued`, `plan_submitted_to_approver_notification_sent`, `launch_sign_off_requested`, `pending_decision_opened`, `support_first_touch_breach`, `temporary_person_expiry_warning_issued`, `verification_blocked`, `verification_unblocked`) were added directly to `contracts/event-types.yaml` without an authorized Contract Change Request or re-freezing `contracts.sha256`. This caused `contracts.sha256` checksum verification to fail against the current repository state (recorded `1ebee5406bb231b5813bcb84c3f618248a9ebc5ac5e13be607b2e2c9557c0427`, recomputed `5ca0e8f105df387bde234f9eb6cb0215252a92dc9c826c65995416061cd23aa9` in POSIX environment / `6393fa7f886b8e8a5c9cfcd35b0271ba17c7f7481180bbe0af37444f398657bc` with local CRLF).

BLAST RADIUS I CAN OBSERVE
- contracts/event-types.yaml (canonical contract modified from 111 to 119 identifiers)
- contracts.sha256 (frozen contract checksum mismatch)
- registries/platform.yaml (modified in commit e836afac to mirror the 8 event types)
- notify/tools/check_push_list.py (depends on 119 event types passing TAXONOMY-RESOLUTION)
- lanes/L5-AUDIT-RESULTS.md (Subsystem K finding cites 119 event types)
- tests/integration/test_event_type_enum.py (tests canonical event-type list properties)

I HAVE NOT EDITED contracts/**.
STATUS: PENDING FOUNDER REVIEW (escalated to L0)
