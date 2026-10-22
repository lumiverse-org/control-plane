CYCLE:            <NNN>
DATE:             <YYYY-MM-DD>
HALTED AT:        <task id, e.g. L0-03-04, and the lane position L1|L4|L2|L3|L5>
BASE SHA:         <the frozen integration base for this cycle>

WHAT THE PROCEDURE REQUIRED
<verbatim quote of the step from L0-03-merge-train.md>

EXACT OUTPUT OBSERVED
<paste the literal command and its literal output — no paraphrase>

CLASSIFICATION       <one of>
  PARTITION-VIOLATION  a PR touches a foreign or unassigned path (PARTITION.md rule 1)
  CONTRACT-DRIFT       contracts.sha256 no longer matches contracts/** (PARTITION.md rule 2)
  TOOLCHAIN-BROKEN     lane-guard.sh / train-*.sh does not behave as its SELF-VERIFY states
  GATE-UNSATISFIABLE   a required status check exists that no workflow emits (Section 98.2, Phase 1)
  BAD-INTEGRATION      integration is red after a merge (L0D-08 applies)
  OTHER                <state it in one sentence; do not invent a classification>

DECISION TAKEN       <one of: SKIP-LANE | REVERT | ROLL-FORWARD | ABORT-CYCLE | DEFER-PROMOTION>
DECISION ID:         <L0D-07 | L0D-08 | L0D-09 | L0D-06 | L0D-04>
DECISION RECORD:     records/decisions/<file written via the record-decision CLI, Section 97.2>

WHAT WAS NOT DONE
No rule was relaxed, no lane branch was rebased or rewritten by L0, no required check was removed,
no contract was edited outside the 17:00 contract window under an approved CCR.

CYCLE DISPOSITION    <CONTINUED | ABORTED>
LANES STILL MERGED THIS CYCLE: <list, in train order>
