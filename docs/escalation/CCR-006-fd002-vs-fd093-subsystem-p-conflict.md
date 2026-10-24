TASK ID:            FD-002 / FD-093 / PFD-019 / L4-T413
CONTRACT FILE:      PARTITION.md / _FOUNDER_DECISIONS.md
CONTRACT VERSION:   1

WHAT THE REPOSITORIES AND DECISIONS STATE NOW
- `_FOUNDER_DECISIONS.md` FD-002 (Decided: 2026-09-02, Band: P0, Gates: Ph0):
  "Subsystem P (people intelligence engine): L0 (the Founder). Forced. §99.3 item 1 (the attention classifier) is design-open. §99.4 item 9 defers P from V1 outright. Not delegable to any lane under any option."
- `_FOUNDER_DECISIONS.md` FD-093 (Decided: 2026-09-08, PFD-019, Band: partition, Status: DECIDED):
  "Option A — L4 owns subsystem P. Capacity planning is a metric aggregate, and L4 is the metrics lane. L4 is the consumer that must honour the `capacity_profile_eligible`, `workload_state_eligible`, and `founder_view_eligible` flags emitted by `derive.py`."
- `.planning/INGEST-CONFLICTS.md` (lines 19-22):
  Carries an active warning: "FD-093 contradicts FD-002 on subsystem P ownership... FD-093 never states it supersedes or amends FD-002... Downstream lane-ownership artifacts (PARTITION.md, lane-paths.tsv, CODEOWNERS) cannot honour both answers simultaneously — one says L0-only/non-delegable, the other says L4. Ask the founder to explicitly reconcile FD-002 and FD-093."

WHAT THE TASK REQUIRES
The governance structure requires all architectural contradictions between formal Founder Decisions to be explicitly reconciled by the Founder before lane boundaries and downstream ownership are frozen.

THE GAP, STATED AS A FACT
Both FD-002 and FD-093 are marked formally DECIDED in `_FOUNDER_DECISIONS.md`. They directly contradict each other regarding the ownership of Subsystem P (People Intelligence / Capacity Profile):
1. FD-002 assigns Subsystem P strictly to L0 as non-delegable to any other lane under any option.
2. FD-093 assigns Subsystem P to L4 without citing FD-002, without stating whether it supersedes FD-002 in whole or in part (e.g. narrowly amending it for the Capacity Profile metric slice while keeping the design-open attention classifier with L0), and without formal reconciliation.
3. Crucially, commit `d098bf2` previously modified `PARTITION.md` (line 20: adding subsystem P to Lane 4) and `metrics/attention/HANDOFF-P.md` (naming L4 as Subsystem P owner) under the assumption that the later decision (FD-093) won. This change is live in the working tree and branch `gravity/batch-3`, but remains contingent upon the Founder's explicit reconciliation of FD-002 vs FD-093. If the Founder rules that FD-002 stands or that Subsystem P belongs to L0, those modifications in commit `d098bf2` must be reverted.
4. Regarding `lane-paths.tsv`: FD-093 action item 2 specified adding a row for the Capacity Profile path. In `lane-paths.tsv`, rule `4\tmetrics/*` (line 28) already structurally covers `metrics/attention/**` (where capacity profile outputs are derived) so no syntax error or unassigned path currently occurs; however, path ownership of any non-metrics Subsystem P components remains unresolved.

BLAST RADIUS I CAN OBSERVE
- `_FOUNDER_DECISIONS.md` (FD-002 line 57 vs FD-093 line 1764)
- `.planning/INGEST-CONFLICTS.md` (standing warning at lines 19-22)
- `PARTITION.md` (line 20 updated to include subsystem P for L4 in commit d098bf2)
- `metrics/attention/HANDOFF-P.md` (updated to claim L4 ownership per FD-093 in commit d098bf2)
- `lane-paths.tsv` (covered under `4\tmetrics/*`; contingent on Subsystem P ownership)
- `CODEOWNERS` (contingent on Subsystem P code path ownership)

I HAVE NOT REVERTED PARTITION.MD OR HANDOFF-P.MD.
STATUS: PENDING FOUNDER RECONCILIATION (escalated to L0)
