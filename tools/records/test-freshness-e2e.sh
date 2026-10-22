#!/usr/bin/env bash
# tools/records/test-freshness-e2e.sh
# End-to-end write freshness proof from real git commit timestamps.
# Master Spec v4.0 Section 97.2 line 8873; Section 53.1 line 4679; L4-06 row L4-P8-01; FD-132.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CONTROL_PLANE_ROOT="${CONTROL_PLANE_ROOT:-$(cd "$HERE/../.." && pwd)}"
VALIDATOR="${CONTROL_PLANE_ROOT}/tools/records/validate-freshness.sh"

if [[ ! -x "${VALIDATOR}" ]]; then
  chmod +x "${VALIDATOR}" 2>/dev/null || true
fi

# 1. Setup temporary git repository
TMP_REPO="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_REPO"
}
trap cleanup EXIT INT TERM

git -C "$TMP_REPO" init -q -b main
git -C "$TMP_REPO" config user.email "freshness-e2e@control-plane.local"
git -C "$TMP_REPO" config user.name "Freshness Tester"

# Initial commit
echo "control-plane-records synthetic fixture" > "$TMP_REPO/README.md"
git -C "$TMP_REPO" add README.md
git -C "$TMP_REPO" commit -q -m "initial commit"

# 2. Seed a BLOCKING breach on records/deployments/ (max_interval_hours: 24, blocking: true)
# Backdate by 50 hours
DATE_50H=$(python3 -c "from datetime import datetime, timezone, timedelta; print((datetime.now(timezone.utc) - timedelta(hours=50)).strftime('%Y-%m-%dT%H:%M:%SZ'))")
mkdir -p "$TMP_REPO/records/deployments"
echo "deployment: test-stale" > "$TMP_REPO/records/deployments/DEP-2026-10-20-001.yaml"
git -C "$TMP_REPO" add records/deployments
GIT_COMMITTER_DATE="$DATE_50H" GIT_AUTHOR_DATE="$DATE_50H" git -C "$TMP_REPO" commit -q -m "stale deployment record"

# 3. Seed an AMBER breach on records/eval/ (max_interval_hours: 72, blocking: false)
# Backdate by 120 hours
DATE_120H=$(python3 -c "from datetime import datetime, timezone, timedelta; print((datetime.now(timezone.utc) - timedelta(hours=120)).strftime('%Y-%m-%dT%H:%M:%SZ'))")
mkdir -p "$TMP_REPO/records/eval"
echo "eval: test-stale" > "$TMP_REPO/records/eval/EVAL-2026-10-17-001.yaml"
git -C "$TMP_REPO" add records/eval
GIT_COMMITTER_DATE="$DATE_120H" GIT_AUTHOR_DATE="$DATE_120H" git -C "$TMP_REPO" commit -q -m "stale eval record"

# 4. Seed a FRESH store on records/uat/ (max_interval_hours: 48, blocking: true)
mkdir -p "$TMP_REPO/records/uat"
echo "uat: test-fresh" > "$TMP_REPO/records/uat/UAT-2026-10-22-001.yaml"
git -C "$TMP_REPO" add records/uat
git -C "$TMP_REPO" commit -q -m "fresh uat record"

# 5. Run validator in repo-cadence mode
OUTPUT="$(bash "$VALIDATOR" --check-repo "$TMP_REPO")"
echo "$OUTPUT"

# 6. Assert correct Amber and Blocking classifications
if ! echo "$OUTPUT" | grep -q "BREACH BLOCKING records/deployments/"; then
  echo "FAIL: expected BREACH BLOCKING on records/deployments/" >&2
  exit 1
fi

if ! echo "$OUTPUT" | grep -q "BREACH AMBER records/eval/"; then
  echo "FAIL: expected BREACH AMBER on records/eval/" >&2
  exit 1
fi

if ! echo "$OUTPUT" | grep -q "FRESH OK records/uat/"; then
  echo "FAIL: expected FRESH OK on records/uat/" >&2
  exit 1
fi

echo "FRESHNESS E2E OK: verified 1 Blocking breach, 1 Amber breach, 1 Fresh"
exit 0
