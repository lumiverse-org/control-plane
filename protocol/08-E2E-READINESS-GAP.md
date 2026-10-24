# Protocol 08: Smoke & E2E Readiness Gap Inventory

**Canonical Spec:** `protocol/08-smoke-and-e2e.md` (1,256 lines)  
**Generated:** 2026-10-24  
**Discipline:** AGENTS.md Zero-Hallucination Anti-Green-Checkmark Standard

---

## 1. Executive Summary

- **Total Positive Checkpoints Evaluated:** 122 instances across E2E-00 through E2E-13 (satisfying the 118-checkpoint minimum floor).
- **Total Negative Gate Tests Evaluated:** 29 instances (NEG-01 through NEG-28 plus NEG-18b restore assertion; satisfying the 28-gate minimum floor).
- **Current Preflight (E2E-00) Status:** 3 PASS (CP-0001, CP-0002, CP-0003), 3 FAIL (CP-0004 unpinned tags consumed, CP-0005 outside core hours / weekend, CP-0006 missing jq/yq on operator runner).
- **Actor Constraint (STOP Rule S-01):** Active GitHub organization (`lumiverse-org`) holds **2 members** (`bendrohit-eng`, `pbhayashri`), failing the minimum 3-human Write requirement for armed gate independence.
- **Harness Scaffolding Completed:** 100% of canonical files transcribed and syntax-validated (`e2e/lib/checkpoint.sh`, `e2e/run.sh`, `e2e/verdict.sh`, 14 stage scripts, 28 negative scripts, fixtures).

| Category | Buildable Now, Offline | Genuinely Blocked on Live Infrastructure | Total |
|---|---|---|---|
| **Positive Checkpoints (E2E-00 .. E2E-13)** | 29 | 103 | 132 |
| **Negative Gate Tests (NEG-01 .. NEG-28)** | 13 | 16 | 29 |
| **Combined Total** | **42** | **119** | **161** |

---

## 2. Checkpoint-by-Checkpoint Readiness Inventory (E2E-00 through E2E-13)

