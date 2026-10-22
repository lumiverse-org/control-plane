# The standing decision window — thirty minutes, midweek, default Thursday

Anchors: MasterSpec v4.0 Section 94.6; decision D79; L0-00-charter.md Section 8.2.
Input:   make decisions
Rule:    every entry actioned, deferred with a date, or explicitly declined (Section 98.1).
         "Deferred" is not a state. A deferral is a review_date on a closure, or the entry stays open.

## The order of work, fixed

1. `make decisions-lint`            — if this is not OK, stop; the queue is not trustworthy.
2. `make decisions | head -20`      — P0 first, then P1, then by gating phase.
3. For each entry actioned:
     a. read the full statement:  implementation/lanes/L0-04-decisions-register.md section 3
     b. write the subject file:   docs/decisions/subjects/<REG-nnn>.txt
        one `option: ` line per option considered (at least two)
        one `evidence: ` line per piece of evidence
        one `review_date: YYYY-MM-DD` line
     c. `docs/decisions/bin/reg-close.sh <REG-nnn> <closed|declined|withdrawn> \
           docs/decisions/subjects/<REG-nnn>.txt`
     d. `docs/decisions/bin/reg-render.sh`
     e. `make decisions-lint`       — must print REG-LINT OK checks=8
4. One commit per window, message: `L0 decision window <YYYY-MM-DD>: closed <ids>`.

## What is never done here

- No entry is closed without at least two options_considered and an ISO review_date.
- No entry is marked closed to clear the queue. An entry with no answer stays open;
  an entry that will not be answered is `declined` and carries the Section 98.1 fields.
- No lane file is edited. A closure that changes what a lane must build is followed by an
  L0-issued reissue of that lane file, never by the lane adapting on its own.
