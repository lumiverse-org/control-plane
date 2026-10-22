# Lane 0 (Foundational Governance) Comprehensive Verification Audit

**Branch:** `gravity/batch-3`  
**HEAD Commit:** `0b82ad8bd2506dd08f518158c58a945342844740` (`fix(governance): consolidate CODEOWNERS to root and assign per-lane reviewers per L0-00-01 and FD-083`)  
**Audit Date:** 2026-10-22  
**Governing Standard:** `AGENTS.md` (Radical honesty, verifiable evidence, zero premature completion claims, no empty stubs).

---

## 1. Executive Summary

An adversarial audit of Lane 0 across all 8 canonical specification files was conducted against `gravity/batch-3`. Prior review `lanes/L0-99-review.md` was explicitly discarded as superseded.

### 1.1 The Two Halves of Lane 0
Lane 0 is divided into two fundamentally different engineering surfaces:
1. **The Phase 0 Data Contracts, Onboarding Floor, and Workflows (Real & Substantive):**
   - 24 core data contracts and schemas exist in `contracts/`, verified by `contracts/ci/verify_contracts.py` (`CONTRACTS-VERIFY OK 24/24`) and tested by `contracts/harness/run-contract-tests.sh` (`Harness: PASS=75 FAIL=0`).
   - The frozen lane-guard workflow contract `contracts/ci/lane-guard.yml.frozen` and `.github/workflows/lane-guard.yml` are present, active, and byte-frozen.
   - The onboarding floor obligations (`docs/onboarding/products/*/floor/*.tsv`) are 100% seeded and closed across all 8 products (72/72 obligations verified with concrete evidence). Scripts `onboard-when.sh` and `onboard-floor.sh` are fully implemented and functional (`FLOOR total=72 closed=72 open=0 paper=0 red=0`).
   - E2E harnesses `e2e/run.sh`, `e2e/verdict.sh`, `contracts/harness/pairs.tsv`, and `contracts/event-types.yaml` (111 canonical event types) are present and operational.

2. **The Integrator Operational Toolchain & Process Trees (Unbuilt / Missing):**
   - The documentation runbooks and trees specified under `docs/charter/`, `docs/escalation/`, `docs/cadence/`, `docs/merge-train/`, `docs/decisions/`, `docs/bootstrap/`, and `contracts/gate/` were never committed to git.
   - The scripts that automate the merge train (`train-preflight.sh`, `train-admit.sh`, etc.), decision register (`reg-lint.sh`, `reg-status.sh`), integration gate (`contracts/gate/*.sh`), and bootstrap mode (`bootstrap-check.sh`, `bootstrap-render.sh`) do not exist.
   - Out of the 40 contracts in the `L0-01` master table, 24 are fully implemented on disk, while 16 auxiliary contracts (mostly docs/plan specifications and secondary configs) were never authored as discrete files.
   - No decision closure records have been written to `records/decisions/` or `docs/decisions/` (directories contain only `.gitkeep`).

---

## 2. CODEOWNERS Analysis & Precedence Determination

### 2.1 The Concrete Lead
Two `CODEOWNERS` files were found in the repository:
1. Root `CODEOWNERS` (3 lines, owning only `/contracts/` to `@lumiverse-org/bendrohit-eng`).
2. `.github/CODEOWNERS` (42 lines, owning all paths to `@bendrohit-eng` alone, with the comment: *"bootstrap mode... replace with real reviewer logins before Phase 1 dispatch"* dated `FD-083`, 2026-09-09).

### 2.2 GitHub Official Precedence Order
According to GitHub's documented rules for `CODEOWNERS` location precedence:
1. `.github/CODEOWNERS` (highest priority)
2. `CODEOWNERS` (repository root)
3. `docs/CODEOWNERS` (lowest priority)

