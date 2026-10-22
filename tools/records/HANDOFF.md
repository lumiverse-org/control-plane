# Lane 4 (Records, Events & Metrics) — Cross-Lane Handoff Manifest

**Path:** `tools/records/HANDOFF.md`  
**Lane:** L4 (Records, Events & Metrics — Subsystems I, N)  
**Charter Authority:** `lanes/L4-00-charter.md` §5  
**Governing Decisions:** FD-065, FD-131, FD-132, FD-133, FD-134 (path harmonized to `tools/records/HANDOFF.md`)  
**Spec References:** Master Spec v4.0 §97, §40.1, §53.1, §103  

---

## 1. Published Artifacts Consumed by Lane 0 (Governance, Foundations & Gates)

Lane 0 consumes the schema contracts, taxonomy, and gate validation tooling to prove platform-wide invariants:

| Published Artifact | Path | Lane 0 Consumption Purpose |
|---|---|---|
| Record Schemas & Base Defs | `schemas/records/**` | Master contract for all 19 record stores of §97.2, including `record.base.schema.json` ($defs), `record.envelope.schema.json`, and individual store schemas (`deployment.schema.json`, `incident.schema.json`, etc.). |
| Event Envelope Schema | `schemas/records/event.envelope.schema.json` | The universal 9-field event envelope enforced on every machine and human event. |
| Schema Gate Validator | `tools/records/validate-schemas.sh` | Execution tool proving schema syntax, required envelope fields, UTC offsets, and negative rejection batteries (Charter DoD-2, DoD-3, DoD-10, DoD-18). |
| Write-Freshness Declarations | `metrics/freshness/write-freshness.yaml` | Declared maximum inter-write interval windows for all stores, establishing the 3 mandatory Blocking stores (`events/`, `records/deployments/`, `records/uat/`). |
| Freshness Validators | `tools/records/validate-freshness.sh`, `tools/records/test-freshness-e2e.sh` | Proves write-freshness declarations and offline end-to-end commit cadence with synthetic git fixtures (DoD-5, FD-132). |
| Retention Declarations | `metrics/retention/retention-classes.yaml`, `tools/records/validate-retention.sh` | Declares store retention classes and proves immutability and retention boundaries (DoD-19). |
| Charter DoD Matrix | `tools/records/run-dod-matrix.sh` | Proves all 20 charter Definition-of-Done rows across the lane (DoD-1..DoD-20, FD-133). |

---

## 2. Published Artifacts Consumed by Lane 1 (Schemas, Registries & Contracts)

Lane 1 consumes L4 taxonomy and metric declarations to embed them into canonical registers:

| Published Artifact | Path | Lane 1 Consumption Purpose |
|---|---|---|
| Event Types Taxonomy | `metrics/taxonomy/event-types.yaml` | The closed 86-identifier taxonomy of §97.3 lines 8944–8963. L1 embeds this list into `registries/platform.yaml` beside supported contract versions (FD-065). |
| Metric Declarations | `metrics/register/metric-declarations.yaml` | Declarations for all OS health measures, time windows, and attribution rules. L1 embeds these definitions into `registries/os-health.yaml`. |
| Signal Source Map | `metrics/signals/sig-source-map.yaml` | Normative mapping resolving §52.2 signal identifiers (SIG-06, SIG-17, SIG-41, SIG-42, SIG-46) to corresponding L4 record stores and L1 event types (FD-065). |
| Source Validation Tool | `metrics/register/validate-sources.sh` | Tooling proving metric store linkage, arming discipline (D77), and baseline integrity (AT-046) (DoD-13, DoD-14, DoD-15). |

---

## 3. Published Artifacts Consumed by Lane 2 (Pipeline, Reusable Workflows & Evidence)

Lane 2 merges after Lane 4 and consumes the writer tooling, handler dispatch, and deployment record shapes:

| Published Artifact | Path | Lane 2 Consumption Purpose |
|---|---|---|
| Record Writer CLI & Library | `tools/records/record-write`, `tools/records/record_write.py` | Python stdlib writer CLI invoked by `.github/workflows/deploy-production.yml` and other workflow jobs as a **required, failing step** (§97.2 line 8867, FD-131). |
| Event Appender CLI & Library | `tools/records/event-append`, `tools/records/event_append.py` | Python stdlib event appender invoked on deployment runs to append validated events to `events/<YYYY-MM-DD>/` (FD-131). |
| RECORD-VERIFICATION-RESULT Handler | `tools/records/record-verification-result`, `tools/records/rvr.py` | The single handler executed by `.github/workflows/record-verification-result.yml` to ingest manual UAT results and restore-test confirmations (§97.2 line 8871, FD-131). |
| Deployment Record Schema | `schemas/records/deployment.schema.json` | Binding schema shape that `deploy-production.yml` must emit to satisfy the §32 Production Evidence Chain. |
| UAT Record Schema | `schemas/records/uat.schema.json` | Schema shape emitted on `verification/uat.md` test run completions. |
| Operational Store Schemas | `schemas/records/{restore-test, eval, launch, security-review, deletion-request}.schema.json` | Shapes for restore testing, AI eval regression runners (SIG-42), launch packs, and deletion runbooks (AT-105). |
| Test Fixture Corpora | `tools/records/fixtures/**` | Golden valid and negative fixture corpora enabling Lane 2 CI workflows to test record emission offline without branch dependencies. |

---

## 4. Published Artifacts Consumed by Lane 3 (Reconciler, Provisioning & Automation)

Lane 3 consumes drift comparison baselines, head anchors, and fail-closed reader tooling:

| Published Artifact | Path | Lane 3 Consumption Purpose |
|---|---|---|
| Write-Freshness Windows | `metrics/freshness/write-freshness.yaml` | Supplies the left-hand comparison baseline for §53.1 drift reconciliation: comparing newest commit timestamps on store paths against declared max intervals (Blocking on `events/`, `records/deployments/`, `records/uat/`). |
| Records Head-SHA Anchor Schema | `metrics/anchor/records-head-anchor.schema.json` | Defines the D107 anchor schema format recorded by the reconciler into the control-plane repository during each reconciliation cycle. |
| Restore-Test Schema & Cadence | `schemas/records/restore-test.schema.json` | Supplies schema and validity criteria for the §53.1 drift check comparing `product.yaml` `restore_tested` against passing records in `records/restore-tests/`. |
| Signal Derivation Map | `metrics/signals/sig-source-map.yaml` | Informs reconciler drift monitors which record stores supply source telemetry for SIG alerts. |
| Fail-Closed Reader | `tools/records/read-across`, `tools/records/read_across.py` | Cross-repository reader implementing §40.1 line 3671 fail-closed behavior (exiting non-zero on unreachable records repository rather than reporting false zeros). |
