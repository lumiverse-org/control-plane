#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/../../.."
bash tools/records/validate-ingest.sh --source-kinds | grep -qx "INGEST OK source-kinds kinds=2 collectors=3 forbidden=0"
