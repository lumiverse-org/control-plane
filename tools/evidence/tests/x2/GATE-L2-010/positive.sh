#!/usr/bin/env bash
# The hosted default of D87: RUNNER_ENVIRONMENT=github-hosted must be admitted.
set -uo pipefail
cd "$(dirname "$0")/../../../../.." || exit 1
RUNNER_ENVIRONMENT=github-hosted \
python3 -m tools.evidence.assert_runner_tier --workflow deploy-production.yml --summary >/dev/null 2>&1
