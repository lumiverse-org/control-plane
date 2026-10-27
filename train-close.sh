#!/usr/bin/env bash
# train-close.sh — L0-owned. Close one cycle record (L0-03-08).
# Usage: ./train-close.sh --cycle <NNN> [--dry-run|--apply]
#        ./train-close.sh <NNN>
#        ./train-close.sh --help
# Default checks the cycle file and does not write, commit, or push.
# --apply updates the notes field and regenerates the cycle log locally.
# There is no mode that commits or pushes.
# EXIT-CODES: 0=pass 1=fail-closed 2=usage
# NO-ARG: usage
# HELP: 0
# Required evidence: docs/merge-train/cycles/cycle-<CYCLE>.tsv
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
usage: ./train-close.sh --cycle <NNN> [--dry-run|--apply]
       ./train-close.sh <NNN>
       ./train-close.sh --help

Default is a no-network fail-closed check. It does not write or call the GitHub CLI.
--apply rewrites the local notes field and runs make train-log.
It still does not commit, push, merge, or promote.

exit 0  CLOSE-DRY OK or CLOSE-APPLIED, and NOT EXECUTED
exit 1  CLOSE-REFUSED (fail-closed)
exit 2  usage
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --apply)
      if [ "$MODE" = "dry" ]; then echo "TRAIN-CLOSE FAIL: --apply and --dry-run conflict"; exit 2; fi
      MODE=apply; APPLY=1; shift ;;
    --dry-run)
      if [ "$MODE" = "apply" ]; then echo "TRAIN-CLOSE FAIL: --apply and --dry-run conflict"; exit 2; fi
      MODE=dry; APPLY=0; shift ;;
    --cycle)
      if [ $# -lt 2 ]; then echo "TRAIN-CLOSE FAIL: --cycle requires a value"; exit 2; fi
      if [ -n "$CYCLE" ]; then echo "TRAIN-CLOSE FAIL: cycle given twice"; exit 2; fi
      CYCLE=$2; shift 2 ;;
    -*)
      echo "TRAIN-CLOSE FAIL: unknown argument '$1'"; exit 2 ;;
    *)
      if [ -n "$POSITIONAL" ]; then echo "TRAIN-CLOSE FAIL: unexpected argument '$1'"; exit 2; fi
      POSITIONAL=$1; shift ;;
  esac
done

if [ -n "$POSITIONAL" ]; then
  if [ -n "$CYCLE" ] && [ "$CYCLE" != "$POSITIONAL" ]; then
    echo "TRAIN-CLOSE FAIL: conflicting cycle"
    exit 2
  fi
  CYCLE=$POSITIONAL
fi

if [ -z "$CYCLE" ]; then
  echo "TRAIN-CLOSE FAIL: cycle required"
  exit 2
fi
if [[ ! $CYCLE =~ ^[0-9]{3}$ ]]; then
  echo "TRAIN-CLOSE FAIL: cycle must be three digits"
  exit 2
fi

EVID="docs/merge-train/cycles/cycle-${CYCLE}.tsv"
if [ ! -f "$EVID" ]; then
  echo "CLOSE-REFUSED: evidence absent: $EVID"
  exit 1
fi

NORM=$(mktemp)
trap 'rm -f "$NORM"' EXIT
tr -d '\r' < "$EVID" > "$NORM"

rc=0
for key in cycle date base promoted notes; do
  if ! grep -q "^${key}"$'\t' "$NORM"; then
    echo "CLOSE-REFUSED: field absent: $key"
    rc=1
  fi
done

for n in 1 4 2 3 5; do
  count=$(grep -c "^L${n}"$'\t' "$NORM" || true)
  count=${count//[^0-9]/}
  count=${count:-0}
  if [ "$count" -ne 1 ]; then
    echo "CLOSE-REFUSED: L${n} recorded ${count} time(s)"
    rc=1
  fi
done

while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    L[12345]$'\t'*) ;;
    *) continue ;;
  esac
  lane=${line%%$'\t'*}
  rest=${line#*$'\t'}
  disp=${rest%%$'\t'*}
  case "$disp" in
    MERGED|SKIPPED|HALTED|NONE) ;;
    *)
      echo "CLOSE-REFUSED: ${lane} illegal disposition '${disp}'"
      rc=1
      continue
      ;;
  esac
  if [ "$disp" = "MERGED" ]; then
    sha=$(printf '%s\n' "$line" | awk -F'\t' '{
      for (i = 1; i <= NF; i++) if ($i ~ /^merge=/) { sub(/^merge=/, "", $i); print $i; exit }
    }')
    if [[ ! $sha =~ ^[0-9a-f]{40}$ ]] || ! git cat-file -e "${sha}^{commit}" >/dev/null 2>&1; then
      echo "CLOSE-REFUSED: ${lane} merge sha missing"
      rc=1
    fi
  fi
done < "$NORM"

if [ "$rc" -ne 0 ]; then
  exit 1
fi

if [ "$APPLY" -eq 0 ]; then
  echo "CLOSE-DRY OK cycle=${CYCLE} lanes=5"
  echo "NOT EXECUTED: no commit, no push"
  exit 0
fi

halts=$(find docs/merge-train/cycles -maxdepth 1 -name "cycle-${CYCLE}.halt.md" | wc -l | tr -d ' ')
tmp=$(mktemp)
trap 'rm -f "$NORM" "$tmp"' EXIT
while IFS= read -r line || [ -n "$line" ]; do
  line=${line%$'\r'}
  case "$line" in
    notes$'\t'*) printf 'notes\thalts=%s\n' "$halts" ;;
    *) printf '%s\n' "$line" ;;
  esac
done < "$EVID" > "$tmp"
mv "$tmp" "$EVID"
trap 'rm -f "$NORM"' EXIT

if ! make --no-print-directory train-log; then
  echo "CLOSE-REFUSED: train-log failed after notes update"
  exit 1
fi
echo "CLOSE-APPLIED cycle=${CYCLE} lanes=5"
echo "NOT EXECUTED: no commit, no push"
exit 0
