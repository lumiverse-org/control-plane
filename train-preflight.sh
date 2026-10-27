#!/usr/bin/env bash
# train-preflight.sh — L0-owned. Open-cycle preflight (L0-03-03).
# Usage: ./train-preflight.sh [--dry-run|--apply]
#        ./train-preflight.sh --help
# Default is no-network: no fetch and no GitHub CLI.
# --apply runs git fetch --prune origin, then the same checks.
# This tool does not push, merge, or promote.
# EXIT-CODES: 0=pass 1=fail-closed 2=usage
# NO-ARG: dry-run
# HELP: 0
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

usage() {
  cat <<'EOF'
usage: ./train-preflight.sh [--dry-run|--apply]
       ./train-preflight.sh --help

Default checks the local work tree, origin/integration, and make promote-check.
It does not fetch and does not call the GitHub CLI.
--apply fetches origin first. It still does not push, merge, or promote.

exit 0  PREFLIGHT OK
exit 1  PREFLIGHT FAIL (fail-closed)
exit 2  usage
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --apply)
      if [ "$MODE" = "dry" ]; then echo "PREFLIGHT USAGE: --apply and --dry-run conflict"; exit 2; fi
      MODE=apply; APPLY=1; shift ;;
    --dry-run)
      if [ "$MODE" = "apply" ]; then echo "PREFLIGHT USAGE: --apply and --dry-run conflict"; exit 2; fi
      MODE=dry; APPLY=0; shift ;;
    *) echo "PREFLIGHT USAGE: unknown argument '$1'"; exit 2 ;;
  esac
done

if ! command -v git >/dev/null 2>&1; then
  echo "PREFLIGHT FAIL: git not available"
  exit 1
fi
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "PREFLIGHT FAIL: not a git work tree"
  exit 1
fi

if [ "$APPLY" -eq 1 ]; then
  if ! git fetch --prune origin >/dev/null 2>&1; then
    echo "PREFLIGHT FAIL: git fetch failed"
    exit 1
  fi
fi

if ! porcelain=$(git status --porcelain 2>/dev/null); then
  echo "PREFLIGHT FAIL: git status failed"
  exit 1
fi
if [ -n "$porcelain" ]; then
  echo "PREFLIGHT FAIL: working tree dirty"
  exit 1
fi

if ! tip_sha=$(git rev-parse --verify --quiet origin/integration 2>/dev/null); then
  echo "PREFLIGHT FAIL: not on integration tip"
  exit 1
fi
if ! head_sha=$(git rev-parse HEAD 2>/dev/null); then
  echo "PREFLIGHT FAIL: not on integration tip"
  exit 1
fi
if [ "$head_sha" != "$tip_sha" ]; then
  echo "PREFLIGHT FAIL: not on integration tip"
  exit 1
fi

if ! command -v make >/dev/null 2>&1; then
  echo "PREFLIGHT FAIL: make not available"
  exit 1
fi
if ! p1=$(make --no-print-directory promote-check 2>&1); then
  printf '%s\n' "$p1"
  echo "PREFLIGHT FAIL: promote-check"
  exit 1
fi
if ! printf '%s\n' "$p1" | grep -q '^CONTRACTS-FROZEN OK$'; then
  printf '%s\n' "$p1"
  echo "PREFLIGHT FAIL: contracts not frozen"
  exit 1
fi
printf '%s\n' "$p1"
echo "PREFLIGHT OK"