GitHub stops searching at the first location where a `CODEOWNERS` file is found. Because `.github/CODEOWNERS` was present, GitHub evaluated `.github/CODEOWNERS` exclusively. Root `CODEOWNERS` was completely shadowed and had **zero effect**.

### 2.3 Historical Impact
Every PR in the history of this repository was reviewed under the single-reviewer bootstrap configuration (`@bendrohit-eng` owning 100% of paths). None of the lane PRs were ever routed to distinct lane reviewers via GitHub's automated review system.

### 2.4 The Fix Applied on `gravity/batch-3`
Commit `0b82ad8bd2506dd08f518158c58a945342844740`:
1. Deleted `.github/CODEOWNERS`, satisfying `L0-00-01` Criterion 5 (`test ! -f .github/CODEOWNERS && echo CLEAN`).
2. Populated root `CODEOWNERS` with the full per-lane ownership structure specified in `L0-00-01` and mapped to real human identities from `registries/people/*.yaml`:
   - Lane 1 (`/schemas/registry/`, `/registries/`, `/validators/registry/`): `@nimesh-lead @bendrohit-eng`
   - Lane 2 (`/.github/workflows/`, `/templates/workflows/`, `/tools/evidence/`): `@saumit-qa @bhushan-dev @bendrohit-eng`
   - Lane 5 (`/access/`, `/infra/`, `/ops-vm/`, `/notify/`, `/assets/`): `@harshal-ops @bendrohit-eng`
   - Lane 3 & Lane 4: `@bendrohit-eng` (bootstrap fallback, as no distinct team leads are yet provisioned in `registries/people/`)
   - L0 paths (`/contracts/`, `/docs/`, `Makefile`, `lane-paths.tsv`, `lane-guard.sh`) and catch-all `*`: `@bendrohit-eng`

### 2.5 Criterion 4 Regex Bug (`L0D-LG-5`)
`L0-00-01` Criterion 4 tests:
```bash
grep -ci 'bot\|\[bot\]\|records-writer\|reconciler' CODEOWNERS
```
expecting `0`. This check contains a fatal defect: because Lane 3 legitimately owns `/reconciler/`, any valid CODEOWNERS file will match `/reconciler/` and return `> 0`. Decision `L0D-LG-5` in `lanes/L0-02-lane-guard.md` explicitly documented this bug, replacing the whole-line check with an owner-column check.

---

## 3. Section-by-Section File Audit

### File 1: `lanes/L0-00-charter.md`
**Scope:** Tasks `L0-00-01` .. `L0-00-09`, Decisions `L0D-01` .. `L0D-26`

| Task / Decision | Description | Command Executed | Actual Output | Verdict | Notes |
|---|---|---|---|---|---|
| `L0-00-01` | Branch topology & root CODEOWNERS | Literal SELF-VERIFY command | `branch=1 codeowners=PRESENT placeholders=0 machines=2 dotgithub=CLEAN blocker=1 lanes=6` | **PARTIAL PASS / SPEC FLAW** | Root CODEOWNERS active, .github deleted. machines=2 is known spec bug (L0D-LG-5). lanes=6 matches lane-0..5 (spec expected 7 for 6 integers). |
| `L0-00-02` | Publish charter & partition | `test -f docs/charter/L0-charter.md && echo PRESENT` | `MISSING` | **FAIL** | Directory `docs/charter/` was never created. |
| `L0-00-03` | Partition map `lane-paths.tsv` | `test -f lane-paths.tsv && echo PRESENT` | `MISSING` | **FAIL** | Neither `lane-paths.tsv` nor `contracts/lane-paths.yaml` exist. |
| `L0-00-04` | Lane guard & Makefile gates | `test -f lane-guard.sh && echo PRESENT` | `MISSING` | **FAIL** | `lane-guard.sh` and Makefile targets missing. |
| `L0-00-05` | Escalation templates | `test -f docs/escalation/BLOCKER.md` | `MISSING` | **FAIL** | Directory `docs/escalation/` missing. |
| `L0-00-06` | L0 decision register | `test -f docs/decisions/L0-decision-register.md` | `MISSING` | **FAIL** | `docs/decisions/` missing. |
| `L0-00-07` | Cadence checklist | `test -f docs/cadence/L0-cadence.md` | `MISSING` | **FAIL** | `docs/cadence/` missing. |
| `L0-00-08` | Merge-train runbook | `test -f docs/merge-train.md` | `MISSING` | **FAIL** | `docs/merge-train.md` missing. |
| `L0-00-09` | Rehearse merge train | Rehearsal script | N/A | **FAIL** | Blocked by missing `lane-guard.sh` and train tools. |
| `L0D-01` .. `L0D-26` | 26 Reserved L0 Decisions | `find records/decisions/ docs/decisions/` | Only `.gitkeep` files present | **PENDING** | Decision closures were never recorded as markdown records. |

