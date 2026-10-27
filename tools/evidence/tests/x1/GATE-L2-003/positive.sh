#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
python3 -m tools.evidence.seeded_defect \
  --result tools/evidence/tests/fixtures/gate-l2-003/seed-held.json --summary
