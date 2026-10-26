TASK ID:            CP-0702 / Section 34.3 / E2E-07
CONTRACT FILE:      protocol/08-smoke-and-e2e.md / docs/reference/MultiProduct_MasterSpec_v4.0.md
CONTRACT VERSION:   1

WHAT THE REPOSITORIES AND SPEC STATE NOW
1. Master Spec v4.0 Section 34.3 (line 2943):
   "Backward compatibility is required for one release cycle — new code must work against the old schema, and old code must survive the new schema. This is what makes rollback possible."
2. Section 34.4 line 2954 (Case B):
   "Migration succeeds, application deployment fails. Roll back the application to the previous digest. Schema is backward compatible by requirement, so the old digest runs correctly."
3. `protocol/08-smoke-and-e2e.md` lines 596-599:
   "# CP-0702 Backward compatibility for one release cycle (Section 34.3): the PREVIOUS digest must still run
   # against the NEW schema. This is what makes rollback possible, so it is proven, not assumed.
   cp_assert CP-0702 \"previous digest runs against the new schema\" \
     ./tools/e2e-drive/compat-probe --env staging --schema new --digest \"$(cat \"${E2E_OUT}/prev-digest\")\""

WHAT THE TASK REQUIRES
Determine whether "no predecessor exists" on an estate's first-ever greenfield deployment (Release 1 of a newly provisioned product, such as `pilot-one-api`) constitutes an architectural failure, or a distinct, honestly-labeled non-applicable / baseline-establishing state.

THE GAP, STATED AS A FACT
Section 34.3 and `protocol/08-smoke-and-e2e.md` mandate proving that the previous release digest runs against the new schema, but neither document specifies the required behavior on initial greenfield provisioning where no prior release digest exists in the estate (`${E2E_OUT}/prev-digest` absent). Two competing architectural interpretations exist:

- Reading A (Strict Fail-Closed):
  Rollback safety cannot be proven without an actual previous digest. On Release 1, CP-0702 must fail closed, meaning full E2E stage progression cannot claim pass until Release >= 2 establishes a predecessor digest baseline.
  
- Reading B (Greenfield Exemption / Baseline Skip):
  Backward compatibility spans "one release cycle." On Release 1, cycle count is 0; backward compatibility against non-existent prior versions is vacuously true or structurally non-applicable. CP-0702 should emit a distinct, audit-logged `PASS/SKIP (INITIAL_RELEASE_NO_PREDECESSOR)` state, establishing the deployed digest as the baseline for Release 2.

BLAST RADIUS I CAN OBSERVE
- `tools/e2e-drive/compat-probe` (exit code and diagnostic output)
- `protocol/08-smoke-and-e2e.md` (CP-0702 assertion semantics)
- `protocol/08-E2E-READINESS-GAP.md` (classification of CP-0702 on initial product onboarding)
- `e2e/stages/07-staging.sh` and `e2e/run.sh`

I HAVE NOT ALTERED compat-probe's fail-closed behavior pending Founder decision.
STATUS: PENDING FOUNDER DECISION (2026-10-26)