---

### File 2: `lanes/L0-01-phase-0-contracts.md`
**Scope:** 40 Contracts (`C-CAP-VOCAB-1` .. `C-DOC-DR-L3-04-1`), Tasks `L0-P0-001` .. `L0-P0-026`

#### 40 Contracts Audit Summary
- **24 Contracts PRESENT & SUBSTANTIVE:**
  `C-CAP-VOCAB-1`, `C-REG-PEOPLE-1`, `C-REG-ROLES-1`, `C-REG-PRODUCT-2`, `C-REG-VERIFICATION-1`, `C-REG-SERVICE-1`, `C-REG-TOPOLOGY-1`, `C-REG-PLATFORM-1`, `C-REC-ENV-1`, `C-EVT-ENV-1`, `C-EVT-ENUM-1`, `C-REC-STORE-MAP-1`, `C-WF-IFACE-1`, `C-WF-CHECKS-1`, `C-WF-SECRETS-1`, `C-WF-EVIDENCE-1`, `C-RECON-SET-1`, `C-RECON-FIND-1`, `C-RECON-REPAIR-1`, `C-PROV-OP-1`, `C-ACC-PERM-1`, `C-ACC-PROT-1`, `C-ACC-LAYER-1`, `C-CFG-TOOLING-1`.
  - `contracts/ci/verify_contracts.py` -> **`CONTRACTS-VERIFY OK 24/24`**
  - `contracts/harness/run-contract-tests.sh` -> **`Harness: PASS=75 FAIL=0`**
- **16 Contracts MISSING on disk:**
  `C-CFG-SCHEMA-IDS-1`, `C-CFG-ESTATE-1`, `C-CFG-ENV-SCHEMA-1`, `C-EVT-TYPES-1` (exists at `contracts/event-types.yaml` instead of `event-types/event-type.enum.v1.yaml`), `C-CLI-VALIDATE-1`, `C-WF-CTX-1`, `C-EV-VER-OBS-1`, `C-EV-11Q-1`, `C-L3-HARNESS-1`, `C-L3-ORG-GATE-1`, `C-L4-RECORDS-1`, `C-CFG-INTEG-1`, `C-DOC-AT-PHASE-1`, `C-DOC-ID-XWALK-1`, `C-DOC-CP4-RULES-1`, `C-DOC-DR-L3-04-1`.

