#!/usr/bin/env bash
# validate-freshness.sh — §97.2 / §53.1 freshness declaration validator and repo cadence checker
# Usage:
#   validate-freshness.sh                -> declaration validator; exits 0 and prints FRESHNESS OK BLOCKING=3
#   validate-freshness.sh --check-repo <dir> -> verifies write cadence of stores in <dir> against write-freshness.yaml
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CONTROL_PLANE_ROOT="${CONTROL_PLANE_ROOT:-$(cd "$HERE/../.." && pwd)}"
FRESHNESS_FILE="${CONTROL_PLANE_ROOT}/metrics/freshness/write-freshness.yaml"

if [[ ! -f "${FRESHNESS_FILE}" ]]; then
  echo "ERROR: ${FRESHNESS_FILE} not found — run L4-04-M02 first" >&2
  exit 1
fi

if [[ "${1:-}" == "--check-repo" || "${1:-}" == "--repo" ]]; then
  TARGET_REPO="${2:-}"
  if [[ -z "${TARGET_REPO}" || ! -d "${TARGET_REPO}" ]]; then
    echo "ERROR: --check-repo requires a valid directory" >&2
    exit 2
  fi
  python3 - "${FRESHNESS_FILE}" "${TARGET_REPO}" <<'PY'
import sys, os, yaml, subprocess, time

freshness_file, repo_dir = sys.argv[1], sys.argv[2]
data = yaml.safe_load(open(freshness_file, encoding="utf-8"))
stores = data.get("stores", [])

now_ts = int(time.time())
blocking_breaches = 0
amber_breaches = 0
fresh_count = 0

for s in stores:
    path = s.get("path")
    max_hours = s.get("max_interval_hours", 24)
    is_blocking = s.get("blocking", False)

    res = subprocess.run(
        ["git", "-C", repo_dir, "log", "-1", "--format=%ct", "--", path],
        capture_output=True,
        text=True,
    )
    ts_str = res.stdout.strip()
    if not ts_str:
        continue

    commit_ts = int(ts_str)
    diff_sec = max(0, now_ts - commit_ts)
    age_hours = diff_sec // 3600

    if age_hours > max_hours:
        if is_blocking:
            blocking_breaches += 1
            print(f"BREACH BLOCKING {path} age={age_hours}h max={max_hours}h")
        else:
            amber_breaches += 1
            print(f"BREACH AMBER {path} age={age_hours}h max={max_hours}h")
    else:
        fresh_count += 1
        print(f"FRESH OK {path} age={age_hours}h max={max_hours}h")

print(f"CADENCE SUMMARY: blocking_breaches={blocking_breaches} amber_breaches={amber_breaches} fresh={fresh_count}")
PY
  exit 0
fi

FAIL=0
MISSING_INTERVAL=()
MISSING_BLOCKING=()

# Collect all declared store paths
mapfile -t STORE_PATHS < <(grep "^  - path:" "${FRESHNESS_FILE}" | sed 's/.*path: "\(.*\)"/\1/' | tr -d '\r')

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
