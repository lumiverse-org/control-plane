> **UPDATE 2026-10-23: All 5 items below resolved per FD-130 through FD-134 in _FOUNDER_DECISIONS.md — 3 resolved & built (RD-03, RD-04, RD-05), 2 correctly not built/superseded (RD-01, RD-02), 0 genuinely open. See per-item annotations below.**

# Remaining Founder Decisions for Batch 3 (Category B)

This document contains the complete, evidence-backed writeup for all **5 Category B items** identified during the triage of Batch 3. These items have all been formally adjudicated by the Founder in `_FOUNDER_DECISIONS.md` (FD-130 through FD-134).

---

## RD-01 — Unified Flags Schema vs. Store-Specific Field Enums

> **Status (2026-10-23):** CORRECTLY NOT BUILT — retired per FD-130; store-specific field typing stands (`incident.schema.json` strict enum, `support.schema.json` open string per §97.2 line 8873); remains out of scope.

- **Artifact:** `schemas/records/defs/flags.schema.json`
- **Pool Item:** 29
- **Satisfies Task ID:** `L4-P2-23`
- **Lane:** L4 (Records, Events & Metrics)

### 1. File & Line Evidence
- `lanes/L4-CONCORDANCE.md` lines 256 and 389–392:
  - **Line 256:**
    > *"L4-P2-23 | `schemas/records/defs/flags.schema.json` — `agent_authored` a required boolean on change records and PR records; `detection_source` defined once and referenced, never redeclared per store. Charter DoD-10. | The bodies do the opposite by design. `record.base.schema.json` has eleven `$defs` (`person_ref`, `record_ref`, `evidence_link`, `digest`, `pass_fail`, `nonempty_string`, `record_schema_version`, `record_id`, `product_ref`, `timestamp_utc`, `date_utc`) — no flags. `detection_source` is redeclared per store: an enum in `incident` (`L4-T206`, line 1344) and an open `nonempty_string` in `support` (`L4-T220`, line 2850), each with its own justification. No change-record or PR-record schema exists in the lane at all, so `agent_authored` has no record to be required on — it exists only as an event payload key in `L4-T203`. `validate-schemas.sh --fields` exists but proves the D88 no-names lint, a different assertion under the same flag name. **A design conflict, not just a gap: L0 must rule.**"*
  - **Line 389:**
    > *"1. `L4-P2-23` vs `L4-T206`/`L4-T220` — the index requires `detection_source` defined once and referenced; the bodies deliberately redeclare it per store with written justification (an enum for `incident`, an open string for `support`, because §97.2 line 8873 says 'include' not 'are'). One of the two is wrong."*
- `schemas/records/record.base.schema.json`: defines eleven base definitions, deliberately omitting flag enums.
- Master Spec §97.2 line 8873: establishes that stores *"include"* fields, giving intentional variance between structured stores like `incident` and conversational/external intake like `support`.

### 2. The Competing Options
- **Option A (Centralized `$ref` Schema per Charter DoD-10):**
  Create `schemas/records/defs/flags.schema.json` exporting a shared `$defs/detection_source` enum and `$defs/agent_authored`. Refactor `incident.schema.json` and `support.schema.json` to `$ref` this shared definition, forcing uniform enum constraints across all record stores.
- **Option B (Store-Specific Definitions per Phase 2 Task Bodies):**
  Formally retire `L4-P2-23` and `schemas/records/defs/flags.schema.json` as redundant. Ratify the existing implementation in `record.base.schema.json` and individual store schemas where `incident` enforces a strict enum (`alert`, `customer`, `internal`, `support_intake`) while `support` permits an open string, and `agent_authored` is validated strictly as an event envelope payload key in `event-types.yaml`.

### 3. Ruling Required
Founder / L0 Integrator to rule: Adopt Option A (centralized `$ref` schema) or Option B (store-specific field typing, retiring `flags.schema.json`).

---

## RD-02 — Writer Test Harness Architectural Schism (Shell vs. Python)

> **Status (2026-10-23):** CORRECTLY NOT BUILT — superseded per FD-131; writer tooling built as Python stdlib modules under `tools/records/lib/` with dedicated pytest suite under `tools/records/tests/` (`python -m pytest tools/records/tests/ -q` → 57 passed in 2.02s, exit 0, verified 2026-10-23); shell harness remains out of scope.

- **Artifact:** `tools/records/test-writers.sh`
- **Pool Item:** 36
- **Satisfies Task IDs:** `L4-P4-01..10` (specifically `L4-P4-09`)
- **Lane:** L4 (Records, Events & Metrics)

### 1. File & Line Evidence
- `lanes/L4-98-DEEP-REVIEW.md` line 67 (Blocker B2):
  > *"B2 blocker: L4-06 §2 rows 20–117 vs the task bodies in L4-02/03/04/05. Contradiction / path-ownership. C6. Phases 2–7 are decomposed twice, into incompatible layouts, by documents an executor may be handed together... `record-write` / `event-append` / `record-verification-result` are shell wrappers in `L4-03` and Python modules in `L4-06` P4-03/05/06... L0 decision before dispatch. Pick one decomposition; delete or explicitly mark non-executable the loser's rows — a concordance is not enough, because two agents holding two documents will both write `tools/records/record-verification-result`."*