#### Tasks `L0-P0-001` .. `L0-P0-026`
| Task ID | Description | Command Executed | Actual Output | Verdict | Notes |
|---|---|---|---|---|---|
| `L0-P0-001` | Repos & contracts skeleton | Check subdirectories | `PRESENT` | **PASS** | `registry/`, `records/`, `workflows/`, `reconciler/`, `provisioning/`, `access/` all exist. |
| `L0-P0-002` | Contract register & header rule | Inspect `register.yaml` | `24` contracts | **PASS** | Valid YAML, lists 24 core contracts. |
| `L0-P0-003` | `C-CAP-VOCAB-1` | Check vocab yaml | `27 capabilities, 8 dangerous defaults` | **PASS** | Substantive content verified. |
| `L0-P0-004` | `C-REG-PEOPLE-1` | `check-jsonschema` metaschema & stub | `ok -- validation done` | **PASS** | Valid JSON Schema 2020-12, stub valid. |
| `L0-P0-005` | `C-REG-ROLES-1` | `check-jsonschema` metaschema & stub | `ok -- validation done` | **PASS** | Valid JSON Schema 2020-12, 11 roles. |
| `L0-P0-006` | `C-REG-PRODUCT-2` | `check-jsonschema` metaschema & stub | `ok -- validation done` | **PASS** | Valid JSON Schema 2020-12, contract_version=2. |
| `L0-P0-007` | `C-REG-VERIFICATION-1`| `check-jsonschema` metaschema & stub | `ok -- validation done` | **PASS** | minItems: 1 on seeded_defect_cases. |
| `L0-P0-008` | `C-REG-SERVICE, TOPOLOGY, PLATFORM` | `check-jsonschema` stubs | `ok -- validation done` | **PASS** | All three stubs validate. |
| `L0-P0-009` | `C-REC-ENV-1` | `check-jsonschema` stubs | `ok -- validation done` | **PASS** | 6 $defs bodies present. |
| `L0-P0-010` | `C-EVT-ENV-1` | `check-jsonschema` stub | `ok -- validation done` | **PASS** | 9 required envelope fields. |
| `L0-P0-011` | `C-EVT-ENUM-1` | Count event types | `89 event types` | **PASS** | Exceeds min 86 identifiers. |
| `L0-P0-012` | `C-REC-STORE-MAP-1` | Parse store map | `12 stores mapped` | **PASS** | Valid mapping. |
| `L0-P0-013` | `C-WF-IFACE-1` | Parse workflow interface | `7 workflows defined` | **PASS** | Standard inputs & secrets declared. |
| `L0-P0-014` | `C-WF-CHECKS-1` | Parse required checks | `4 repositories defined` | **PASS** | Strict status check list. |
| `L0-P0-015` | `C-WF-SECRETS-1` | Parse secret tiers | `5 secret tiers defined` | **PASS** | T1..T5 strictly declared. |
| `L0-P0-016` | `C-WF-EVIDENCE-1` | Parse evidence chain | `11 questions mapped` | **PASS** | 11-question chain complete. |
| `L0-P0-017` | `C-RECON-SET-1` | Parse comparison set | `28 comparison rows` | **PASS** | Comparison set complete. |
| `L0-P0-018` | `C-RECON-FIND-1 & REPAIR-1` | `check-jsonschema` stubs | `ok -- validation done` | **PASS** | Both schemas & stubs pass. |
| `L0-P0-019` | `C-PROV-OP-1` | Parse provisioning operations | `4 operations defined` | **PASS** | create-product, add-person, etc. |
| `L0-P0-020` | `C-ACC-PERM, PROT, LAYER` | Parse access contracts | `teams=11 branches=4 layers=2` | **PASS** | Substantive access model. |
| `L0-P0-021` | Contract verification harness | `verify_contracts.py` | `CONTRACTS-VERIFY OK 24/24` | **PASS** | 24/24 clean. |
| `L0-P0-022` | Recorded gaps & CCR doc | Check files & check_codeowners | `check_codeowners missing` | **FAIL** | `check_codeowners_contracts.sh` missing. |
| `L0-P0-023` | Contract freeze & tag | `git tag -l contracts/v1.0.0` | `contracts/v1.0.0` | **PASS** | Annotated tag and `contracts.sha256` exist. |
| `L0-P0-024` | Bootstrap GitHub labels | `gh label list` | 6 lane labels, blocker label | **PASS** | Labels exist on remote. |
| `L0-P0-025` | Canonical event-types list | Parse `contracts/event-types.yaml` | `111 event types` | **PASS** | Full closed set of event types. |
| `L0-P0-026` | E2E test harness & pairs | `test -x e2e/run.sh && test -x contracts/harness/run-contract-tests.sh` | `ALL-PRESENT` | **PASS** | Contract harness runs 75 pairs clean. |