| Checkpoint ID | Description | Required Tool / Command | Tool Exists? | Readiness Classification | Owning Lane (§8.3) | Blocking Dependency / Rationale |
|---|---|---|---|---|---|---|
| `CP-0001` | HEAD is the tip of integration | `git` | **EXISTS** | `BUILDABLE NOW, OFFLINE` | **L0** | Git repo inspection |
| `CP-0002` | Operator environment is API-key-free | `env / grep` | **EXISTS** | `BUILDABLE NOW, OFFLINE` | **L0** | Local environment check |
| `CP-0003` | Pilot product absent before the run | `gh` | **EXISTS** | `BUILDABLE NOW, OFFLINE` | **L0** | First-run conditional check |
| `CP-0004` | Consumed workflow tags match platform.yaml pins | `tools/verify-workflow-tag-pins.sh` | **EXISTS** | `BUILDABLE NOW, OFFLINE` | **L0** | Offline static YAML & pin audit |
| `CP-0005` | Run window admits a compliant production deploy | `tools/freeze-window-check.sh` | **EXISTS** | `BUILDABLE NOW, OFFLINE` | **L0** | Offline calendar logic (§34.2) |
| `CP-0006` | Required tools present (gh, jq, yq mikefarah, curl, base64, git) | `gh, jq, yq, curl, base64, git` | **EXISTS (gh,curl,base64,git) / MISSING (jq,yq)** | `BUILDABLE NOW, OFFLINE` | **L0** | CLI tool presence check on operator runner |
| `CP-0101` | create-product completes | `tools/provision/create-product` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires live GitHub organization API to provision repo org/pilot-one-api |
| `CP-0102-setup` | Makefile exposes setup | `gh` | **EXISTS** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires real org/pilot-one-api repo contents on GitHub |
| `CP-0102-dev` | Makefile exposes dev | `gh` | **EXISTS** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires real org/pilot-one-api repo contents on GitHub |
| `CP-0102-test` | Makefile exposes test | `gh` | **EXISTS** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires real org/pilot-one-api repo contents on GitHub |
| `CP-0102-uat-local` | Makefile exposes uat-local | `gh` | **EXISTS** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires real org/pilot-one-api repo contents on GitHub |
| `CP-0102-migrate` | Makefile exposes migrate | `gh` | **EXISTS** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires real org/pilot-one-api repo contents on GitHub |
| `CP-0102-reset` | Makefile exposes reset | `gh` | **EXISTS** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires real org/pilot-one-api repo contents on GitHub |
| `CP-0102-health` | Makefile exposes health | `gh` | **EXISTS** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires real org/pilot-one-api repo contents on GitHub |
| `CP-0102-parity` | Makefile exposes parity | `gh` | **EXISTS** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires real org/pilot-one-api repo contents on GitHub |
| `CP-0103` | Required repository files present | `tools/provision/check-required-files` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires scaffolded org/pilot-one-api repository |
| `CP-0104-ci` | ci.yml generated and tag-pinned | `gh` | **EXISTS** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires scaffolded org/pilot-one-api repository on GitHub |
| `CP-0104-build` | build.yml generated and tag-pinned | `gh` | **EXISTS** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires scaffolded org/pilot-one-api repository on GitHub |
| `CP-0104-deploy-staging` | deploy-staging.yml generated and tag-pinned | `gh` | **EXISTS** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires scaffolded org/pilot-one-api repository on GitHub |
| `CP-0104-deploy-production` | deploy-production.yml generated and tag-pinned | `gh` | **EXISTS** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires scaffolded org/pilot-one-api repository on GitHub |
| `CP-0104-migrate` | migrate.yml generated and tag-pinned | `gh` | **EXISTS** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires scaffolded org/pilot-one-api repository on GitHub |
| `CP-0104-restore-test` | restore-test.yml generated and tag-pinned | `gh` | **EXISTS** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires scaffolded org/pilot-one-api repository on GitHub |
| `CP-0104-restore-production` | restore-production.yml generated and tag-pinned | `gh` | **EXISTS** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires scaffolded org/pilot-one-api repository on GitHub |
| `CP-0105` | Third-party actions pinned to 40-char SHA | `tools/verify-action-pins.sh` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires scaffolded org/pilot-one-api repository |
| `CP-0106` | Staging/prod restricted to default branch and protected tags | `tools/provision/check-environment-policy` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L5** | Requires GitHub Environment protection rules on org/pilot-one-api |
| `CP-0107` | Branch protection matches template | `tools/provision/diff-branch-protection` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L5** | Requires GitHub Branch Protection on org/pilot-one-api |
| `CP-0108-portfolio-board` | pilot-one discoverable on portfolio-board | `tools/verify-surface-enumeration.sh` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires live portfolio board infrastructure |
| `CP-0108-grafana` | pilot-one discoverable on grafana | `tools/verify-surface-enumeration.sh` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires live Grafana instance |
| `CP-0108-scorecard` | pilot-one discoverable on scorecard | `tools/verify-surface-enumeration.sh` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires live scorecard dashboard |
| `CP-0108-devlake` | pilot-one discoverable on devlake | `tools/verify-surface-enumeration.sh` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires live DevLake instance |
| `CP-0108-reviewer-matrix` | pilot-one discoverable on reviewer-matrix | `tools/verify-surface-enumeration.sh` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires live reviewer matrix surface |
| `CP-0108-dependency-graph` | pilot-one discoverable on dependency-graph | `tools/verify-surface-enumeration.sh` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires live dependency graph surface |
| `CP-0109` | No hard-coded product list anywhere | `tools/verify-no-product-list.sh` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L3** | Static regex scan across dashboards, workflows, tools, templates |
| `CP-0110` | CONFIGURE checklist and channel/mailbox steps emitted | `tools/provision/check-scaffold-issues` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires GitHub Issues on org/pilot-one-api |
| `CP-0201` | Assignments merged to the registry | `tools/provision/apply-assignments` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L3** | Local YAML edit tool for products/pilot-one/product.yaml |
| `CP-0202` | Reconciliation run applies declared state | `gh workflow run reconcile.yml` | **EXISTS (gh)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires live GitHub Actions workflow runner in control-plane |
| `CP-0203` | CODEOWNERS generated from assignments, no machine identity | `tools/provision/verify-codeowners` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires live org/pilot-one-api CODEOWNERS file |
| `CP-0204` | GitHub Team membership matches product.yaml assignments | `tools/provision/diff-team-membership` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires live GitHub Teams in lumiverse-org |
| `CP-0205` | Zero blocking orphans on pilot-one | `reconciler/orphan-report` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L3** | Offline referential integrity check against product.yaml |
| `CP-0206` | cross_reviewer holds Write | `tools/provision/check-permission` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L5** | Requires real GitHub repository collaborator permissions check |
| `CP-0301` | verification/contract.yaml present and schema-valid | `validators/registry/validate-verification-contract` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L1** | Offline JSON schema validation of verification contract |
| `CP-0302` | Performance mechanism declared | `gh api / yq` | **EXISTS (gh) / MISSING (yq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L1** | Requires live org/pilot-one-api repo on GitHub |
| `CP-0303` | Seeded-defect case declared in contract.yaml | `gh api / yq` | **EXISTS (gh) / MISSING (yq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L1** | Requires live org/pilot-one-api repo on GitHub |
| `CP-0304` | Verification contract rejects its seeded defect | `tools/evidence/run-verification-contract` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires cloned pilot repo and test runner execution |
| `CP-0305` | Verification contract passes on the clean tree | `tools/evidence/run-verification-contract` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires cloned pilot repo and test runner execution |
| `CP-0306` | Coverage map resolves every requirement to a check | `tools/evidence/check-coverage-map` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L1** | Offline mapping comparison between requirements and tests |
| `CP-0401` | Plan submitted as a plan-approval request | `tools/gate1/submit-plan` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L0** | Gate 1 plan submission CLI / record generator |
| `CP-0402` | Plan-checker accepts a well-formed plan | `tools/gate1/plan-check` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L0** | Static plan markdown parser and rule checker (§30.2) |
| `CP-0403` | Approver resolved from capability and notified | `tools/gate1/verify-notification` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires live notification mechanism (push/webhook/email) |
| `CP-0404` | Gate 1 approved by lead-1 | `tools/gate1/approve` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires distinct lead-1 authenticated identity (§2.2, S-01) |
| `CP-0405` | plan_approved event written with envelope and agent_authored flag | `tools/records/find-event` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L4** | Offline event log search in records store |
| `CP-0406` | Computed requirement set rendered on Gate 1 surface | `tools/gate1/verify-requirement-set` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires live Gate 1 rendering surface |
| `CP-0501` | Branch pushed and PR opened by dev-a | `tools/e2e-drive/open-pr` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live org/pilot-one-api repo and dev-a identity |
| `CP-0502` | No required check reports skipped or neutral | `tools/evidence/check-conclusions` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires real PR check runs on GitHub Actions |
| `CP-0503-unit` | CI job unit concluded success | `tools/evidence/check-job` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live CI runner execution on GitHub Actions |
| `CP-0503-integration` | CI job integration concluded success | `tools/evidence/check-job` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live CI runner execution on GitHub Actions |
| `CP-0503-build` | CI job build concluded success | `tools/evidence/check-job` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live CI runner execution on GitHub Actions |
| `CP-0503-security-scan` | CI job security-scan concluded success | `tools/evidence/check-job` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live CI runner execution on GitHub Actions |
| `CP-0503-licence-scan` | CI job licence-scan concluded success | `tools/evidence/check-job` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live CI runner execution on GitHub Actions |
| `CP-0503-contract-validation` | CI job contract-validation concluded success | `tools/evidence/check-job` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live CI runner execution on GitHub Actions |
| `CP-0503-registry-validation` | CI job registry-validation concluded success | `tools/evidence/check-job` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live CI runner execution on GitHub Actions |
| `CP-0503-parity` | CI job parity concluded success | `tools/evidence/check-job` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live CI runner execution on GitHub Actions |
| `CP-0503-verification-contract` | CI job verification-contract concluded success | `tools/evidence/check-job` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live CI runner execution on GitHub Actions |
| `CP-0504` | Environment parity clean | `tools/evidence/check-job` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live CI parity check result |
| `CP-0505` | Gate 2 approved by independent reviewer dev-b | `tools/e2e-drive/approve-pr` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires distinct real reviewer identity dev-b on GitHub |
| `CP-0506` | gate_2_approval event carries reviewer role | `tools/records/find-event` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L4** | Offline event search in records store |
| `CP-0507` | Merge succeeds once protection is satisfied | `tools/e2e-drive/merge-pr` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires real PR merge on GitHub |
| `CP-0601` | Build workflow produced an artifact | `tools/e2e-drive/wait-workflow` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live GitHub Actions build workflow run |
| `CP-0602` | Digest recorded and well-formed | `tools/evidence/read-digest` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live artifact digest from build run |
| `CP-0603` | SBOM recorded beside the digest | `tools/evidence/check-sbom` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live SBOM artifact generation |
| `CP-0604` | artifact_built event carries the digest | `tools/records/find-event` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L4** | Offline event search in records store |
| `CP-0605` | Registry refuses to overwrite pushed digest tag | `tools/e2e-drive/attempt-tag-overwrite` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live OCI registry (ghcr.io) tag immutability check |
| `CP-0701` | Migration applied through CI, not by hand | `tools/e2e-drive/run-workflow` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live staging database and migration workflow |
| `CP-0702` | Previous digest runs against new schema | `tools/e2e-drive/compat-probe` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live staging environment backward compatibility test |
| `CP-0703` | Staging deploy succeeded with built digest | `tools/e2e-drive/run-workflow` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live staging deployment pipeline |
| `CP-0704` | Staging /version equals built digest | `tools/evidence/read-version` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires running staging service at https://pilot-one.staging.internal |
| `CP-0705` | Staging smoke passed | `tools/e2e-drive/run-smoke` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live staging service endpoint |
| `CP-0706` | Performance assertions within declared thresholds | `tools/evidence/run-performance` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live load/performance test runner against staging |
| `CP-0707` | UAT result recorded via RECORD-VERIFICATION-RESULT | `gh workflow run record-verification-result.yml` | **EXISTS (gh)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L4** | Requires live GitHub Actions dispatch and qa-1 human actor |
| `CP-0708` | records/uat/ carries the run's UAT record | `tools/records/find-record` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L4** | Offline record search in control-plane-records store |
| `CP-0709` | UAT record authored by records-writer in control-plane-records | `tools/records/verify-author` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L4** | Requires git commit provenance check on control-plane-records repo |
| `CP-0801` | No open verification-block record | `tools/records/check-verification-block` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L4** | Offline verification-block store query |
| `CP-0802` | Production approval recorded against staging-verified digest | `tools/e2e-drive/approve-production` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires distinct lead-1 human approval event |
| `CP-0803` | Production approver differs from change author | `tools/records/verify-approval-identity` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L4** | Offline identity comparison between author and approver |
| `CP-0804` | production_approval_granted event distinct from gate_2_approval | `tools/records/find-event` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L4** | Offline event search in records store |
| `CP-0901` | Freeze gate resolved against declared calendar | `tools/evidence/verify-freeze-evaluation` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L2** | Offline check verifying calendar source in deployment record |
| `CP-0902` | Production deploy succeeded | `tools/e2e-drive/run-workflow` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live production deployment workflow |
| `CP-0903` | Production job pulled digest and ran no build step | `tools/evidence/verify-no-rebuild` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live production workflow run logs analysis |
| `CP-0904` | Deployment record written to records/deployments/ | `tools/records/find-record` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L4** | Offline record search in control-plane-records store |
| `CP-0905` | Production smoke passed | `tools/e2e-drive/run-smoke` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live production service endpoint |
| `CP-0906` | Health checks green with dependency detail | `curl / jq` | **EXISTS (curl) / MISSING (jq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L5** | Requires live production /health endpoint with mTLS scrape cert |
| `CP-0907` | Production /version equals approved digest | `tools/evidence/read-version` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live production /version endpoint |
| `CP-0908` | All eight ship conditions satisfied | `tools/evidence/check-ship-definition` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L2** | Offline audit of 8 ship conditions including STATE.md |
| `CP-1000` | evidence-chain assembled from permitted sources only | `tools/evidence/evidence-chain` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires live GitHub, Actions, Grafana API collectors |
| `CP-1001` | Q1 commit equals merge SHA | `jq` | **MISSING (jq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires assembled evidence chain from live run |
| `CP-1002` | Q2 PR resolves from commit-to-PR association | `jq` | **MISSING (jq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires assembled evidence chain from live run |
| `CP-1003` | Q3 approver=dev-b role=cross_reviewer | `jq` | **MISSING (jq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires assembled evidence chain from live run |
| `CP-1004` | Q4 run_url is real run whose head SHA is Q1 commit | `jq` | **MISSING (jq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires assembled evidence chain from live run |
| `CP-1005` | Q5 digest equals build digest | `jq` | **MISSING (jq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires assembled evidence chain from live run |
| `CP-1006` | Q6 staging_deployed_at present, UTC with offset | `jq` | **MISSING (jq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires assembled evidence chain from live run |
| `CP-1007` | Q7 smoke=pass and uat_record points at real file | `jq` | **MISSING (jq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires assembled evidence chain from live run |
| `CP-1008` | Q8 approver=lead-1 verified by workflow-identity gate | `tools/e2e-drive/workflow-identity-verify` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires live workflow identity verification tool |
| `CP-1009` | Q9 production_deployed_at present | `jq` | **MISSING (jq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires assembled evidence chain from live run |
| `CP-1010` | Q10 smoke=pass, attached to deployment | `jq` | **MISSING (jq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires assembled evidence chain from live run |
| `CP-1011` | Q11 digest read live from GET /version | `jq` | **MISSING (jq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires live production /version endpoint |
| `CP-1012` | Recorded digest equals running digest (item 5 == 11) | `jq` | **MISSING (jq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Invariant #22: requires live running container |
| `CP-1013` | Production digest equals staging-verified digest | `jq` | **MISSING (jq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Invariant #22: requires live deployment records |
| `CP-1014` | verify-digest-chain sweep reports zero mismatches | `tools/evidence/verify-digest-chain` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires sweep across live deployed services |
| `CP-1015` | Every answer names a canonical record store | `jq` | **MISSING (jq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | Requires assembled chain from live run |
| `CP-1016` | events/, records/deployments/, records/uat/ within write-freshness window | `tools/records/check-write-freshness` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L4** | Offline timestamp check on record stores |
| `CP-1101` | Rollback to previous approved digest succeeds | `tools/e2e-drive/run-workflow` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live rollback.yml execution on production |
| `CP-1102` | /version reports rolled-back digest | `tools/evidence/read-version` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live production /version query |
| `CP-1103` | Rollback recorded as exceptional auth with from/to digest | `tools/records/find-event` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L4** | Offline event query in records store |
| `CP-1104` | Roll forward to approved digest | `tools/e2e-drive/run-workflow` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Requires live production re-deploy |
| `CP-1105` | restore-production.yml runs with scoped identity and no human credential | `tools/e2e-drive/run-workflow` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | AT-103: requires live production restore execution |
| `CP-1106` | restore-test record carries integrity_check and named verifier | `tools/records/find-record` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L4** | Offline record query in records store |
| `CP-1107` | restore_tested date matches a passing record | `validators/drift/check-restore-tested` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L3** | Offline product.yaml vs record comparison |
| `CP-1108` | Planted defect regression test fails without fix | `tools/evidence/run-regression` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Invariant #2: requires test execution in repo |
| `CP-1201` | Reconciliation found seeded canary | `reconciler/run / jq` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | AT-102: requires reconciler run against live GitHub estate |
| `CP-1202` | Zero-finding run classified failed, not clean | `jq` | **MISSING (jq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires live reconciliation run output |
| `CP-1203` | Per-registry comparison counts recorded and non-zero | `jq` | **MISSING (jq)** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | Requires live reconciliation run output |
| `CP-1204` | Run result written whether or not findings exist | `tools/records/find-record` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L4** | Offline query in records/reconciliation |
| `CP-1205` | Stricter-than-declared control is raised, not relaxed | `tools/e2e-drive/stricter-control-probe` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | AT-033: requires mutation of live GitHub repo branch protection |
| `CP-1206` | Operating system reports failure in its own health job | `tools/e2e-drive/self-observability-probe` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | AT-032: requires deliberate fault injection in live health job |
| `CP-1207` | Independent control verifier result present and externally written | `tools/records/find-record` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L4** | Requires off-VM execution and external credential write |
| `CP-1208` | Expired exception auto-revoked; unrevokable becomes Blocking | `tools/e2e-drive/exception-expiry-probe` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | AT-036/037: requires live exception lifecycle handling |
| `CP-1209` | Bootstrap exception at expiry arms or blocks | `tools/e2e-drive/bootstrap-expiry-probe` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | AT-039: requires live gate arming reconciliation |
| `CP-1210` | Reconciler credential bounded on all six attempts | `tools/e2e-drive/at-110-reconciler-bounds.sh` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | AT-110: requires real API privilege boundary probe against GitHub |
| `CP-1310` | Ops console read-only on all four attempts | `tools/e2e-drive/at-108-ops-console.sh` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L5** | AT-108: requires live founder ops console instance |
| `CP-1311` | Cage egress wall and wall-clock stop hold | `tools/e2e-drive/at-109-cage.sh` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L5** | AT-109: requires live Linux cage worker environment |
| `CP-1312` | Machine account restricted to draft PRs, GitHub-side | `tools/e2e-drive/draft-pr-only-verification.sh` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L5** | Invariant #18: requires real GitHub account machine-bg permissions probe |
| `CP-1313` | No customer data in repositories | `tools/evidence/check-no-customer-data` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L5** | Invariant #111: local regex/data-shape scan over pilot repo and records |

---

## 3. Negative Gate Test Readiness Inventory (NEG-01 through NEG-28)

| Negative Test ID | Gate Under Test / Description | Required Tool / Command | Tool Exists? | Readiness Classification | Owning Lane (§8.3) | Blocking Dependency / Rationale |
|---|---|---|---|---|---|---|
| `NEG-01` | Digest immutability: request production deploy of unverified digest | `tools/e2e-drive/run-workflow` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Inv #22: requires live workflow dispatch with foreign digest |
| `NEG-02` | Digest immutability: trigger deploy-production.yml with rebuild: true | `tools/e2e-drive/run-workflow` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Inv #22, #23: requires production deploy workflow parameter validation |
| `NEG-03` | /version match: deploy, then hot-patch container | `tools/e2e-drive/hot-patch-container` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | §32 item 11: requires running production container mutation |
| `NEG-04` | Verification contract: always-passing contract rejected as non-discriminating | `tools/evidence/run-verification-contract` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L1** | §31.2, SIG-18: discriminates between seeded defect and clean tree |
| `NEG-05` | Plan-checker: schema-touching plan with no rollback strategy rejected | `tools/gate1/plan-check` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L0** | §30.2: static schema and markdown verification |
| `NEG-06` | Plan-checker: plan with no automated verify command rejected | `tools/gate1/plan-check` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L0** | §30.2: static plan AST/regex validation |
| `NEG-07` | Plan-checker: plan referencing non-existent symbol rejected | `tools/gate1/plan-check` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L0** | §30.2: symbol table lookup against codebase |
| `NEG-08` | Plan-checker: plan adding slopsquat package name rejected | `tools/gate1/plan-check` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L0** | §30.2: package name legitimacy check |
| `NEG-09` | Gate 1 independence: author dev-a cannot approve own plan | `tools/gate1/approve` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L0** | §26.1: requires multi-actor capability resolution (S-01, bootstrap-skipped) |
| `NEG-10` | Gate 2 independence: author cannot approve own PR | `tools/e2e-drive/approve-pr` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L5** | Inv #8, #9: requires real GitHub PR review permissions (S-01, bootstrap-skipped) |
| `NEG-11` | Gate 2 staleness: new push invalidates approval | `tools/e2e-drive/merge-pr` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | Inv #9: requires real GitHub Branch Protection dismiss_stale_reviews |
| `NEG-12` | Read-only approval: read permission holder cannot approve | `tools/e2e-drive/approve-pr` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L5** | §95.4: requires live collaborator role enforcement (S-01, bootstrap-skipped) |
| `NEG-13` | Production self-approval: approver cannot dispatch deploy | `tools/e2e-drive/run-workflow` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | §27.2, Inv #12: requires workflow identity check (S-01, bootstrap-skipped) |
| `NEG-14` | Production approval ordering: cannot approve before staging verification | `tools/e2e-drive/approve-production` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | §27: requires staging verification record existence gate |
| `NEG-15` | Verification block: deploy fails closed while block exists | `tools/records/open-verification-block` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L4** | §27: fail-closed evaluation against verification block store |
| `NEG-16` | Environment ref policy: deploy from unauthorized branch rejected | `tools/e2e-drive/run-workflow` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | §33.4: requires GitHub Environment ref protection rules |
| `NEG-17` | Record write path: reconciler credential cannot write to records | `tools/records/test-write` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L4** | §97.1, AT-110: requires credential permission boundary enforcement |
| `NEG-18` | Reconciler canary: zero findings classified as FAILED run | `reconciler/run` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | AT-102: requires reconciler canary probe removal |
| `NEG-18b` | Canary restored and found again | `reconciler/run` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L3** | AT-102: requires reconciler canary probe restoration |
| `NEG-19` | Required-check integrity: path filter on required job rejected | `tools/e2e-drive/path-filter-probe` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L2** | §33.2: static AST audit of workflow if: conditions on required checks |
| `NEG-20` | Tag pin integrity: tag ruleset blocks moving workflows/* tag | `tools/e2e-drive/move-workflow-tag` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L2** | §33.2, §53.1: requires GitHub Tag Protection Ruleset enforcement |
| `NEG-21` | Renovate path guard: non-Renovate author pushing lockfile rejected | `tools/e2e-drive/push-commit` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L2** | §33.2: git commit author and changed paths audit |
| `NEG-22` | Friday freeze: deploy dispatched at 15:30 Friday declared time rejected | `tools/e2e-drive/run-workflow` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L2** | §34.2, §97.1: calendar freeze gate evaluation |
| `NEG-23` | Machine authority: machine account cannot merge/approve/deploy | `tools/e2e-drive/machine-action` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L5** | Inv #18, §37.3: requires GitHub-side actor gate permissions |
| `NEG-24` | Parity: staging-only env var causes parity violation blocking deploy | `tools/evidence/check-parity` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L2** | §33.1: environment variable comparison across environments |
| `NEG-25` | Exception expiry: exception without expiry date fails validation | `validators/registry/validate-exceptions` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L1** | Inv #77: offline schema validation of exceptions.yaml |
| `NEG-26` | Auto-repair direction: refuses to move toward looser control | `reconciler/auto-repair` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L3** | Inv #81, AT-033: control direction monotonicity enforcement |
| `NEG-27` | Deployment record: deploy aborts when record write fails | `tools/e2e-drive/run-workflow` | **MISSING** | `GENUINELY BLOCKED ON LIVE INFRASTRUCTURE` | **L4** | §97.2: evidence chain closure requirement on deploy |
| `NEG-28` | Customer data: fixture containing customer data detected/rejected | `tools/evidence/check-no-customer-data` | **MISSING** | `BUILDABLE NOW, OFFLINE` | **L5** | Inv #111: offline PII / customer data pattern detector |

---

## 4. Owning Lane Action Backlog (§8.3 Routing)

| Lane | Scope | Buildable Now (Offline) Deliverables | Genuinely Blocked Deliverables (Awaiting Live Infra) |
|---|---|---|---|
| **L0** | Harness, Gate 1, Preflight, Evidence Assembly | `tools/verify-workflow-tag-pins.sh`, `tools/freeze-window-check.sh`, `tools/gate1/plan-check`, `tools/gate1/submit-plan` | Gate 1 push notification service, multi-actor approval (`lead-1` vs `dev-a`), `evidence-chain` multi-API aggregator |
| **L1** | Schemas, Contracts, Registries | `validators/registry/validate-verification-contract`, `validators/registry/validate-exceptions`, coverage map validator | Live verification contract evaluation against deployed services |
| **L2** | Workflows, Pipelines, Builds, Deploys | Static AST / if: condition verifiers (`check-conclusions`), offline parity check, commit/author guards | `org/pilot-one-api` repo, GitHub Actions runners, GHCR container push/pull, staging/production deployments |
| **L3** | Provisioning, Reconciler, Drift | `tools/verify-no-product-list.sh`, `apply-assignments`, orphan reporting | Live GitHub Org scaffolding (`create-product` shell executor), GitHub Teams, live Reconciler canary execution (AT-102, AT-110) |
| **L4** | Records Store, Events, Freshness | `tools/records/find-record`, `tools/records/find-event`, `check-write-freshness`, verification block logic | `control-plane-records` repository, GitHub App `records-writer[bot]` token execution |
| **L5** | Access, Cage, VM, Boundaries | PII / customer data pattern detector (`check-no-customer-data`) | Linux cage worker isolation (AT-109), Founder ops console (AT-108), GitHub machine account restrictions (Invariant #18) |

---

## 5. Conclusion: What Stands Between Harness and Real V1 Verification

1. **Scaffolding Complete:** All 14 stage scripts and 28 negative scripts are written, syntactically valid, and bound to protocol 08 primitives.
2. **Real Tooling Built:** `tools/verify-workflow-tag-pins.sh --strict` and `tools/freeze-window-check.sh --need-minutes 90` are fully implemented with real logic.
3. **True Current State:** The execution chain breaks at **CP-0004** in Preflight due to unregistered reusable workflow tags (`workflows/v1`, `workflows/v1.0.0`), followed by CP-0005 (weekend execution) and CP-0006 (operator CLI environment). Beyond Preflight, 80 positive checkpoints and 18 negative tests are genuinely blocked on live multi-tenant infrastructure.
4. **Anti-Hallucination Integrity:** Per `AGENTS.md`, zero stubs or mocks were introduced to fake passes against unbuilt infrastructure. The harness reports failures accurately and truthfully.
