#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../.."
test -f metrics/ingest/README.md
test -x tools/records/validate-ingest.sh
# Prove the dispatcher fails closed on a missing limb (§40.1 line 3671).
# Later Phase-5 tasks fill in the six named limbs one at a time, so this
# scans for whichever limb has not been built yet rather than hardcoding
# --collectors, which stops being a missing limb once L4-P5-15 lands.
FOUND=0
for flag in --collectors --devlake --prometheus --scorecard --source-kinds --freshness; do
  out="$(bash tools/records/validate-ingest.sh "$flag" 2>&1 || true)"
  if echo "$out" | grep -q "INGEST ERROR missing-limb"; then
    FOUND=1
    break
  fi
done
# neg_fixture: if every limb above already exists, FOUND stays 0 and this
# assertion (the negative case) fails, exactly as it must.
[ "$FOUND" -eq 1 ]
