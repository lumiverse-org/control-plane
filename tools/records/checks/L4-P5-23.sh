#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../.."
bash tools/records/validate-ingest.sh --freshness | grep -qx "INGEST OK freshness slo=1 none-declared=2 arming_strings=3 violations=0"
