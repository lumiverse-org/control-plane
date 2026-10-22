# The D101 arming order — step N may not start until step N-1 is recorded

Authority: D101 (spec L10194); Section 98.2 Phase 1 (spec L9017-L9018); Section 95.2 (spec L8680).
The gate that mechanically refuses an unsatisfiable arming is L5's (access/arming/, L5-01-10).
This file is L0's record of the order and of the evidence for each step.

| # | Step | Evidence recorded at | Done? |
|---|---|---|---|
| 1 | Organisation base permission = Read | L5-01-03 apply runbook output | |
| 2 | Teams created and GRANTING WRITE, interim assignment set | L5-01-05 + L5-01-12 runbook output | |
| 3 | Branch protection applied in the UNARMED profile | L5-01-07 + L5-01-12 runbook output | |
| 4 | Required-status-check list EMPTY per repository | L5-01-13 Phase 1 access completion check | |
| 5 | Checks added per phase, named by that phase's completion check | each phase's completion check | |
| 6 | Code-Owner-and-approval gate ARMED (rows 5 and 6 of arming-matrix.tsv) | docs/bootstrap/activation/T2W-<date>.md (L0-06-09) | |
| 7 | Workflow-identity gate ARMED on production deploys (row 14) | docs/bootstrap/activation/T3H-<date>.md (L0-06-10) | |

## Why the order and not the list

Section 98.2 L9017, verbatim: "Arming a Code-Owner-and-approval gate while no Team grants Write leaves
nobody whose approval counts, and Section 95.4 names the result exactly: a team that experiences its
merges mysteriously breaking." Section 98.2 L9018 states the second half: "A required check no workflow
emits blocks every pull request indefinitely; a list that silently stays empty is a gate that reads armed
and is not."

Step 2 BEFORE step 3. This is the D101 correction and it is not negotiable.
