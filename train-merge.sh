#!/usr/bin/env bash
# train-merge.sh — L0-owned. Preconditions for one lane merge (L0-03-06).
# Usage: ./train-merge.sh --lane <1..5> --pr <n> --cycle <NNN> [--dry-run|--apply]
#        ./train-merge.sh <lane> <pr> <cycle>
#        ./train-merge.sh --help
# Default does not fetch and does not call the GitHub CLI.
# --apply repeats the same local checks. There is no mode that merges or pushes.
# EXIT-CODES: 0=pass 1=fail-closed 2=usage
# NO-ARG: usage
# HELP: 0
# Required evidence: docs/merge-train/cycles/cycle-<CYCLE>.tsv
#   plus an admission line verdict=ADMIT and "L<n> SELF-VERIFY OK".
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
LANE=""
PR=""
CYCLE=""
POSITIONALS=()

usage() {
  cat <<'EOF'
usage: ./train-merge.sh --lane <1..5> --pr <n> --cycle <NNN> [--dry-run|--apply]
       ./train-merge.sh <lane> <pr> <cycle>
       ./train-merge.sh --help

Default is a no-network fail-closed check of local cycle evidence.
--apply does not enable a merge. This tool never merges, pushes, or promotes.

exit 0  MERGE-DRY OK or MERGE-READY OK, and NOT EXECUTED
exit 1  MERGE-REFUSED (fail-closed)
exit 2  usage
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --apply)
      if [ "$MODE" = "dry" ]; then echo "TRAIN-MERGE FAIL: --apply and --dry-run conflict"; exit 2; fi
      MODE=apply; APPLY=1; shift ;;
    --dry-run)
      if [ "$MODE" = "apply" ]; then echo "TRAIN-MERGE FAIL: --apply and --dry-run conflict"; exit 2; fi
      MODE=dry; APPLY=0; shift ;;
    --lane)
      if [ $# -lt 2 ]; then echo "TRAIN-MERGE FAIL: --lane requires a value"; exit 2; fi
      LANE=$2; shift 2 ;;
    --pr)
      if [ $# -lt 2 ]; then echo "TRAIN-MERGE FAIL: --pr requires a value"; exit 2; fi
      PR=$2; shift 2 ;;
    --cycle)
      if [ $# -lt 2 ]; then echo "TRAIN-MERGE FAIL: --cycle requires a value"; exit 2; fi
      CYCLE=$2; shift 2 ;;
    -*)
      echo "TRAIN-MERGE FAIL: unknown argument '$1'"; exit 2 ;;
    *)
      POSITIONALS+=("$1"); shift ;;
  esac
done

if [ "${#POSITIONALS[@]}" -gt 0 ]; then
  if [ -n "$LANE" ] || [ -n "$PR" ] || [ -n "$CYCLE" ]; then
    echo "TRAIN-MERGE FAIL: do not mix flags with positional arguments"
    exit 2
  fi
  if [ "${#POSITIONALS[@]}" -ne 3 ]; then
    echo "TRAIN-MERGE FAIL: positional form is <lane> <pr> <cycle>"
    exit 2
  fi
  LANE=${POSITIONALS[0]}
  PR=${POSITIONALS[1]}
  CYCLE=${POSITIONALS[2]}
fi

if [ -z "$LANE" ] || [ -z "$PR" ] || [ -z "$CYCLE" ]; then
  echo "TRAIN-MERGE FAIL: lane, pr, and cycle are required"
  exit 2
fi
case "$LANE" in
  1|2|3|4|5) ;;
  *) echo "TRAIN-MERGE FAIL: lane must be 1..5"; exit 2 ;;
esac
if [[ ! $PR =~ ^[0-9]{1,10}$ ]]; then
  echo "TRAIN-MERGE FAIL: pr must be an integer"
  exit 2
fi
if [[ ! $CYCLE =~ ^[0-9]{3}$ ]]; then
  echo "TRAIN-MERGE FAIL: cycle must be three digits"
  exit 2
fi

EVID="docs/merge-train/cycles/cycle-${CYCLE}.tsv"
if [ ! -f "$EVID" ]; then
  echo "MERGE-REFUSED: evidence absent: $EVID"
  exit 1
fi

NORM=$(mktemp)
trap 'rm -f "$NORM"' EXIT
tr -d '\r' < "$EVID" > "$NORM"

if grep -q "^L${LANE}"$'\t' "$NORM"; then
  echo "MERGE-REFUSED: L${LANE} already recorded in $EVID"
  exit 1
fi

for n in 1 4 2 3 5; do
  if [ "$n" = "$LANE" ]; then
    break
  fi
  if ! grep -q "^L${n}"$'\t' "$NORM"; then
    echo "MERGE-REFUSED: L${n} has no disposition before L${LANE}"
    exit 1
  fi
done

admit=""
for c in \
  "docs/merge-train/cycles/cycle-${CYCLE}.admit-L${LANE}.txt" \
  "/tmp/admit-${CYCLE}-L${LANE}.txt"
do
  if [ -f "$c" ]; then
    admit=$c
    break
  fi
done
if [ -z "$admit" ]; then
  echo "MERGE-REFUSED: admission evidence absent"
  exit 1
fi
aline=$(tr -d '\r' < "$admit")
if [[ "$aline" == *$'\n'* ]]; then
  echo "MERGE-REFUSED: admission evidence is not a single line"
  exit 1
fi
if [[ "$aline" != "lane=${LANE} pr=${PR} "* || "$aline" != *" verdict=ADMIT" ]]; then
  echo "MERGE-REFUSED: admission is not verdict=ADMIT for lane=${LANE} pr=${PR}"
  exit 1
fi

vf="docs/merge-train/cycles/cycle-${CYCLE}.verify"
if [ ! -f "$vf" ]; then
  echo "MERGE-REFUSED: self-verify evidence absent: $vf"
  exit 1
fi
if ! tr -d '\r' < "$vf" | grep -q "^L${LANE} SELF-VERIFY OK$"; then
  echo "MERGE-REFUSED: L${LANE} SELF-VERIFY OK absent"
  exit 1
fi

if [ "$APPLY" -eq 1 ]; then
  echo "MERGE-READY OK lane=${LANE} pr=${PR} cycle=${CYCLE}"
else
  echo "MERGE-DRY OK lane=${LANE} pr=${PR} cycle=${CYCLE}"
fi
echo "NOT EXECUTED: no merge, no push, no promotion"
exit 0
