#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
python3 -m tools.evidence.check_required_contexts \
  --templates templates/workflows \
  --registry templates/workflows/required-checks.yaml --summary
