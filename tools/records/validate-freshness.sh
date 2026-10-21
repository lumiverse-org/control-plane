#!/usr/bin/env bash
# validate-freshness.sh — §97.2 / §53.1 freshness declaration validator
# Exit 0 and print FRESHNESS OK BLOCKING=3 when all checks pass.
# Exit non-zero and print named failures otherwise.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CONTROL_PLANE_ROOT="${CONTROL_PLANE_ROOT:-$(cd "$HERE/../.." && pwd)}"
FRESHNESS_FILE="${CONTROL_PLANE_ROOT}/metrics/freshness/write-freshness.yaml"

if [[ ! -f "${FRESHNESS_FILE}" ]]; then
  echo "ERROR: ${FRESHNESS_FILE} not found — run L4-04-M02 first" >&2
  exit 1
fi

FAIL=0
MISSING_INTERVAL=()
MISSING_BLOCKING=()

# Collect all declared store paths
mapfile -t STORE_PATHS < <(grep "^  - path:" "${FRESHNESS_FILE}" | sed 's/.*path: "\(.*\)"/\1/')

if [[ "${#STORE_PATHS[@]}" -eq 0 ]]; then
  echo "ERROR: no stores found in ${FRESHNESS_FILE}" >&2
  exit 1
fi

# For each store, confirm max_interval_hours is present in its block
for store in "${STORE_PATHS[@]}"; do
  LINE=$(grep -n "path: \"${store}\"" "${FRESHNESS_FILE}" | head -1 | cut -d: -f1)
  if [[ -z "${LINE}" ]]; then
    MISSING_INTERVAL+=("${store}:path-not-found")
    FAIL=1
    continue
  fi
  # Look for max_interval_hours within the next 10 lines of this store block
  BLOCK=$(sed -n "${LINE},$((LINE+10))p" "${FRESHNESS_FILE}")
  if ! echo "${BLOCK}" | grep -q "max_interval_hours:"; then
    MISSING_INTERVAL+=("${store}")
    FAIL=1
  fi
done

# Count blocking: true entries
BLOCKING_COUNT=$(grep -c "blocking: true" "${FRESHNESS_FILE}" || true)

if [[ "${BLOCKING_COUNT}" -ne 3 ]]; then
  echo "ERROR: expected exactly 3 stores with blocking: true, found ${BLOCKING_COUNT}" >&2
  FAIL=1
fi

# Confirm the mandated three blocking stores are present and marked blocking
REQUIRED_BLOCKING=("events/" "records/deployments/" "records/uat/")
for store in "${REQUIRED_BLOCKING[@]}"; do
  LINE=$(grep -n "path: \"${store}\"" "${FRESHNESS_FILE}" | head -1 | cut -d: -f1)
  if [[ -z "${LINE}" ]]; then
    echo "ERROR: mandatory blocking store '${store}' not declared" >&2
    MISSING_BLOCKING+=("${store}:missing")
    FAIL=1
    continue
  fi
  BLOCK=$(sed -n "${LINE},$((LINE+5))p" "${FRESHNESS_FILE}")
  if ! echo "${BLOCK}" | grep -q "blocking: true"; then
    echo "ERROR: mandatory store '${store}' is not marked blocking: true" >&2
    MISSING_BLOCKING+=("${store}:not-blocking")
    FAIL=1
  fi
done

if [[ "${#MISSING_INTERVAL[@]}" -gt 0 ]]; then
  echo "ERROR: stores missing max_interval_hours: ${MISSING_INTERVAL[*]}" >&2
fi

if [[ "${FAIL}" -ne 0 ]]; then
  exit 1
fi

echo "FRESHNESS OK BLOCKING=3"
exit 0
