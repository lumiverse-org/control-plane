> **UPDATE 2026-10-23: All 44 items below are adjudicated — 4 resolved & built per FD-132..FD-134 and L1-107, 40 correctly not built (retired/superseded/deferred per FD-047, FD-112, FD-130, FD-131, FD-135, PARTITION.md, and master/06-v1-scope.md), 0 still genuinely open — see per-item annotations below.**

# New Founder Decisions & Architectural Blockers for Batch 3 (2026-10-21)

This document catalogs all 44 items from `_gravity-handoff/batch-3/pool.json` that cannot be built by an autonomous agent without violating canonical governance, scope boundaries, or architecture invariants. Each entry provides exact file and line citations, identifies the conflicting canonical decisions, and specifies the ruling required from the Founder / L0 Integrator.

---

## 1. Scope Deferrals & Partition Violations (`master-phases-2-6`)

### `metrics/cli.py` (satisfies L4-P4-01..10)
> **Status (2026-10-23):** CORRECTLY NOT BUILT — deferred per master/06-v1-scope.md §9.4 and master/04-phase-map.md (runtime CLI operational runners for live metrics stores deferred to Phase 4 Environments & Parity); remains out of scope.
- **Pool Item:** 76 (`metrics/cli.py`)
- **Scope Conflict:** Deferred to Phase 4. `master/06-v1-scope.md` §9.4 and `master/04-phase-map.md` explicitly define Phase 1/2 as schema/contract foundations and defer runtime CLI operational runners for live metrics stores (`metrics/cli.py`) to Phase 4 (Environments & Parity).
- **Architectural Contradiction:** Sibling analysis in `lanes/L4-98-DEEP-REVIEW.md` line 67 (Blocker B2) identifies an unadjudicated design schism: `L4-04` specifies a shell-based test runner (`tools/records/test-writers.sh`) asserting against mock curl commands, whereas later tasks assume a Python CLI harness (`metrics/cli.py`). Attempting to build `metrics/cli.py` now forces an unratified architectural choice before Phase 4.
- **Decision Required:** Founder to formally confirm that `metrics/cli.py` remains deferred to Phase 4 per `master/06-v1-scope.md` §9.4, or provide the frozen CLI argparse signature.

---

