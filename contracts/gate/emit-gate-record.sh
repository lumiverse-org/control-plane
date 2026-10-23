#!/usr/bin/env sh
# =============================================================================
# emit-gate-record.sh - L0-owned (contracts/gate/**, L0D-IG-1).
# The ONE thing that COMMITS a gate record. Invoked by CI under
# RECORDS_WRITER_TOKEN (protocol/10 sections 7.2, 7.3, 7.4). L0 never pushes to
# control-plane-records: L4 owns that repository entirely (PARTITION.md).
#   --gate lane             --pr <n> --head <sha> --result <r> --run-id <id>
#   --gate integration-step --head <sha> --ct <r> --audits <r> --run-id <id>
#   --gate integration      --cycle <id> --head <sha> --result <r> --run-id <id>
#   [--log <path>]          per-check lines; defaults to .gate/integration.log
# Writes ONE file via the Contents API with NO sha parameter, so a second write
# to the same key is refused by GitHub itself (invariant 47).
# Last line on stdout is the verdict. Exit 0 pass, 1 fail, 2 config error.
# =============================================================================
set -eu
GATE=""; PR=""; HEAD=""; CYCLE=""; RESULT=""; CT=""; AUDITS=""; RUNID=""
LOG="${GATE_LOG:-.gate/integration.log}"
while [ $# -gt 0 ]; do case "$1" in
  --gate)    GATE="$2";   shift 2 ;;
  --pr)      PR="$2";     shift 2 ;;
  --head)    HEAD="$2";   shift 2 ;;
  --cycle)   CYCLE="$2";  shift 2 ;;
  --result)  RESULT="$2"; shift 2 ;;
  --ct)      CT="$2";     shift 2 ;;
  --audits)  AUDITS="$2"; shift 2 ;;
  --run-id)  RUNID="$2";  shift 2 ;;
  --log)     LOG="$2";    shift 2 ;;
  *) echo "EMIT-GATE-RECORD FAIL: unknown argument '$1'"; exit 2 ;;
esac; done
[ -n "$GATE" ] && [ -n "$HEAD" ] || { echo "EMIT-GATE-RECORD FAIL: --gate and --head are required"; exit 2; }

OWNER="${RECORDS_REPO_OWNER:-${GITHUB_REPOSITORY_OWNER:-}}"
[ -n "$OWNER" ] || { echo "EMIT-GATE-RECORD FAIL: RECORDS_REPO_OWNER unset - the target org is never guessed"; exit 2; }
REPO="$OWNER/control-plane-records"
DATE=$(date -u +%F); TS=$(date -u +%Y-%m-%dT%H:%M:%SZ); SHORT=$(printf '%s' "$HEAD" | cut -c1-7)

case "$GATE" in
  lane)
    [ -n "$PR" ] || { echo "EMIT-GATE-RECORD FAIL: --pr is required for --gate lane"; exit 2; }
    KEY="PR-$PR-$SHORT"; ID="GATERUN-$DATE-lane-PR$PR"; WF="selfci-gate-a" ;;
  integration-step)
    KEY="$SHORT"; ID="GATERUN-$DATE-integration-step-$SHORT"; WF="selfci-integration"
    RESULT="$CT/$AUDITS" ;;
  integration)
    [ -n "$CYCLE" ] || { echo "EMIT-GATE-RECORD FAIL: --cycle is required for --gate integration"; exit 2; }
    KEY="CYCLE-$CYCLE"; ID="GATE-$CYCLE"; WF="selfci-gate-b" ;;
  *) echo "EMIT-GATE-RECORD FAIL: --gate must be lane, integration-step or integration"; exit 2 ;;
esac
REC="records/gate/$GATE/$DATE/$KEY.yaml"

VERDICT=FAIL
case "$GATE:$RESULT" in
  lane:success|integration:success|integration-step:success/success) VERDICT=PASS ;;
esac

NLINES=0
if [ -f "$LOG" ]; then NLINES=$(grep -c . "$LOG" || true); fi
if [ "$GATE" = "integration" ] && [ "$NLINES" -eq 0 ]; then
  echo "EMIT-GATE-RECORD FAIL: gate log $LOG absent or empty - a cycle record with no per-check lines is not evidence (protocol/05 section 10)"
  exit 1
fi
if [ "$NLINES" -eq 0 ]; then CH="checks: []"
else CH="checks:
$(sed 's/\\/\\\\/g; s/"/\\"/g; s/^/  - "/; s/$/"/' "$LOG")"; fi

BODY=$(printf 'record_schema_version: 1\nid: %s\nproduct: control-plane\ntimestamp: %s\ngate: %s\ncycle: %s\nhead: %s\nworkflow: %s\nrun_id: "%s"\nverdict: %s\nat_denominator: "37/110 (protocol/02 section 9.1)"\n%s\n' \
  "$ID" "$TS" "$GATE" "${CYCLE:-none}" "$HEAD" "$WF" "$RUNID" "$VERDICT" "$CH")

ERRF="${TMPDIR:-/tmp}/emit-gate-record.$$"
B64=$(printf '%s' "$BODY" | base64 | tr -d '\n')
if gh api --method PUT "repos/$REPO/contents/$REC" \
     -f message="gate record $ID" -f content="$B64" >/dev/null 2>"$ERRF"; then
  printf 'EMIT-GATE-RECORD PASS gate=%s record=%s verdict=%s checks=%s\n' "$GATE" "$REC" "$VERDICT" "$NLINES"
  rm -f "$ERRF"; exit 0 # exit 0 = gate ARMED (FD-035)
fi
if grep -qi 'sha\|already exists\|422' "$ERRF" 2>/dev/null; then
  printf 'EMIT-GATE-RECORD FAIL record=%s reason=already-exists - records are append-only, never overwritten (invariant 47)\n' "$REC"
else
  printf 'EMIT-GATE-RECORD FAIL record=%s reason=write-refused\n' "$REC"
fi
rm -f "$ERRF"; exit 1