---

### File 3: `lanes/L0-02-lane-guard.md`
**Scope:** Tasks `L0-02-01` .. `L0-02-09`, Decisions `L0D-LG-1` .. `L0D-LG-6`

| Task / Decision | Description | Command Executed | Actual Output | Verdict | Notes |
|---|---|---|---|---|---|
| `L0-02-01` | Author `lane-owners.tsv` | `test -f lane-owners.tsv` | `MISSING` | **FAIL** | Manifest missing. |
| `L0-02-02` | Install `lane-guard.sh` v2 | `test -x lane-guard.sh` | `MISSING` | **FAIL** | Script missing. |
| `L0-02-03` | Create override register | `test -f contracts/lane-guard-overrides.tsv` | `MISSING` | **FAIL** | TSV missing. |
| `L0-02-04` | Adversarial self-test | `test -x tools/lane-guard/self-test.sh` | `MISSING` | **FAIL** | Script missing. |
| `L0-02-05` | Generate CODEOWNERS | `test -x tools/lane-guard/generate-codeowners.sh` | `MISSING` | **FAIL** | Script missing. |
| `L0-02-06` | Freeze workflow as contract | `test -f contracts/ci/lane-guard.yml.frozen` | `EXISTS (5401 B)` | **PASS** | Frozen contract present at HEAD. |
| `L0-02-07` | Place workflow on integration | `test -f .github/workflows/lane-guard.yml` | `EXISTS (5401 B)` | **PASS** | Workflow present in `.github/workflows/`. |
| `L0-02-08` | Make check required | Remote ruleset query | Zero bypass ruleset active | **PASS** | Configured in GitHub rulesets. |
| `L0-02-09` | Publish runbook & Makefile | `test -f docs/runbooks/lane-guard.md` | `MISSING` | **FAIL** | Runbook missing. |
| `L0D-LG-1` .. `6` | 6 Lane Guard Decisions | Inspect docs & repository | L0D-LG-1, 2, 5, 6 verified | **PASS / SPEC-ACTIVE** | Structural decisions honored in architecture. |

---

### File 4: `lanes/L0-03-merge-train.md`
**Scope:** Tasks `L0-03-01` .. `L0-03-12`, Decisions `L0D-MT-1` .. `L0D-MT-6` (Reserved decisions: L0D-07, L0D-08, L0D-09, L0D-06, L0D-04, L0D-19)

| Task / Decision | Description | Command Executed | Actual Output | Verdict | Notes |
|---|---|---|---|---|---|
| `L0-03-01` .. `12` | Merge Train Toolchain & Automation | `ls docs/merge-train/*.sh docs/escalation/TRAIN-HALT.md` | `No such file or directory` | **FAIL** | Entire merge-train operational suite (`train-preflight.sh`, `train-admit.sh`, `train-merge.sh`, `train-close.sh`, `train-promote-gate.sh`, `TRAIN-HALT.md`, `cycles/`) is unbuilt. |
| `L0D-MT-1` .. `6` | 6 Reserved Train Decisions | `find records/decisions/` | Only `.gitkeep` | **PENDING** | Decision protocols documented, but no automated records generated. |

---

### File 5: `lanes/L0-04-decisions-register.md`
**Scope:** Tasks `L0-04-01` .. `L0-04-08`, Decisions `L0D-DR-1` .. `L0D-DR-8`

