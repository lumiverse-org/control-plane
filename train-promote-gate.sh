#!/usr/bin/env bash
# train-promote-gate.sh — L0-owned. The full gate for integration -> main (L0D-09).
# Usage: ./train-promote-gate.sh <CYCLE> [--dry-run|--apply]
#        ./train-promote-gate.sh --help
# Default is no-network and does not call the GitHub CLI.
# --apply may git-fetch and run read-only `gh run list` for P9.
# This tool never pushes, merges, or promotes.
# EXIT-CODES: 0=pass 1=fail-closed 2=usage
# NO-ARG: usage
# HELP: 0
# Required evidence: docs/merge-train/cycles/cycle-<CYCLE>.tsv
# Absent evidence exits 1 before any fetch or GitHub CLI call.
# P9 without --apply reads docs/merge-train/cycles/cycle-<CYCLE>.ci
# whose single line is "<40-hex origin/integration sha> success".
set -euo pipefail

unset CDPATH
export GIT_TERMINAL_PROMPT=0
export GCM_INTERACTIVE=never

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$ROOT"

# Git for Windows worktrees record `gitdir: C:/...`. MSYS git joins that
# onto the cwd and refuses the repository. git.exe reads the Windows path.
if ! declare -F git >/dev/null 2>&1 && command -v git.exe >/dev/null 2>&1; then
  git() { command git.exe "$@"; }
fi

APPLY=0
MODE=""
CYCLE=""
POSITIONAL=""

usage() {
  cat <<'EOF'
usage: ./train-promote-gate.sh <CYCLE> [--dry-run|--apply]
       ./train-promote-gate.sh --cycle <CYCLE> [--dry-run|--apply]
       ./train-promote-gate.sh --help

CYCLE is three digits. Required evidence is
docs/merge-train/cycles/cycle-<CYCLE>.tsv. If that file is absent the gate
refuses immediately and does not fetch or call the GitHub CLI.

Default runs P1-P9 from local files and local refs.
P9 then requires docs/merge-train/cycles/cycle-<CYCLE>.ci to contain exactly
"<origin/integration sha> success".
--apply fetches origin and reads `gh run list` for P9 only.
Neither mode pushes, merges, or promotes.

exit 0  PROMOTE-GATE OK
exit 1  fail-closed (missing evidence or a P1-P9 failure)
exit 2  usage
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --apply)
      if [ "$MODE" = "dry" ]; then echo "PROMOTE-GATE USAGE: --apply and --dry-run conflict"; exit 2; fi
      MODE=apply; APPLY=1; shift ;;
    --dry-run)
      if [ "$MODE" = "apply" ]; then echo "PROMOTE-GATE USAGE: --apply and --dry-run conflict"; exit 2; fi
      MODE=dry; APPLY=0; shift ;;
    --cycle)
      if [ $# -lt 2 ]; then echo "PROMOTE-GATE USAGE: --cycle requires a value"; exit 2; fi
      if [ -n "$CYCLE" ]; then echo "PROMOTE-GATE USAGE: cycle given twice"; exit 2; fi
      CYCLE=$2; shift 2 ;;
    -*)
      echo "PROMOTE-GATE USAGE: unknown argument '$1'"; exit 2 ;;
    *)
      if [ -n "$POSITIONAL" ]; then echo "PROMOTE-GATE USAGE: unexpected argument '$1'"; exit 2; fi
      POSITIONAL=$1; shift ;;
  esac
done

if [ -n "$POSITIONAL" ]; then
  if [ -n "$CYCLE" ] && [ "$CYCLE" != "$POSITIONAL" ]; then
    echo "PROMOTE-GATE USAGE: conflicting cycle"
    exit 2
  fi
  CYCLE=$POSITIONAL
fi

if [ -z "$CYCLE" ]; then
  echo "PROMOTE-GATE USAGE: cycle required"
  exit 2
fi
if [[ ! $CYCLE =~ ^[0-9]{3}$ ]]; then
  echo "PROMOTE-GATE USAGE: cycle must be three digits"
  exit 2
fi

EVID="docs/merge-train/cycles/cycle-${CYCLE}.tsv"
if [ ! -f "$EVID" ]; then
  echo "GATE-FAIL evidence absent: $EVID"
  echo "PROMOTE-GATE FAIL: 1 condition(s)"
  exit 1
fi

NORM=$(mktemp)
SHAS=$(mktemp)
trap 'rm -f "$NORM" "$SHAS"' EXIT
tr -d '\r' < "$EVID" > "$NORM"

FAIL=0
note() { echo "  $1"; }
bad() { echo "GATE-FAIL $1"; FAIL=$((FAIL+1)); }

if [ "$APPLY" -eq 1 ]; then
  if ! git fetch --prune origin >/dev/null 2>&1; then
    bad "P0 git fetch failed"
  fi
fi

if p1=$(make --no-print-directory promote-check 2>&1) \
   && printf '%s\n' "$p1" | grep -q '^CONTRACTS-FROZEN OK$'; then
  note "P1 contracts frozen OK"
else
  bad "P1 contracts not frozen"
fi

have_refs=0
if git rev-parse --verify --quiet origin/main >/dev/null 2>&1 \
   && git rev-parse --verify --quiet origin/integration >/dev/null 2>&1; then
  have_refs=1
