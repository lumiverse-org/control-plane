#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
python3 -m tools.evidence.identity_gate \
  --approval tools/evidence/tests/fixtures/gate-l2-009/approval.yaml \
  --deployer dev-two --summary
