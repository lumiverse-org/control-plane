#!/usr/bin/env bash
# train-scripts-selftest.sh — bats-free checks for the four L0-03 tools.
# Asserts each script exists, --help exits 0, the no-arg path exits with a
# documented code, and promote-gate refuses when its cycle evidence is absent
# without calling git or the GitHub CLI.
set -euo pipefail

unset CDPATH
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$ROOT"

PASS=0
FAIL=0
ok() { PASS=$((PASS+1)); printf 'PASS %s\n' "$*"; }
bad() { FAIL=$((FAIL+1)); printf 'FAIL %s\n' "$*"; }

SCRIPTS=(train-preflight.sh train-merge.sh train-close.sh train-promote-gate.sh)

for s in "${SCRIPTS[@]}"; do
  if [ -f "$s" ]; then
    ok "exists $s"
  else
    bad "missing $s"
  fi
  if [ -f "$s" ] && grep -q 'set -euo pipefail' "$s"; then
    ok "pipefail $s"
  else
    bad "pipefail missing in $s"
  fi
  if [ -f "$s" ] && grep -q 'EXIT-CODES: 0=pass 1=fail-closed 2=usage' "$s"; then
    ok "exit codes documented $s"
  else
    bad "exit codes not documented in $s"
  fi
  if [ -f "$s" ] && grep -E -n 'git push|git merge($|[^A-Za-z-])|git revert|gh pr|gh api' "$s"; then
    bad "mutating command present in $s"
  else
    ok "no mutating command in $s"
  fi
done

if grep -E -n 'gh ' train-promote-gate.sh | grep -v 'gh run list' | grep -v 'command -v gh' | grep -v '^[^:]*:#'; then
  bad "train-promote-gate.sh has a gh call other than run list"
else
  ok "promote-gate gh use is read-only run list"
fi

LOG=$(mktemp)
trap 'rm -f "$LOG"' EXIT

git() { printf 'INVOKED git %s\n' "$*" >> "$TRAIN_CMD_LOG"; return 99; }
gh() { printf 'INVOKED gh %s\n' "$*" >> "$TRAIN_CMD_LOG"; return 99; }
export -f git gh
export TRAIN_CMD_LOG="$LOG"

: > "$LOG"
bash -c 'git --version' >/dev/null 2>&1 || true
if grep -q '^INVOKED git ' "$LOG"; then
  ok "command spy intercepts git"
else
  bad "command spy did not intercept git"
fi
: > "$LOG"

run_spied() {
  local name="$1" allowed="$2"
  shift 2
  : > "$LOG"
  set +e
  out=$(bash "$@" 2>&1)
  rc=$?
  set -e
  case " $allowed " in
    *" $rc "*) ok "$name rc=$rc" ;;
    *)
      bad "$name rc=$rc allowed=[$allowed]"
      printf '%s\n' "$out" | sed -n '1,20p' | sed 's/^/    /'
      ;;
  esac
  if [ -s "$LOG" ]; then
    bad "$name invoked a spied command"
    sed 's/^/    /' "$LOG"
  else
    ok "$name did not call git or gh"
  fi
  RUN_OUT=$out
  RUN_RC=$rc
}

run_spied "help train-preflight.sh" "0" ./train-preflight.sh --help
run_spied "help train-merge.sh" "0" ./train-merge.sh --help
run_spied "help train-close.sh" "0" ./train-close.sh --help
run_spied "help train-promote-gate.sh" "0" ./train-promote-gate.sh --help

run_spied "noarg train-merge.sh" "2" ./train-merge.sh
run_spied "noarg train-close.sh" "2" ./train-close.sh
run_spied "noarg train-promote-gate.sh" "2" ./train-promote-gate.sh

cycle=999
if [ -e "docs/merge-train/cycles/cycle-${cycle}.tsv" ]; then
  cycle=998
fi
if [ -e "docs/merge-train/cycles/cycle-${cycle}.tsv" ]; then
  bad "no absent cycle id available to test"
else
  ok "using absent cycle ${cycle}"
  run_spied "promote-gate absent evidence" "1" ./train-promote-gate.sh "$cycle"
  if printf '%s\n' "$RUN_OUT" | grep -q "GATE-FAIL evidence absent: docs/merge-train/cycles/cycle-${cycle}.tsv" \
     && printf '%s\n' "$RUN_OUT" | grep -q '^PROMOTE-GATE FAIL:'; then
    ok "promote-gate refusal text"
    printf '%s\n' "$RUN_OUT" | sed 's/^/    /'
  else
    bad "promote-gate refusal text"
    printf '%s\n' "$RUN_OUT" | sed 's/^/    /'
  fi
  if [ -e "docs/merge-train/cycles/cycle-${cycle}.tsv" ]; then
    bad "promote-gate created cycle-${cycle}.tsv"
  else
    ok "promote-gate did not create evidence"
  fi
  run_spied "promote-gate --apply absent evidence" "1" ./train-promote-gate.sh --apply "$cycle"
  run_spied "merge absent evidence" "1" ./train-merge.sh --lane 1 --pr 1 --cycle "$cycle"
  run_spied "close absent evidence" "1" ./train-close.sh --cycle "$cycle"
fi

# Preflight's no-arg path is the real local check, so it must see real git.
export -nf git gh 2>/dev/null || true
unset -f git gh || true
set +e
pre_out=$(env -u 'BASH_FUNC_git%%' -u 'BASH_FUNC_gh%%' bash ./train-preflight.sh 2>&1)
pre_rc=$?
set -e
pre_last=$(printf '%s\n' "$pre_out" | tail -n 1)
if [ "$pre_rc" -eq 0 ] && [ "$pre_last" = "PREFLIGHT OK" ]; then
  ok "noarg train-preflight.sh rc=0 PREFLIGHT OK"
elif [ "$pre_rc" -eq 1 ] && printf '%s' "$pre_last" | grep -q '^PREFLIGHT FAIL:'; then
  ok "noarg train-preflight.sh rc=1 ${pre_last}"
else
  bad "noarg train-preflight.sh rc=${pre_rc} last=${pre_last}"
  printf '%s\n' "$pre_out" | sed -n '1,20p' | sed 's/^/    /'
fi

printf 'RESULT pass=%s fail=%s\n' "$PASS" "$FAIL"
if [ "$FAIL" -ne 0 ]; then
  exit 1
fi
exit 0