fi

if [ "$have_refs" -eq 1 ]; then
  if ./train-owners.sh origin/main origin/integration | grep -q '^TRAIN-OWNERS OK$'; then
    note "P2 all paths owned OK"
  else
    bad "P2 unassigned path in range"
  fi
else
  bad "P2 refs unavailable"
fi

if [ "$have_refs" -eq 1 ]; then
  BOTWF=0
  p3_fail=0
  if ! git log --format='%H' origin/main..origin/integration > "$SHAS"; then
    bad "P3 git log failed"
    p3_fail=1
  else
    while IFS= read -r sha; do
      [ -n "$sha" ] || continue
      if ! an=$(git log -1 --format='%an <%ae>' "$sha" 2>/dev/null); then
        bad "P3 cannot read $sha"
        p3_fail=1
        continue
      fi
      case "$an" in
        *"[bot]"*|*"bot@"*)
          names=$(git show --name-only --format= "$sha" 2>/dev/null || true)
          wf=0
          while IFS= read -r path; do
            case "$path" in
              .github/workflows/*) wf=1; break ;;
            esac
          done <<< "$names"
          if [ "$wf" -eq 1 ]; then
            echo "  BOT WORKFLOW COMMIT: $sha $an"
            BOTWF=$((BOTWF+1))
          fi
          ;;
      esac
    done < "$SHAS"
  fi
  if [ "$p3_fail" -eq 0 ] && [ "$BOTWF" -eq 0 ]; then
    note "P3 no machine workflow commit OK"
  elif [ "$BOTWF" -gt 0 ]; then
    bad "P3 $BOTWF machine workflow commit(s)"
  fi
else
  bad "P3 refs unavailable"
fi

p4=0
while IFS= read -r evline; do
  low=${evline,,}
  case "$low" in
    *api_key*) p4=1; break ;;
  esac
done <<EOF
$(env)
EOF
unset evline low
if [ "$p4" -eq 1 ]; then
  bad "P4 API key present in env"
else
  note "P4 no API key OK"
fi

MERGED=$(grep -c $'\tMERGED\t' "$NORM" || true)
MERGED=${MERGED//[^0-9]/}
MERGED=${MERGED:-0}
VOK=0
VF="docs/merge-train/cycles/cycle-${CYCLE}.verify"
if [ -f "$VF" ]; then
  VOK=$(tr -d '\r' < "$VF" | grep -c 'SELF-VERIFY OK$' || true)
  VOK=${VOK//[^0-9]/}
  VOK=${VOK:-0}
fi
if [ "$VOK" -ge "$MERGED" ]; then
  note "P5 self-verify $VOK >= merged $MERGED OK"
else
  bad "P5 self-verify $VOK < merged $MERGED"
fi

LANES=0
for n in 1 4 2 3 5; do
  if grep -q "^L${n}"$'\t' "$NORM"; then
    LANES=$((LANES+1))
  fi
done
if [ "$LANES" -eq 5 ]; then
  note "P6 cycle closed OK"
else
  bad "P6 cycle open: $LANES/5 lanes recorded"
fi

if grep -q $'^promoted\tNO$' "$NORM"; then
  note "P7 not yet promoted OK"
else
  bad "P7 cycle already promoted or field malformed"
fi

if ./train-freeze-window.sh >/dev/null; then
  note "P8 freeze window open OK"
else
  bad "P8 freeze window CLOSED"
fi

HEAD_SHA=$(git rev-parse --verify --quiet origin/integration 2>/dev/null || true)
if [ "$APPLY" -eq 1 ]; then
  if [[ ! $HEAD_SHA =~ ^[0-9a-f]{40}$ ]]; then
    bad "P9 origin/integration sha unavailable"
  elif ! command -v gh >/dev/null 2>&1; then
    bad "P9 GitHub CLI not available"
  elif ! CONC=$(gh run list --branch integration --limit 20 \
        --json headSha,conclusion \
        --jq "[.[]|select(.headSha==\"${HEAD_SHA}\")|.conclusion]|unique|join(\",\")"); then
    bad "P9 gh run list failed"
  else
    case "$CONC" in
      success) note "P9 integration CI green OK" ;;
      "") bad "P9 no CI run for $HEAD_SHA" ;;
      *) bad "P9 integration CI conclusions: $CONC" ;;
    esac
  fi
else
  CIE="docs/merge-train/cycles/cycle-${CYCLE}.ci"
  if [[ ! $HEAD_SHA =~ ^[0-9a-f]{40}$ ]]; then
    bad "P9 origin/integration unavailable"
  elif [ ! -f "$CIE" ]; then
    bad "P9 CI evidence absent: $CIE"
  else
    line=$(tr -d '\r' < "$CIE")
    if [ "$line" = "$HEAD_SHA success" ]; then
      note "P9 local CI evidence OK"
    else
      bad "P9 local CI evidence does not match origin/integration success"
    fi
  fi
fi

if [ "$FAIL" -eq 0 ]; then
  echo "PROMOTE-GATE OK (${CYCLE} ${HEAD_SHA:-missing})"
  exit 0
fi
echo "PROMOTE-GATE FAIL: $FAIL condition(s)"
exit 1