### `.github/workflows/eval-regression.yml` (satisfies L5-P3-12)
> **Status (2026-10-23):** CORRECTLY NOT BUILT — deferred per master/06-v1-scope.md §8.3 (AT-107 on binding must-not-claim list for V1 exit gates) and prohibited by PARTITION.md line 18 (.github/workflows/** owned exclusively by Lane 2); remains out of scope.
- **Pool Item:** 77 (`.github/workflows/eval-regression.yml`)
- **Scope Conflict:** Explicitly forbidden in V1 scope. `master/06-v1-scope.md` §8.3 explicitly includes `AT-107` and `.github/workflows/eval-regression.yml` in the binding **"must not claim"** list for V1 exit gates.
- **Partition Conflict:** Under `PARTITION.md` line 18, `.github/workflows/**` is owned strictly and exclusively by Lane 2 (`lane/2/*`). Lane 5 (`lane/5/*`) is strictly prohibited from authoring files in `.github/workflows/`.
- **Decision Required:** Drop `.github/workflows/eval-regression.yml` from the Batch 3 Lane 5 backlog as out of V1 scope per `master/06-v1-scope.md` §8.3 and in violation of `PARTITION.md`.

---

### `registries/platform.yaml` (satisfies L5-P4-01..03)
> **Status (2026-10-23):** RESOLVED for Lane 1 / CORRECTLY NOT BUILT by Lane 5 — file exists at `registries/platform.yaml` (seeded by Lane 1 under L1-107 in commit ed2c4ae per PARTITION.md line 17; `python -m pytest validators/registry/tests/test_platform_schema.py -q` → 12 passed in 0.36s, exit 0, verified 2026-10-23); Lane 5 mutation/ownership correctly rejected and AT-106 deferred per master/06-v1-scope.md §8.3.
- **Pool Item:** 78 (`registries/platform.yaml`)
- **Scope Conflict:** Forbidden in V1 scope. `master/06-v1-scope.md` §8.3 places `AT-106` (Gate 1 notification taxonomy extensions in platform registry) on the "must not claim" list for V1.
- **Partition Conflict:** Under `PARTITION.md` line 17, `registries/**` is owned strictly and exclusively by Lane 1 (`lane/1/*`). Lane 5 writing to `registries/platform.yaml` constitutes a fatal cross-lane partition violation.
- **Decision Required:** Confirm that `registries/platform.yaml` cannot be authored or mutated by Lane 5, and that AT-106 remains deferred per `master/06-v1-scope.md` §8.3.

---

## 2. Lane 4 Residual Contradictions & External Boundaries

### `control-plane-records/PROTECTION-REQUEST.md` (satisfies L4-T003)
> **Status (2026-10-23):** CORRECTLY NOT BUILT — withdrawn per lanes/L4-06-tasks.md line 557 (citing L4-00-charter.md:323) and external repo boundary; branch protection gap accepted temporarily per FD-135; remains out of scope.
- **Pool Item:** 24 (`control-plane-records/PROTECTION-REQUEST.md`)
- **Evidence:** Explicitly WITHDRAWN in `lanes/L4-06-tasks.md:557` ("**WITHDRAWN** — superseded by D107 ruleset configuration (see `L4-00-charter.md` line 323). Not built, not pending.").
- **Decision Required:** Formal deletion of Item 24 from the active task backlog.

---

### `control-plane-records/README.md` (satisfies L4-P1-T04)
> **Status (2026-10-23):** CORRECTLY NOT BUILT in control-plane — external repository path per PARTITION.md line 8; belongs strictly in control-plane-records repository; remains out of scope.
- **Pool Item:** 25 (`control-plane-records/README.md`)
- **Evidence:** External repository path. `PARTITION.md` line 8 defines `control-plane-records` as a separate git repository (`records/**`, `events/**`). Files destined for `control-plane-records` cannot be committed to the `control-plane` workspace repository.
- **Decision Required:** Route this deliverable to the `control-plane-records` repository workspace.

---

### `schemas/records/defs/flags.schema.json` (satisfies L4-P2-23)
> **Status (2026-10-23):** CORRECTLY NOT BUILT — retired as redundant per FD-130 (resolves RD-01); store-specific field typing stands (`incident.schema.json` strict enum, `support.schema.json` open string per §97.2 line 8873); remains out of scope.
- **Pool Item:** 28 (`schemas/records/defs/flags.schema.json`)
- **Evidence:** `lanes/L4-CONCORDANCE.md` line 267 formally records `L4-P2-23` (`schemas/records/defs/flags.schema.json`) as "RETIRED per FD-130. Redundant; not built." Store-specific field typing was confirmed per §97.2 line 8873 ("include" not "are"), where `incident` enforces a strict enum and `support` permits an open string, rendering an external `defs/flags.schema.json` redundant.
- **Decision Required:** L0 ruling on whether `flags.schema.json` should be created as a shared `$ref` target or retired as redundant with `event-envelope.schema.json`.

---

### `tools/records/store-inventory.yaml` (satisfies L4-P2-25)
> **Status (2026-10-23):** CORRECTLY NOT BUILT — struck by Decision D21 in lanes/L4-99-review.md line 409 in favor of `schemas/records/store-map.yaml` (which exists and has 19 store definitions, verified 2026-10-24); remains out of scope.
- **Pool Item:** 29 (`tools/records/store-inventory.yaml`)
- **Evidence:** Explicitly STRUCK by Decision D21 in `lanes/L4-99-review.md` line 409: "store-inventory.yaml is struck; schemas/records/store-map.yaml is the single authoritative store deliverable." `schemas/records/store-map.yaml` was verified and already exists with 19 rows per FD-059.
- **Decision Required:** Mark Item 29 as obsolete/superseded by `store-map.yaml`.

---

### `tools/records/test-writers.sh` (satisfies L4-P4-01..10)
> **Status (2026-10-23):** CORRECTLY NOT BUILT as shell script — superseded per FD-131 (resolves RD-02); Python stdlib writer modules built under `tools/records/lib/` with dedicated pytest suite under `tools/records/tests/` (`python -m pytest tools/records/tests/ -q` → 57 passed in 2.02s, exit 0, verified 2026-10-23); shell harness remains out of scope.
- **Pool Item:** 36 (`tools/records/test-writers.sh`)
- **Evidence:** Confirmed architectural schism cataloged in `lanes/L4-98-DEEP-REVIEW.md` line 67 (Blocker B2). `L4-04` specifies bash tests expecting live mock HTTP endpoints, while `L4-06` specifies Python test suites. Executing without live test servers causes immediate exit failure.
- **Decision Required:** L0 decision on the test harness technology (shell vs python pytest) for record writer validation.

---

### `tools/records/test-freshness-e2e.sh` (satisfies L4-P8-01)
> **Status (2026-10-23):** RESOLVED — see FD-132 (resolves RD-03); file exists at `tools/records/test-freshness-e2e.sh`; `bash tools/records/test-freshness-e2e.sh` → FRESHNESS E2E OK: verified 1 Blocking breach, 1 Amber breach, 1 Fresh (exit 0), verified 2026-10-23.
- **Pool Item:** 37 (`tools/records/test-freshness-e2e.sh`)
- **Evidence:** Built as an offline integration test with synthetic backdated git fixture per FD-132.
- **Decision Required:** Resolved by FD-132.

---

### `tools/records/run-dod-matrix.sh` (satisfies L4-P8-02)
> **Status (2026-10-23):** RESOLVED — see FD-133 (resolves RD-04); file exists at `tools/records/run-dod-matrix.sh`; `bash tools/records/run-dod-matrix.sh` → DOD MATRIX SUMMARY: 15 passed, 0 failed, 5 skipped (remote-required); DOD MATRIX OK (exit 0), verified 2026-10-23.
- **Pool Item:** 38 (`tools/records/run-dod-matrix.sh`)
- **Evidence:** Built to execute 15 local/in-repo DoD rows with remote-required rows explicitly reported as SKIPPED per FD-133.
- **Decision Required:** Resolved by FD-133.

---

### `tools/records/HANDOFF.md` (satisfies L4-P8-03)
> **Status (2026-10-23):** RESOLVED — see FD-134 (resolves RD-05); harmonized file exists at `tools/records/HANDOFF.md` (`metrics/HANDOFF.md` CORRECTLY NOT BUILT per FD-134; harmonized to `tools/records/` where cross-lane tooling lives), verified 2026-10-23.
- **Pool Item:** 39 (`metrics/HANDOFF.md`, harmonized to `tools/records/HANDOFF.md`)
- **Evidence:** Cross-lane handoff manifest harmonized to `tools/records/HANDOFF.md` beside the cross-lane tools it documents per FD-134.
- **Decision Required:** Resolved by FD-134.

---

## 3. Lane 5 Dual-Decomposition Blockers & Retired Task Bodies (FD-047)

**The Systemic Blocker:**
In `_FOUNDER_DECISIONS.md`, Founder Decision **FD-047** ("B1-L5 · L5 task system", decided 2026-09-03) established:
> *"Phase files (L5-01..L5-05) are authoritative. L5-06-tasks.md becomes a concordance index only; its task bodies do not execute."*

Furthermore, `lanes/L5-98-DEEP-REVIEW.md` Blocker **B-01** and **B-02** explicitly document that the task bodies in `L5-06-tasks.md` collide with the authoritative phase files (`L5-01` through `L5-05`) on file paths, directory structures, and schemas, violating `PARTITION.md` Rule 3 ("No shared mutable file, ever. No competing layouts").

All 33 remaining Lane 5 items in `pool.json` were extracted directly from the retired `L5-06-tasks.md` task bodies. Building them would duplicate and break the existing, authoritative implementations already present in the repository:

### Group A: Assisted & Credential Isolation Tasks
- **`access/tools/check_org_evidence.py` (Item 43, L5-T15):** Explicitly marked `[ASSISTED — L0 EXECUTES]`. Requires an authenticated GitHub organisation-owner console session. `L5-06-tasks.md` line 1273 states: *"A low-cost agent must not hold, be handed, or type an organisation-owner credential."*
  > **Status (2026-10-23):** CORRECTLY NOT BUILT — retired per FD-047; superseded by authoritative Phase file L5-01 (access/model/organisation.yaml); requires L0 org-owner credentials and remains out of agent scope.
- **`access/acceptance/at110_probe.py` (Item 75, L5-T56):** Explicitly marked `[ASSISTED — L0 EXECUTES]`. Requires live execution of six credential-bound attempts against protected API endpoints.
  > **Status (2026-10-23):** CORRECTLY NOT BUILT — retired per FD-047; superseded by authoritative Phase file L5-07 implementation at access/tests/at-110-reconciler-bounds.sh; live reconciler probe requires L0 human execution.

### Group B: DevLake & Ops-VM Image Lock (FD-112)
- **`ops-vm/tools/check_versions_lock.py` (Item 44, L5-T16)**
  > **Status (2026-10-23):** CORRECTLY NOT BUILT — retired per FD-047; DevLake removed from V1 stack per FD-112; remains out of scope.
- **`ops-vm/tools/render_compose.py` (Item 45, L5-T17)**
  > **Status (2026-10-23):** CORRECTLY NOT BUILT — retired per FD-047; DevLake removed from V1 stack per FD-112; remains out of scope.
- **`ops-vm/provision/provision.sh` (Item 46, L5-T18)**
  > **Status (2026-10-23):** CORRECTLY NOT BUILT — retired per FD-047; superseded by authoritative Phase file L5-04 provisioning at ops-vm/provision/30-stack-up.sh; remains out of scope.
- **Evidence:** `FD-112` ("DevLake V1: Deferred (PFD-032)") officially removed DevLake from the V1 stack. `L5-06-tasks.md` L5-T16/T17 hardcodes DevLake image locks and compose manifests. Additionally, `ops-vm/provision/` already contains the authoritative `30-stack-up.sh` from `L5-04`.

### Group C: Smoke & Deadman Divergence
- **`ops-vm/tools/post_patch_smoke.py` (Item 47, L5-T20):** Collides with the existing authoritative shell implementation at `ops-vm/checks/post-patch-smoke.sh` and `access/layer-b/check-post-patch.sh` (active in `infra/tools/readiness.sh`).
  > **Status (2026-10-23):** CORRECTLY NOT BUILT — retired per FD-047; superseded by authoritative implementations at ops-vm/checks/post-patch-smoke.sh and access/layer-b/check-post-patch.sh; remains out of scope.
- **`ops-vm/tools/deadman_heartbeat.py` (Item 48, L5-T21):** Collides with the existing authoritative implementation in `ops-vm/deadman/` and requires a live external witness identity reserved for L0.
  > **Status (2026-10-23):** CORRECTLY NOT BUILT — retired per FD-047; superseded by ops-vm/checks/deadman-heartbeat-fresh.sh; off-VM witness identity is L0-reserved.

### Group D: AI Toolchain Dual-Tree Schism (`access/ai-runtime/` vs `access/ai-toolchain/`)
> **Status (2026-10-23):** CORRECTLY NOT BUILT (Items 49–57) — retired per FD-047; superseded by authoritative Phase file L5-05 (`access/ai-toolchain/`, validated by `python access/ai-toolchain/validate_toolchain.py` → PASS 6 runtimes, exit 0, verified 2026-10-23); competing `access/ai-runtime/` layout prohibited by PARTITION Rule 3.
- **`access/ai-runtime/tools/validate_runtime_contract.py` (Item 49, L5-T24)**
- **`access/ai-runtime/tools/check_no_api_keys.py` (Item 50, L5-T25)**
- **`access/ai-runtime/tools/check_extension_pins.py` (Item 51, L5-T26)**
- **`access/ai-runtime/tools/check_constitution_reference.py` (Item 52, L5-T27)**
- **`access/ai-runtime/tools/preflight_secret_strip.py` (Item 53, L5-T28)**
- **`access/ai-runtime/tools/check_ai_restrictions.py` (Item 54, L5-T29)**
- **`access/ai-runtime/tools/eval_runner.py` (Item 55, L5-T30)**
- **`access/ai-runtime/tools/validate_benchmark_record.py` (Item 56, L5-T31)**
- **`access/ai-runtime/tools/workstation_check.sh` (Item 57, L5-T32)**
- **Evidence:** Authoritative phase file `L5-05` established and populated `access/ai-toolchain/` (validated by `infra/tools/readiness.sh` via `access/ai-toolchain/validate_toolchain.py`, with checks in `access/ai-toolchain/checks/`). Retired `L5-06` tasks prescribe an entirely parallel, incompatible directory tree under `access/ai-runtime/`. Creating `access/ai-runtime/` creates an instant architectural collision.

### Group E: Asset Inventory Tooling Divergence
> **Status (2026-10-23):** CORRECTLY NOT BUILT (Items 58–61) — retired per FD-047; superseded by authoritative Phase file L5-05 (`assets/validate_assets.py` → PASS 14 files, exit 0, and `assets/validate_deadlines.py` → PASS, exit 0, verified 2026-10-23); competing `assets/tools/` layout prohibited by PARTITION Rule 3.
- **`assets/tools/validate_inventory.py` (Item 58, L5-T33..T35)**
- **`assets/tools/deadline_watch.py` (Item 59, L5-T36)**
- **`assets/tools/vendor_deprecation_feed.py` (Item 60, L5-T37)**
- **`assets/tools/orphan_owners.py` (Item 61, L5-T38)**
- **Evidence:** Authoritative `L5-05` implemented asset validation directly at `assets/validate_assets.py` and `assets/validate_deadlines.py` (passing in `infra/tools/readiness.sh`). Retired `L5-06` mandates `assets/tools/` with a separate JSON-schema engine that contradicts existing inventory YAML fixtures (`L5-98-DEEP-REVIEW.md` Blocker B-13).

### Group F: Notification Routing Monolith vs Directory-Per-Route
> **Status (2026-10-23):** CORRECTLY NOT BUILT (Items 62–65) — retired per FD-047; superseded by authoritative Phase file L5-05 (directory-per-route `notify/routes/`, validated by `python notify/check_channels.py` → PASS, exit 0, and `python notify/check_closed_list.py` → PASS, exit 0, verified 2026-10-23); monolithic `notify/tools/` layout prohibited by PARTITION Rule 3.
- **`notify/tools/validate_notify_config.py` (Item 62, L5-T39..T40)**
- **`notify/tools/route.py` (Item 63, L5-T41)**
- **`notify/tools/check_phone_path.py` (Item 64, L5-T43)**
- **`notify/tools/check_no_paging_apps.py` (Item 65, L5-T44)**
- **Evidence:** As noted in `L5-98-DEEP-REVIEW.md` Blocker B-02 and Major M-14, `L5-06` prescribes monolithic registries (`notify/contract/push-events.yaml` and `notify/routing/channels.yaml`), which violates `PARTITION.md` Rule 3 ("directory-per-item only; no lane appends to a shared index"). Authoritative `L5-05` built the directory-per-route architecture under `notify/routes/`, validated by `notify/check_push_list.py` and `notify/check_channels.py`.

### Group G: Layer B Naming and Toolchain Divergence (`access/layer-b/` vs `access/layerb/`)
> **Status (2026-10-23):** CORRECTLY NOT BUILT (Items 66–74) — retired per FD-047; superseded by authoritative Phase file L5-03 (hyphenated `access/layer-b/` layout, e.g. `at-098-separately-credentialed.sh`, `check-access-log.sh`, `check-allowlist-parity.sh`); competing unhyphenated `access/layerb/` tools prohibited by PARTITION Rule 3.
- **`access/layerb/tools/check_separate_credential.py` (Item 66, L5-T46)**
- **`access/layerb/tools/check_no_people_datasource.py` (Item 67, L5-T47)**
- **`access/tests/test_at098.py` (Item 68, L5-T48)**
- **`access/layerb/tools/allowlist_sync.py` (Item 69, L5-T49)**
- **`access/layerb/tools/access_log.py` (Item 70, L5-T50)**
- **`access/layerb/tools/check_backup_policy.py` (Item 71, L5-T51)**
- **`access/layerb/selfview/generate_selfview.py` (Item 72, L5-T52)**
- **`access/layerb/tools/check_drill_record.py` (Item 73, L5-T54)**
- **`access/acceptance/at_runner.py` (Item 74, L5-T55)**
- **Evidence:** Authoritative `L5-03` established `access/layer-b/` (hyphenated) with shell checks (`check-access-log.sh`, `check-allowlist-parity.sh`, `check-post-patch.sh`). The retired `L5-06` tasks prescribe unhyphenated `access/layerb/tools/` with python pytest equivalents.

### Decision Required for Lane 5
In accordance with **FD-047**, the Founder / L0 Integrator has confirmed that:
1. `pool.json` items 43 through 75 are formally retired, as they derive from the superseded `L5-06-tasks.md` atomic task list.
2. The authoritative implementation of Lane 5 remains governed by the phase files (`L5-01` through `L5-05`, `L5-07`), which are 81.25% green (13/16 gates passing in `infra/tools/readiness.sh`: failing gates are `owned-roots`, `test-coverage`, `layerb-post-patch`; verified live 2026-10-24, exit 1).
3. Future Lane 5 task pools must be generated from the concordance in `lanes/L5-CONCORDANCE.md` §7.2 rather than the retired `L5-06` task bodies.
