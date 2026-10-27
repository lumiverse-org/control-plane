#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
python3 -m tools.evidence.digest_invariant \
  --requested sha256:abababababababababababababababababababababababababababababababab \
  --staging-record tools/evidence/tests/fixtures/nt-04/staging-record.yaml --summary