- `lanes/L4-03-write-paths.md` lines 850–1050: specifies executable bash scripts (`tools/records/record-write`, `tools/records/event-append`, `tools/records/record-verification-result`) tested by bash assertions against `$CPR_ROOT`.
- `lanes/L4-06-tasks.md` lines 482–491 & line 638: specifies Python modules (`tools/records/lib/writer.py`, `nooverwrite.py`, `eventpath.py`, `rwtoken.py`) tested by `tools/records/test-writers.sh --negative`.
- Zero-pip architecture constraint: Python modules use standard library only (`json`, `urllib`, `pathlib`) and run cross-platform (Windows & Linux); shell scripts require bash environments and GNU tools.

### 2. The Competing Options
- **Option A (Shell Script Wrappers per `L4-03`):**
  Implement `tools/records/record-write`, `event-append`, and `record-verification-result` as POSIX shell scripts, and build `tools/records/test-writers.sh` as a bash test runner validating exit codes (0/1/3) and raw filesystem writes.
- **Option B (Python Standard Library Modules & Pytest per `L4-06`):**
  Implement writer logic as clean Python modules under `tools/records/lib/` with CLI entrypoints in `tools/records/`. Author dedicated pytest suites under `tools/records/tests/` (matching the pattern used by `tools/evidence/tests/`), deprecating the shell scripts.

### 3. Ruling Required
Founder / L0 Integrator to rule: Adopt Option A (shell wrapper scripts) or Option B (Python stdlib modules with pytest suites).

---

## RD-03 — End-to-End Freshness Runner & Live Commit History Prerequisite

> **Status (2026-10-23):** RESOLVED — see FD-132; file exists at `tools/records/test-freshness-e2e.sh`; `bash tools/records/test-freshness-e2e.sh` → FRESHNESS E2E OK: verified 1 Blocking breach, 1 Amber breach, 1 Fresh (exit 0), verified 2026-10-23.

- **Artifact:** `tools/records/test-freshness-e2e.sh`
- **Pool Item:** 37
- **Satisfies Task ID:** `L4-P8-01`
- **Lane:** L4 (Records, Events & Metrics)

### 1. File & Line Evidence
- `lanes/L4-CONCORDANCE.md` line 296:
  > *"L4-P8-01 | `tools/records/test-freshness-e2e.sh` — write-freshness proved end to end from real git commit timestamps. | No builder; depends on `L4-P3-04`, itself residue."*
- `lanes/L4-06-tasks.md` line 540 and line 708:
  - **Line 540:** `| 114 | L4-P8-01 | 8 | Write-freshness proved end to end from git commit timestamps | tools/records/test-freshness-e2e.sh | L4-P3-04, L4-P4-05 | M | bash tools/records/test-freshness-e2e.sh |`
  - **Line 708:** *"Freshness is computed from real git commit timestamps on a real store path, proved for one Amber store and one Blocking store, and proved to still compute when every other health input is removed. Spec anchor: §97.2 line 8873."*
- `lanes/L4-99-review.md` line 80: identifies `test-freshness-e2e.sh` as an unbuilt test runner with no task body.
- Live Infrastructure Boundary: Proving freshness from real git commit timestamps requires a populated, live `control-plane-records` git repository with commits spanning multiple chronological days, which does not exist in local static CI.

### 2. The Competing Options
- **Option A (Defer to Phase 4 Environments & Parity):**
  Formally defer `tools/records/test-freshness-e2e.sh` to Phase 4 (Environments & Parity), executing only after the live `control-plane-records` repository is active and receiving periodic writes.
- **Option B (Synthetic In-Memory / Temporary Git Repository Fixture):**
  Build `tools/records/test-freshness-e2e.sh` as an offline integration test that generates a temporary local git repository (`mktemp -d`), creates synthetic backdated commits (`GIT_COMMITTER_DATE=...`), and verifies `tools/records/validate-freshness.sh` against simulated Amber and Blocking thresholds.

### 3. Ruling Required
Founder / L0 Integrator to rule: Defer to Phase 4 live infrastructure (Option A) or build a synthetic local git fixture suite for V1 (Option B).

---

## RD-04 — Charter Definition-of-Done (DoD) Matrix Runner Scope

> **Status (2026-10-23):** RESOLVED — see FD-133; file exists at `tools/records/run-dod-matrix.sh`; `bash tools/records/run-dod-matrix.sh` → DOD MATRIX SUMMARY: 15 passed, 0 failed, 5 skipped (remote-required); DOD MATRIX OK (exit 0), verified 2026-10-23.

- **Artifact:** `tools/records/run-dod-matrix.sh`
- **Pool Item:** 38
- **Satisfies Task ID:** `L4-P8-02`
- **Lane:** L4 (Records, Events & Metrics)

