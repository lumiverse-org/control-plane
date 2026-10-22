# L0 integrator daily, weekly, monthly and quarterly cadence

Grounded in the day model of §94.2 and the Team Lead priority model of §94.5. During the build the human lead
holds both the Founder and Team Lead surfaces (§98.7: "the Founder solo under Bootstrap Mode").

## 8.1 Daily — the integrator's day

| Time | L0 activity | Output |
|---|---|---|
| 09:30 | Blocker sweep. Read every open `blocker` issue opened since the last sweep | Each answered, or converted to an L0D decision and dated |
| 09:45 | `integration` health: `make lane-guard` across every lane branch pushed overnight | Green list; any red branch is told to stop |
| 10:00 | Drift and orphan alerts on the control-plane repository itself — SIG-03 permission drift, SIG-05 orphan risk, SIG-13 failed reconciliations | Blocking-class items actioned before anything else |
| 10:30 | **Contract-freeze integrity check**: `make promote-check` sub-step verifying `contracts.sha256` still matches | `CONTRACTS-FROZEN OK` |
| 10:30–13:00 | Heavy block (§94.2). L0 authoring: contracts, docs, decision records | The day's L0 deliverable |
| 14:00 | Window-tight block: lane PR review — partition compliance and contract conformance only, never style | Approvals or change requests |
| 16:30 | Second blocker sweep | Same-day close on everything opened before 16:00 |
| 17:00 | **Contract window** — the only time `contracts/**` is edited, and only under an approved CCR | Re-freeze + decision record |
| 17:30 | End-of-day readiness check (§94.5 priority 10), adapted to the build: every lane has an unblocked next task; no unactioned Blocking-class drift; no blocker older than one working day; no lane branch older than one day unrebased | Actioned or explicitly carried over with a recorded reason |

**Only these interrupt L0** (§94.5, adapted): a blocker issue, a CCR, Blocking-class drift, a red `integration`,
and a lane branch that has touched a foreign path. Routine lane PR notifications do not.

## 8.2 Weekly — the integrator's week

| When | L0 activity | Anchor |
|---|---|---|
| Monday 09:30 | Portfolio review of the build: phase position per lane, P0-before-P2 lock status, every open L0D | §94.8 |
| Monday 10:00 | Which constraint binds this week — which lane is the bottleneck, and whether it is a contract gap or a capacity gap | §94.6 |
| Monday 14:00 | Verification sequence for the week — which acceptance tests of §100 become provable this week | §94.8 |
| **Wednesday** | **MERGE TRAIN** — the weekly cycle, run in the fixed order (§9) | PARTITION.md |
| Midweek, default Thursday | Standing decision window, thirty minutes: every open L0D prompt actioned, deferred with a date, or explicitly declined | §94.6, D79 |
| Friday 15:00 | Freeze: no promotion `integration → main` after this point in the week | §94.8 |
| Friday 16:30 | Weekly banded attention self-report, five minutes | §94.8, §97.4 |
| Friday 17:00 | **Weekly bootstrap log entry** under `records/bootstrap-log/` — the fixed three-field template: gates stubbed and armed; bootstrap exceptions opened and closed; phase completion checks run and their results. Two of the three fields are generator-filled; L0 writes the judgment lines | §95.4, §94.8 |
| Friday 17:15 | Next week's lane queue refilled — every lane has a Ready task with satisfied dependencies | §94.5 priority 6 |

The bootstrap-log entry is not optional and has a detector: control-plane CI raises **Blocking** drift when the
newest entry is older than the calibrated staleness window, initial value 7 days (§95.4, L0D-17).

## 8.3 Monthly and quarterly

| Cadence | L0 activity | Anchor |
|---|---|---|
| Monthly | Dependency, Scorecard, cost-band and asset-expiry sweep across the two repositories | §94.8 |
| Monthly | Judgment-capture ritual, 15 minutes: the month's classification and routing judgment calls recorded so they feed Coordination attention and calibration | §94.8 |
| Quarterly, month 1 | Operating-system review from the generated review pack — retires at least one policy, one metric or one automation, or records why nothing warranted retirement (AT-045) | §94.8, §98.5 G8 |
| Quarterly, month 2 | Escrow seal audit and its functional verification | §94.8, §14.4 |
| Quarterly, month 3 | Control-plane disaster-recovery drill | §94.8 |

Quarterly rituals are staggered, not stacked; the month assignments above are the spec's stated initial values and
are recalibrated only by the ritual attention-hours budget line of §57.2 (L0D-17).
