#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
python3 -m tools.evidence.actor_gate \
  --actor dev-1 --capability production-approval \
  --people tools/evidence/fixtures/actor/people.yaml --summary
