TASK ID:            L1-308 / R-PRD-08, R-PRD-20..R-PRD-26
CONTRACT FILE:      contracts/registry/product.contract.v2.json (and schemas/product/product.contract.v2.schema.json)
CONTRACT VERSION:   2

WHAT THE CONTRACT SAYS NOW
1. Blocker 1 (Library consumer contract tests):
   `contracts/registry/product.contract.v2.json` defines the `verification` block as:
   ```json
   "verification": {
     "type": "object",
     "required": ["automated", "method", "evidence_url", "last_verified_at"],
     "properties": {
       "automated": { "type": "string", "enum": ["required", "optional", "not-applicable"] },
       "method": { "type": "string" },
       "evidence_url": { "type": "string" },
       "last_verified_at": { "type": "string", "format": "date-time" }
     }
   }
   ```
   There is no field in `product.yaml` / `product.contract.v2.json` for `consumer_contract_tests`.
   In contrast, MasterSpec §20.1's `service.yaml` contract carries `verification.consumer_contract_tests` explicitly.

2. Blocker 2 (Customer-hosted recovery exemption):
   `contracts/registry/product.contract.v2.json` defines the `recovery` property:
   ```json
   "recovery": {
     "type": ["object", "null"],
     "properties": {
       "rpo_minutes": { "type": "integer" },
       "rto_minutes": { "type": "integer" },
       "backup_cadence": { "type": "string" },
       "last_restore_test": { "type": "string", "format": "date" }
     }
   }
   ```
   There is no cross-file reference mechanism in `product.yaml` to resolve exemptions in `exceptions.yaml` (§54.1).

WHAT THE TASK REQUIRES
MasterSpec §15.7 defines the Conformance Profiles equivalent-evidence matrix:
- `library` profile: "Registry version plus consumer contract tests. Internal dependencies may be empty. automated verification required."
- `customer-hosted` profile: "recovery non-null OR a recorded exemption with a compensating control."

Task L1-308 (`lanes/L1-05-tasks.md`, lines 1856-1908) implements the seven §15.7 conformance profile rules (`R-PRD-08`, `R-PRD-20`..`R-PRD-26`). The implementation in `validators/registry/rules/r_prd_08.py` and `validators/registry/tests/test_r_prd_08.py` passes 17 tests and explicitly isolates two intentional, spec-mandated blockers as `strict=True` `xfail` test cases:
1. `test_library_missing_consumer_contract_tests_triggers_r_prd_21`: checks that a library product without consumer contract test declarations is flagged.
2. `test_customer_hosted_recovery_exempted_is_not_flagged`: checks that a customer-hosted product with a recorded exemption in `exceptions.yaml` is permitted without a local non-null `recovery` block.

THE GAP, STATED AS A FACT
Two architectural collisions prevent unblocking these two rules without Founder direction:

1. Blocker 1 — Library Conformance Evidence Gap:
   MasterSpec §15.7 requires consumer contract tests for `library` profiles, but §15.1 `product.yaml` carries no `consumer_contract_tests` field. §20.1 `service.yaml` carries `verification.consumer_contract_tests`, but a library is not currently required to author `service.yaml`.
   Candidate resolutions pre-filed by the task spec (deliberately not chosen):
   (a) Add a `consumer_contract_tests` field to `product.contract.v2.json` schema (a §60.2 versioned contract schema change).
   (b) Require products with `conformance_profile: library` to author a companion `service.yaml` where §20.1 verification fields already exist.

2. Blocker 2 — Customer-Hosted Recovery Exemption Cross-File Resolution:
   MasterSpec §15.7 permits customer-hosted products to satisfy disaster recovery via "a recorded exemption with a compensating control," which lives in `exceptions.yaml` (§54.1) in a separate repository path.
   The validator currently operates per-file on `product.yaml` without cross-file resolution into `exceptions.yaml`.
   Candidate resolutions pre-filed by the task spec (deliberately not chosen):
   (a) Implement a cross-file resolver in Lane 1 validators permitting `R-PRD-23` to ingest and validate `exceptions.yaml` exemption tokens.
   (b) Permit an inline exception identifier token within `recovery.exemption_id` directly in `product.yaml`.

BLAST RADIUS I CAN OBSERVE
- `contracts/registry/product.contract.v2.json` (potential schema change under Option 1a)
- `schemas/product/product.contract.v2.schema.json` (schema mirror)
- `validators/registry/rules/r_prd_08.py` (implementation of `R-PRD-21` and `R-PRD-23`)
- `validators/registry/tests/test_r_prd_08.py` (xfail tests `test_library_missing_consumer_contract_tests_triggers_r_prd_21` and `test_customer_hosted_recovery_exempted_is_not_flagged`)
- `lanes/L1-05-tasks.md` (task L1-308 specification)
- `lanes/L1-AUDIT-RESULTS.md` (audit finding and pending task row)

STATUS: RESOLVED 2026-10-24 — Founder decisions: (a) add consumer_contract_tests directly to the v2 product schema under verification (not requiring companion service.yaml); (b) build a real cross-file resolver connecting product.yaml's recovery value to exceptions.yaml exemption records (not an inline token). Both decisions implemented and verified with zero xfails.