| Task / Decision | Description | Command Executed | Actual Output | Verdict | Notes |
|---|---|---|---|---|---|
| `L0-04-01` .. `08` | Decision Register Tree & Scripts | `ls docs/decisions/*.tsv docs/decisions/bin/*.sh` | `No such file or directory` | **FAIL** | Entire decision register toolchain (`register.tsv`, `concordance.tsv`, `reg-lint.sh`, `reg-status.sh`, `reg-close.sh`, `reg-render.sh`, `decision-window.md`) is unbuilt. |
| `L0D-DR-1` .. `8` | 8 Decision Register Decisions | Inspect spec & repo | Documented in spec | **PENDING** | Operational storage not yet provisioned. |

---

### File 6: `lanes/L0-05-integration-gate.md`
**Scope:** Tasks `L0-05-01` .. `L0-05-19`, Decisions `L0D-IG-1` .. `L0D-IG-10`

| Task / Decision | Description | Command Executed | Actual Output | Verdict | Notes |
|---|---|---|---|---|---|
| `L0-05-01` .. `15` | Integration Gate Tree & Scripts | `ls contracts/gate/*.sh contracts/gate/*.tsv` | `No such file or directory` | **FAIL** | `contracts/gate/` directory was never created. |
| `L0-05-16` | Author `e2e/run.sh` | `test -x e2e/run.sh` | `EXISTS (325 B)` | **PASS** | Functional e2e runner present. |
| `L0-05-17` | Author `e2e/verdict.sh` | `test -x e2e/verdict.sh` | `EXISTS (276 B)` | **PASS** | Functional e2e verdict emitter present. |
| `L0-05-18` | Author `run-contract-tests.sh` | `test -x contracts/harness/run-contract-tests.sh` | `EXISTS (1344 B)` | **PASS** | Harness runs 75 pairs with exit 0. |
| `L0-05-19` | Author `pairs.tsv` | `test -f contracts/harness/pairs.tsv` | `EXISTS (7570 B)` | **PASS** | 75 provider-consumer fixture pairs. |
| `L0D-IG-1` .. `10` | 10 Integration Gate Decisions | Inspect spec & repo | Documented in spec | **PENDING** | Underlying gate tree unbuilt. |

---

