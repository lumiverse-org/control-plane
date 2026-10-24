TASK ID:            L1-103 / L1-202
CONTRACT FILE:      registries/roles.yaml
CONTRACT VERSION:   1

WHAT THE CONTRACT SAYS NOW
roles:
  - id: founder
    default_capabilities: [strategy, budget, hiring, lifecycle-decision, customer-commitment, exceptional-approval, people-intelligence]

WHAT THE TASK REQUIRES
MasterSpec Section 101 Decision D106 (line 10217) and Invariant 79 explicitly mandate:
"No role default carries a dangerous capability. Section 7.1 and Section 64.1 both state that a new person enters with no `production-approval` and no dangerous capabilities and that capabilities are never inherited silently from a role default, and invariant 79 makes minimum privilege binding — while `roles.yaml` granted `production-approval` by default to five roles, contradicting all three. The dangerous set is named and is explicit-grant-only: `production-approval`, `platform-change-approval`, `platform-admin`, `security-review`, `migration-review`, `exceptional-approval`, `lifecycle-decision`, `people-intelligence`. Control-plane CI rejects a role default containing any of them. Role defaults now carry only what describes the shape of the job."

THE GAP, STATED AS A FACT
Master Spec Decision D106 already decided that dangerous capabilities must not appear in any role default. However, `registries/roles.yaml` (transcribed verbatim from MasterSpec §8 before D106 was reconciled into the registry artifact) still lists three dangerous capabilities in the `founder` role's `default_capabilities`: `lifecycle-decision`, `exceptional-approval`, and `people-intelligence`.
This contradiction directly breaches D106. It is currently masked by an intentional xfail in `validators/registry/tests/test_r_cap_02.py::test_spec_founder_row_known_contradiction`, and has never been entered into the canonical `_FOUNDER_DECISIONS.md` or `docs/decisions/register.tsv` (it was only noted in an informal, untracked lane-local note "D-L0-09" in `lanes/L0-01-phase-0-contracts.md`).
Whether to strip those three capabilities from `registries/roles.yaml`'s founder defaults is a Founder call with estate governance implications.

BLAST RADIUS I CAN OBSERVE
- registries/roles.yaml (founder role default_capabilities at line 5)
- validators/registry/rules/r_cap_02.py (enforcement rule for dangerous capabilities in role defaults)
- validators/registry/tests/test_r_cap_02.py (test_spec_founder_row_known_contradiction)
- lanes/L1-05-tasks.md (L1-103 and L1-202 task specifications)
- lanes/L0-01-phase-0-contracts.md (untracked local note D-L0-09)

STATUS: RESOLVED 2026-10-24 — Founder decided: strip the 3 capabilities, matching D106
RESOLUTION NOTE: The three dangerous capabilities (lifecycle-decision, exceptional-approval, people-intelligence) were stripped from registries/roles.yaml founder default_capabilities; test_r_cap_02.py's xfail was removed and all tests pass cleanly.
