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
