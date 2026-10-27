#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
python3 -m tools.evidence.evidence_chain \
  --deployment tools/evidence/tests/fixtures/gate-l2-008/deployment.yaml --summary
