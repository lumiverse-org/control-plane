# L0 DECISION REGISTER

These identifiers are PLAN-LOCAL. They are not Appendix A Decision Register ids (D1..D112) and never will be.
Every closure is written as a decision record under records/decisions/ using the Section 97.2 schema
(id, decider, prompt_received, decided, subject, options_considered, evidence, review_date).
Every open prompt lives under records/decisions/pending/ and is drained at the midweek decision window (D79).
Status values: OPEN | CLOSED | DECLINED. DECLINED carries the gate answers and a review date (Section 98.1).

## 4. The seven design-open items — reserved to L0, all of them

§99.3 names exactly seven matters the implementer must still invent. Each is assigned a plan-local decision id
below. These ids are **plan-local, not Appendix A Decision Register ids** — they never collide with `D1…D112`.

| Plan id | §99.3 item | The open matter | Closed no later than | Spec anchor 
|---|---|---|---|---
| **L0D-10** | 1 | The attention classifier and constraint diagnosis algorithm — Healthy / Watch / Action Required with the reason on the same line, and "which constraint binds" | Phase G3 (§98.5) | §98.5, §99.3 item 1 
| **L0D-11** | 2 | The `make parity` declaration format — the environment-schema format compared across local, staging and production, defined once and reused | Phase 4 (§98.2), because Phase 4's completion check runs `make parity` | §98.2, §99.3 item 2 
| **L0D-12** | 3 | Plan-checker internals — every assumed capability verified against the exact pinned GSD release, and the in-house build budgeted if verification fails | Phase 7 (§98.2); the verification itself is a Phase 1 item (§99.6 risk 4) | §98.2, §99.6 risk 4, §99.3 item 3 
| **L0D-13** | 4 | DevLake field coverage — which metrics need bespoke computation beyond DevLake's models (routine reviews absorbed cross-checked against the routing table, reviewer familiarity, reviewer-spread) | Before Phase G3 (§98.5 states G3 depends on confirmed coverage) | §98.5, §99.3 item 4 
| **L0D-14** | 5 | Machine sources for context checks — where the computable boundary is drawn across the fifteen systemic context checks of §80, with the humans named in §80.2 classifying the rest | Phase P4 (§98.6) | §98.6, §80, §99.3 item 5 
| **L0D-15** | 6 | KPI instrumentation projects — scoping each §79 row marked "available after instrumentation" as its own mini-project | Phase P2 (§98.6) | §98.6, §79, §99.3 item 6 
| **L0D-16** | 7 | Calibration methods — PLU fit, forecast scoring, sustainable-utilisation bands, the §97.4 attention-session parameters, the §72.3 confidence table | Quarterly refits; first method recorded at Phase G5 (§98.5) | §98.5, §72.3, §97.4, §99.3 item 7 

Until an item is closed, **no lane may build anything whose behaviour depends on it.** A lane that reaches such a
dependency files a blocker (§7.1) naming the L0D id.

## 5. The L0-only decision register — what only L0 may decide

Plan-local ids. Every closure is written as a decision record under `records/decisions/` using the §97.2 schema,
and every open prompt as a record under `records/decisions/pending/` via the record-decision CLI (§97.2).

### 5.1 Contracts and schemas

| Plan id | Reserved decision | Spec anchor 
|---|---|---
| L0D-01 | The shape of every registry, product, record and event schema, and its direct transcription to JSON Schema | §7, §8, §15, §97.2 
| L0D-02 | `contract_version` policy: what constitutes a breaking change, the supported-version window, deprecation deadlines | §60, invariant 73 
| L0D-03 | `record_schema_version` and `event_schema_version` handling; the binding event envelope field list | §97.2, §97.3 
| L0D-17 | Every value marked **calibrated configuration** and its stated initial value — including "sustained" (initial 6 consecutive weeks, SIG-07/SIG-08/SIG-30), the bootstrap-log staleness window (initial 7 days, §95.4), the triage budget (initial 5 minutes per product per pass, §94.3), the AI-eval triage block (initial 30 minutes, §94.3), the SIG-42 regression tolerance (initial 5 percentage points, §52.2), the §29.5 scope-growth threshold | §84.6, Section 100 AT-074, D102 

### 5.2 Partition, ownership and access

| Plan id | Reserved decision | Spec anchor 
|---|---|---
| L0D-04 | The path→lane map and residual ownership; any extension of `lane-paths.tsv` | PARTITION.md rule 1 
| L0D-05 | Any `CODEOWNERS` edit; the rule that CODEOWNERS carries human identities only | §98.2 Phase 1 completion check 
| L0D-18 | Fail-closed versus fail-open classification of every control | §64, invariant 80 
| L0D-25 | Secrets-tier assignment and credential scope, including the records-writer's `contents: write` scope and the reconciler's declared repair scope | §40.1, §26.4, D89, invariant 25 
| L0D-26 | Anything touching subsystem L / Layer B datasource separation — the second Founder-only Grafana instance, the separately-credentialed people datasource | §90.3, §92.8, D75, invariants 106 and 109 

### 5.3 Merge train and release

| Plan id | Reserved decision | Spec anchor 
|---|---|---
| L0D-06 | Approving or denying a Contract Change Request | PARTITION.md rule 2 
| L0D-07 | Any deviation from the fixed merge order `L1 → L4 → L2 → L3 → L5` | PARTITION.md §"Branch & merge model" 
| L0D-08 | Revert versus roll-forward when `integration` breaks | §28, invariant 27 
| L0D-09 | Promotion `integration → main` | PARTITION.md §"Branch & merge model" 

### 5.4 Programme governance

| Plan id | Reserved decision | Spec anchor 
|---|---|---
| L0D-19 | Opening and closing every bootstrap exception, with expiry, owner and deactivation trigger | §95, §54.2, invariant 77, SIG-39 
| L0D-20 | Declaring a phase `declined` — a recorded decision carrying the gate answers, the forgone capabilities and a review date | §98.1 
| L0D-21 | Releasing the P0-before-P2 lock (only a `declined` P0 releases it; an unbuilt P0 holds it) | §98.1 
| L0D-22 | The drift-budget tolerances and headline thresholds in `os-health.yaml`, and each signal's `activation_dependency` and `lookback_window` | §52.1, §52.2 (D77), §53.4 
| L0D-23 | The enforcement classification — mechanical / policy / review-held — of each of the 111 invariants | §101 preamble, authored at Phase G2 
| L0D-24 | Accepting a risk or recording a plan-tier fallback (branch protection on private repos requires the Team plan; environment required reviewers are Enterprise-only and are not depended on) | §99.5, §99.6 risk 5, D73, D80 
