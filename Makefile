# Makefile — Multi-Product Engineering OS convenience targets
# Usage: make <target>
# FD-082: task IDs normalized to L<N>-<FF>-<NN> format

.PHONY: help check concordance handover canary validate test phase0-dry setup capacity schedule-check ready-queue lint metrics orphans lane-guard train freeze gate-freeze promote-check

LANE ?= 0
BASE ?= integration
HEAD ?= HEAD

lane-guard:
	@./lane-guard.sh $(LANE) $(BASE) $(HEAD)

train:
	@echo "MERGE TRAIN ORDER (FROZEN): L1 -> L4 -> L2 -> L3 -> L5"
	@echo "Per lane: rebase -> lane-guard -> lane SELF-VERIFY -> merge --no-ff -> re-verify"

freeze:
	@test -d contracts || { echo "CONTRACTS-NOT-FROZEN: contracts/ does not exist"; exit 1; }
	@find contracts -type f -not -path 'contracts/gate/*' -not -path 'contracts/ci/*' \
	  | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1 > contracts.sha256
	@echo "CONTRACTS-FROZEN $$(cat contracts.sha256)"

gate-freeze:
	@test -d contracts/gate || { echo "GATE-NOT-FROZEN: contracts/gate/ does not exist"; exit 1; }
	@find contracts/gate -type f -not -name PHASE \
	  | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1 > gate.sha256
	@echo "GATE-FROZEN $$(cat gate.sha256)"

promote-check:
	@$(MAKE) decisions-gate PHASE=$$(cat contracts/gate/PHASE 2>/dev/null || echo Ph0)
	@test -d contracts || { echo "CONTRACTS-NOT-FROZEN: contracts/ does not exist"; exit 1; }

	@test -f contracts.sha256 || { echo "CONTRACTS-NOT-FROZEN: no freeze hash recorded"; exit 1; }
	@now=$$(find contracts -type f -not -path 'contracts/gate/*' -not -path 'contracts/ci/*' \
	  | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1); \
	 was=$$(cat contracts.sha256); \
	 if [ "$$now" = "$$was" ]; then echo "CONTRACTS-FROZEN OK"; \
	 else echo "CONTRACTS-DRIFT: frozen=$$was actual=$$now"; exit 1; fi


# Default target
help:
	@echo "Multi-Product Engineering OS — Make targets"
	@echo ""
	@echo "  check        Run concordance check (5-lane) + verify_handover"
	@echo "  concordance  Run concordance check only"
	@echo "  handover     Run verify_handover.sh only"
	@echo "  canary       Check registry canary sentinel"
	@echo "  validate     Run L1 validator CLI (Option B)"
	@echo "  phase0-dry   Dry-run Phase 0 (creates no resources)"
	@echo "  setup        Install git hooks"
	@echo "  capacity     L4 capacity model for current month (FD-089/FD-090)"
	@echo "  schedule-check L4 floor obligation check for current month (FD-031)"
	@echo "  ready-queue  L4 ready queue miss check (FD-091/PFD-017)"
	@echo ""

check: concordance handover
	@echo "=== All checks passed ==="

concordance:
	bash _concordance-check.sh lanes

handover:
	bash ../verify_handover.sh 2>/dev/null || bash ../../verify_handover.sh 2>/dev/null || bash ../../../verify_handover.sh

canary:
	bash scripts/canary-check.sh registries/people/_canary.yaml

validate:
	python -m validators.registry.cli \
		--root . \
		--as-of $(shell date +%Y-%m-%d) \
		--records-root records/ \
		--format json

test:
	python -m pytest tests/ -v --tb=short

metrics:
	bash scripts/metrics/validate-metrics.sh

orphans:
	bash scripts/orphan-detect.sh .

phase0-dry:
	@echo "Setting GITHUB_TOKEN is required. Run:"
	@echo "  \$$env:GITHUB_TOKEN = 'your-pat'; bash run-phase-0.sh --dry-run"
	@echo ""
	@echo "Pre-flight check:"
	bash scripts/provision/check-prerequisites.sh

setup:
	@echo "Installing git hooks..."
	@mkdir -p .git/hooks
	@cp scripts/git-hooks/pre-commit .git/hooks/pre-commit 2>/dev/null && chmod +x .git/hooks/pre-commit || echo "No pre-commit hook found"
	@cp scripts/git-hooks/commit-msg .git/hooks/commit-msg 2>/dev/null && chmod +x .git/hooks/commit-msg || echo "No commit-msg hook found"
	@echo "Done."

lint:
	python -m py_compile validators/registry/cli.py && echo "Python lint: OK"
	python -m py_compile validators/registry/rules/registry.py && echo "Rule registry lint: OK"

capacity:
	python scripts/l4/capacity-model.py --period $(shell date +%Y-%m) --output text

