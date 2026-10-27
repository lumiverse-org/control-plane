#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
python3 -m tools.evidence.timegate \
  --at 2026-09-10T04:00:00Z --tz Asia/Kolkata --profile business-hours --summary