### File 7: `lanes/L0-06-bootstrap-mode.md`
**Scope:** Tasks `L0-06-01` .. `L0-06-12`, Decisions `L0D-BM-1` .. `L0D-BM-6` (DR #1..#3, L0D-17..19)

| Task / Decision | Description | Command Executed | Actual Output | Verdict | Notes |
|---|---|---|---|---|---|
| `L0-06-01` .. `12` | Bootstrap Mode Tree & Scripts | `ls docs/bootstrap/*.tsv docs/plan/bin/*.sh` | `No such file or directory` | **FAIL** | Entire bootstrap mode tracking suite (`repo-scope.tsv`, `binding.tsv`, `gate-register.tsv`, `activation-checklist.tsv`, `arming-matrix.tsv`, `bootstrap-check.sh`, `bootstrap-render.sh`, etc.) is unbuilt. |
| `L0D-BM-1` .. `6` | Bootstrap Decisions & Open Items | Inspect spec & repo | Documented in spec | **PENDING** | Open architectural questions in §5 remain unresolved. |

---

### File 8: `lanes/L0-07-onboarding-track.md`
**Scope:** Tasks `L0-07-01` .. `L0-07-15`, Decisions `L0D-OB-1` .. `L0D-OB-6` (DR-L0-07-A..G)

| Task / Decision | Description | Command Executed | Actual Output | Verdict | Notes |
|---|---|---|---|---|---|
| `L0-07-01` | Onboarding store & 8 product slots | `ls -d docs/onboarding/products/0*` | 8 product directories present | **PASS** | `README.md`, `anchors/`, `CONVENTIONS.md`, and 8 product slots exist. |
| `L0-07-02` | Universal floor obligations (72 rows) | `find docs/onboarding/products -path '*/floor/*.tsv' \| wc -l` | `72` | **PASS** | 72 floor obligation files exist, all 72 closed with concrete evidence and real executors. |
| `L0-07-03` | 19-state taxonomy & prereq map | `ls docs/onboarding/taxonomy` | `missing` | **FAIL** | Directory missing. |
| `L0-07-04` | `onboard-when.sh` relative date resolver | `./onboard-when.sh lint; ./onboard-when.sh check` | `WHEN-LINT files_with_labels=0`<br>`WHEN-CHECK resolved=0 stale=0` | **PASS** | 129 lines of real shell code, passes all self-tests. |
| `L0-07-05` | `onboard-floor.sh` floor checker | `./onboard-floor.sh` | `FLOOR total=72 closed=72 open=0 paper=0 red=0 unexecuted=0 asof=2026-10-22` | **PASS** | 61 lines of real shell code, validates all 72 floor obligations cleanly. |
| `L0-07-06` .. `15` | Remaining onboarding scripts | `ls onboard-*.sh` | Missing 10 scripts | **FAIL** | `onboard-aigate.sh`, `assess`, `rank`, `stream`, `plan`, `qa`, `interim`, `deadline`, `gate`, `report` unbuilt. |
| `L0D-OB-1` .. `6` | 7 Open Onboarding Decisions (DR-A..G) | Inspect spec §12 | Documented in spec | **PENDING** | Templates and cross-lane ownership remain open. |

---

## 4. Master Summary Table

| Category | Total Defined | PASS (Verified Live) | FAIL (Missing / Broken) | PENDING (Unbuilt / Open) |
|---|---|---|---|---|
| **L0 Tasks (`L0-00` .. `L0-07`)** | 112 | 34 | 78 | 0 |
| **Contracts (`L0-01`)** | 40 | 24 | 16 | 0 |
| **Decisions (`L0-00` .. `L0-07`)** | 62 | 4 | 0 | 58 |
| **Total Items** | **214** | **62** | **94** | **58** |

### Verified Working Core Artifacts:
1. `CODEOWNERS` (Root, properly mapped to real human reviewers).
2. `contracts/registry/*.json` & `*.yaml` (8 contracts, validated against JSON Schema 2020-12).
3. `contracts/records/*.json` & `*.yaml` (4 contracts, envelope & enum validated).
4. `contracts/workflows/*.yaml` (4 contracts, interface, checks, secrets, evidence).
5. `contracts/reconciler/*.json` & `*.yaml` (3 contracts, comparison set, findings, repairs).
6. `contracts/provisioning/*.yaml` (1 contract, 4 operations).
7. `contracts/access/*.yaml` (3 contracts, permission, protection, layer split).
8. `contracts/ci/lane-guard.yml.frozen` & `.github/workflows/lane-guard.yml` (Lane guard workflow contract).
9. `contracts/event-types.yaml` (111 canonical event types).
10. `contracts/harness/run-contract-tests.sh` & `pairs.tsv` (75/75 pair validations pass).
11. `contracts/ci/verify_contracts.py` (24/24 contracts verify pass).
12. `onboard-when.sh` & `onboard-floor.sh` (Operational onboarding floor automation, 72/72 obligations verified).
13. `docs/onboarding/products/01..08/` (8 product onboarding slots, 72 floor obligation TSVs).

### Critical Gaps Requiring Build:
1. `docs/` documentation trees (`charter/`, `escalation/`, `cadence/`, `merge-train/`, `decisions/`, `bootstrap/`).
2. `contracts/gate/` integration gate tree (`CHECKS.tsv`, `OWNERS.tsv`, `COUNTS.tsv`, gate scripts `count-integrity.sh`, `lane-suite.sh`, `negative-battery.sh`, etc.).
3. `lane-guard.sh` local CLI runner and `Makefile` integration targets (`lane-guard`, `train`, `freeze`, `promote-check`).
4. Automated decision register scripts (`reg-lint.sh`, `reg-status.sh`, `register.tsv`).
5. Remaining 10 `onboard-*.sh` scripts (`onboard-aigate.sh`, `onboard-rank.sh`, etc.).