schedule-check:
	python scripts/l4/scheduling.py --check --period $(shell date +%Y-%m)

ready-queue:
	bash scripts/l4/ready-queue.sh --check

# --- merge train (L0-03) ---
.PHONY: train-preflight train-log train-owners promote-gate

train-preflight:
	@git fetch --prune origin >/dev/null 2>&1
	@test -z "$$(git status --porcelain)" || { echo "PREFLIGHT FAIL: working tree dirty"; exit 1; }
	@test "$$(git rev-parse HEAD)" = "$$(git rev-parse origin/integration)" \
	  || { echo "PREFLIGHT FAIL: not on integration tip"; exit 1; }
	@$(MAKE) --no-print-directory promote-check
	@echo "PREFLIGHT OK"

train-owners:
	@./train-owners.sh $(BASE) $(HEAD)

train-log:
	@test -f docs/merge-train.md || { echo "TRAIN-LOG FAIL: runbook missing"; exit 1; }
	@grep -q '<!-- CYCLE-LOG:BEGIN -->' docs/merge-train.md \
	  || { echo "TRAIN-LOG FAIL: BEGIN marker missing"; exit 1; }
	@{ awk '{print} /<!-- CYCLE-LOG:BEGIN -->/{exit}' docs/merge-train.md; \
	   printf '| cycle | date | L1 | L4 | L2 | L3 | L5 | promoted | notes |\n'; \
	   printf '|---|---|---|---|---|---|---|---|---|\n'; \
	   for f in $$(ls docs/merge-train/cycles/cycle-*.tsv 2>/dev/null | LC_ALL=C sort); do \
	     ./train-row.sh "$$f"; \
	   done; \
	   awk '/<!-- CYCLE-LOG:END -->/{f=1} f{print}' docs/merge-train.md; \
	 } > docs/merge-train.md.new
	@mv docs/merge-train.md.new docs/merge-train.md
	@echo "TRAIN-LOG OK"

promote-gate:
	@./train-promote-gate.sh $(CYCLE)

# --- L0-04: the decision register -------------------------------------------
# `decisions`      the queue, for the standing decision window (charter 8.2)
# `decisions-lint` integrity of the register itself
# `decisions-gate` PHASE=<token>: fails if any P0 or P1 entry gating at or
#                  before PHASE is still open. Local only (L0D-DR-7).
.PHONY: decisions decisions-lint decisions-gate

decisions:
	@docs/decisions/bin/reg-status.sh

decisions-lint:
	@docs/decisions/bin/reg-lint.sh

decisions-gate:
	@test -n "$(PHASE)" || { echo "DECISIONS-GATE FAIL: PHASE is required"; exit 2; }
	@docs/decisions/bin/reg-lint.sh >/dev/null || { echo "DECISIONS-GATE FAIL: register integrity"; exit 1; }
	@n=$$(docs/decisions/bin/reg-status.sh "$(PHASE)" | tail -1 | sed 's/.*overdue=//'); \
	 b=$$(awk -F'\t' '!/^#/ && $$6=="open" && ($$2=="P0" || $$2=="P1")' docs/decisions/register.tsv | wc -l | tr -d ' '); \
	 if [ "$$b" -gt 0 ]; then \
	   echo "DECISIONS-GATE FAIL: $$b P0/P1 entries still open at $(PHASE) (overdue=$$n)"; \
	   docs/decisions/bin/reg-status.sh "$(PHASE)" | awk '$$2=="P0" || $$2=="P1"'; \
	   exit 1; \
	 fi; \
	 echo "DECISIONS-GATE OK phase=$(PHASE) overdue=$$n blocking=0"

# --- L0-06: bootstrap mode ---
.PHONY: bootstrap-render bootstrap-check bootstrap-log bootstrap-fresh

bootstrap-render:
	@CP=$(CURDIR) sh docs/plan/bin/bootstrap-render.sh

bootstrap-check:
	@CP=$(CURDIR) sh docs/plan/bin/bootstrap-check.sh

bootstrap-log:
	@CP=$(CURDIR) sh docs/plan/bin/bootstrap-log-gen.sh

bootstrap-fresh:
	@CP=$(CURDIR) sh docs/plan/bin/bootstrap-log-fresh.sh

# --- integration gate (L0-05) ---
.PHONY: gate-integration gate-integration-dry

gate-integration:
	@test -n "$(CYCLE)" || { echo "GATE FAIL: CYCLE=<id> required"; exit 2; }
	@git fetch --prune origin >/dev/null 2>&1
	@./contracts/gate/run-integration.sh "$(CYCLE)"

gate-integration-dry:
	@GATE_DRY=1 ./contracts/gate/run-integration.sh "$(CYCLE)"
