# Bootstrap Mode — how this programme operates while one person holds the context

Authority: MasterSpec v4.0 Section 95 (spec L8636-L8712); decisions D57 (L10125) and D101 (L10194);
invariant 77 (L9554); signal SIG-39 (L4568); acceptance test AT-039 (L9361).
Owner: L0, under reserved decision L0D-19 (docs/charter/L0-00-charter.md Section 5.4).

## The one sentence that governs the scope

Bootstrap Mode is scoped PER REPOSITORY, never per company (Section 95.1, spec L8642). Product
repositories whose existing teams hold Write satisfy gate independence immediately, run fully armed
from day one, and never enter bootstrap. See docs/bootstrap/repo-scope.tsv.

## What bootstrap does NOT relax

Independence requirements only (Section 95.3, spec L8687). See docs/bootstrap/binding.tsv — eight
items that hold from day one, each carrying the Section 101 invariant number that states it.

## The files

| File | What it is |
|---|---|
| repo-scope.tsv          | which repositories are in bootstrap, and why |
| binding.tsv             | Section 95.3 — what stays binding even in bootstrap |
| gate-register.tsv       | one row per relaxed gate: expiry, owner, deactivation trigger |
| activation-checklist.tsv| Section 95.4 — the headcount thresholds and their verifications |
| arming-matrix.tsv       | the unarmed configuration recorded beside the armed one (Section 95.2 L8680) |
| exceptions/             | the rendered exception records, one file per exception |
| activation/             | evidence from each threshold's checklist run, negative tests included |

## The commands

    make bootstrap-render     # regenerate exceptions/ from gate-register.tsv
    make bootstrap-check      # fail-closed validation; last line BOOTSTRAP-CHECK OK
    make bootstrap-log        # write this week's log entry, two fields generated
    make bootstrap-fresh      # staleness detector; Blocking past the calibrated window

## The rule nobody may relax

A bootstrap exception is opened, renewed and closed by L0 alone (L0D-19). No lane opens one. A lane
that believes it needs one files a blocker (docs/escalation/BLOCKER.md) naming L0D-19.