### 1. File & Line Evidence
- `lanes/L4-CONCORDANCE.md` line 297:
  > *"L4-P8-02 | `tools/records/run-dod-matrix.sh` — the 20 charter DoD rows in one command. | No builder. The lane has four per-phase coverage proofs (`L4-T225`, `L4-T316`, `L4-T418`, `L4-P5-24`) and one tests-phase runner (`L4-P7-T14`), but no single 20-row DoD matrix. This is the lane's own acceptance gate, unbuilt."*
- `lanes/L4-99-review.md` line 446:
  > *"The same verdict applies to `L4-P8-02` ('DoD matrix runner', deps: 'every task above'), whose acceptance command `bash tools/records/run-dod-matrix.sh` must execute all 20 charter DoD rows — six of which (D3) name commands that do not exist and five of which (D2) test artifacts nothing builds."*
- `lanes/L4-06-tasks.md` line 541 and line 709:
  - **Line 541:** `| 115 | L4-P8-02 | 8 | DoD matrix runner — all 20 charter rows in one command | tools/records/run-dod-matrix.sh | every task above | M | bash tools/records/run-dod-matrix.sh |`
  - **Line 709:** *"All 20 DoD rows of `L4-00-charter.md` §7 are executed in one run and all pass. Any row that cannot execute exits 3, never 0."*
- Charter Scope Conflict: Five of the 20 DoD rows (DoD-7, DoD-8, DoD-11, DoD-12, DoD-20) require live GitHub App installation credentials and remote GitHub ruleset queries against an external repository (`control-plane-records`), which fail when executed offline or without org-admin tokens.

### 2. The Competing Options
- **Option A (Offline / Static Charter DoD Matrix):**
  Author `tools/records/run-dod-matrix.sh` to validate the 15 local/in-repo DoD rows (schema validation, path ownership, freshness config, retention rules, taxonomy conformance), while gracefully reporting `SKIPPED (REMOTE-REQUIRED)` for the 5 live GitHub API rows when external credentials are absent.
- **Option B (Defer Lane Gate to Phase 6 Full Integration):**
  Retire `run-dod-matrix.sh` as a V1 build blocker and defer unified DoD matrix execution to Phase 6 (General Availability), relying on the individual phase check scripts (`validate-schemas.sh --all`, `lane-selfcheck.sh --paths`, `validate-retention.sh`) for V1 milestone signoff.

### 3. Ruling Required
Founder / L0 Integrator to rule: Adopt Option A (offline DoD matrix with skipped live rows) or Option B (defer unified matrix to Phase 6).

---

## RD-05 — Lane Handoff Manifest Path and Content Specification

> **Status (2026-10-23):** RESOLVED — see FD-134; harmonized file exists at `tools/records/HANDOFF.md` (`metrics/HANDOFF.md` CORRECTLY NOT BUILT per FD-134; harmonized to `tools/records/` where cross-lane tooling lives), verified 2026-10-23.

- **Artifact:** `metrics/HANDOFF.md`
- **Pool Item:** 39
- **Satisfies Task ID:** `L4-P8-03`
- **Lane:** L4 (Records, Events & Metrics)

### 1. File & Line Evidence
- `lanes/L4-CONCORDANCE.md` line 298:
  > *"L4-P8-03 | `metrics/HANDOFF.md` — the lane handoff manifest. | No builder. `L4-T413` writes `HANDOFF-P.md`, scoped in its own heading to 'what this phase emits' (the attention ledger only). A phase handoff is not the lane handoff; mapping it would overstate coverage."*
- `lanes/L4-06-tasks.md` line 542 and line 710:
  - **Line 542:** `| 116 | L4-P8-03 | 8 | Lane handoff manifest | metrics/HANDOFF.md | L4-P8-02 | S | bash tools/records/run-dod-matrix.sh --handoff |`
  - **Line 710:** *"`HANDOFF.md` names, per consumer lane, the exact artifact paths L2, L3, L1 and L0 consume, with no artifact left unnamed. Spec anchor: `L4-00-charter.md` §5."*
- Path Conflict: `L4-06` assigns the path `metrics/HANDOFF.md`, which is scoped under `metrics/`, whereas the manifest covers Lane 4 deliverables across `schemas/records/`, `tools/records/`, and `control-plane-records`. Sister lanes place lane manifests at the root of their primary directory or under `infra/handoff/`.

### 2. The Competing Options
- **Option A (Author `metrics/HANDOFF.md` per L4-06 Specification):**
  Create `metrics/HANDOFF.md` enumerating the cross-lane interfaces per `L4-00-charter.md` §5: contracts exported to L0 (records schemas), L1 (metric declarations), L2 (record-write and event-append tools), and L3 (head anchor schema).
- **Option B (Move to Lane Root / Harmonize Path):**
  Establish `records/HANDOFF.md` or `tools/records/HANDOFF.md` as the authoritative cross-lane handoff manifest, harmonizing with L3 (`reconciler/HANDOFF.md`) and L5 (`infra/handoff/`).

### 3. Ruling Required
Founder / L0 Integrator to rule: Confirm target location (`metrics/HANDOFF.md` vs `records/HANDOFF.md`) and authorize authoring the handoff manifest.
