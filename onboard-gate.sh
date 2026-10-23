#!/usr/bin/env sh
# =============================================================================
# onboard-gate.sh — L0-owned. The onboarding-track gate: one command, one
# verdict. Plan: implementation/lanes/L0-07-onboarding-track.md L0-07-14.
# OK | PENDING (an L0 or assessor input is absent) | SIGNAL (a true fact worth
# surfacing) | FAIL (the store contradicts itself, or a generated file diverged).
# usage: onboard-gate.sh [--asof YYYY-MM-DD]
# =============================================================================
set -u
OB="${OB_ROOT:-docs/onboarding}"
HERE=$(dirname "$0")
ASOF=$(date -u +%Y-%m-%d)
[ $# -ge 2 ] && [ "$1" = "--asof" ] && ASOF="$2"
export OB_ROOT="$OB"
fails=0; pend=0; sig=0
row() { printf '  %-10s %s\n' "$1" "$2"; }

out=$("$HERE/onboard-when.sh" lint 2>&1);        rc=$?
if [ $rc -eq 0 ]; then row when-lint OK; else row when-lint "FAIL — $(printf '%s' "$out" | head -1)"; fails=$((fails+1)); fi

out=$("$HERE/onboard-floor.sh" --asof "$ASOF" 2>&1); rc=$?
if [ $rc -eq 0 ]; then row floor "OK — $(printf '%s' "$out" | tail -1)"
else row floor "FAIL — $(printf '%s' "$out" | head -1)"; fails=$((fails+1)); fi

out=$("$HERE/onboard-aigate.sh" 2>&1); rc=$?
if [ $rc -eq 0 ]; then row aigate "OK — $(printf '%s' "$out" | tail -1)"
else row aigate "FAIL — $(printf '%s' "$out" | grep INVALID | head -1)"; fails=$((fails+1)); fi

out=$("$HERE/onboard-assess.sh" 2>&1); rc=$?
if [ $rc -eq 0 ]; then row assess "OK — $(printf '%s' "$out" | tail -1)"
else row assess "FAIL — $(printf '%s' "$out" | grep INVALID | head -1)"; fails=$((fails+1)); fi

out=$("$HERE/onboard-rank.sh" 2>&1); rc=$?
if [ $rc -eq 0 ]; then row rank "OK — $(printf '%s' "$out" | tail -1)"
elif printf '%s' "$out" | grep -q 'RANK-INVALID'; then row rank "FAIL — $(printf '%s' "$out" | grep RANK-INVALID | head -1)"; fails=$((fails+1))
else row rank "PENDING — DR-L0-07-D (the eight facts.tsv are unwritten)"; pend=$((pend+1)); fi

out=$("$HERE/onboard-stream.sh" check 2>&1); rc=$?
if [ $rc -eq 0 ]; then row stream "OK — $(printf '%s' "$out" | tail -1)"
else row stream "FAIL — $(printf '%s' "$out" | tail -1) (Section 73.1 permits one stream)"; fails=$((fails+1)); fi

out=$("$HERE/onboard-plan.sh" --check 2>&1); rc=$?
if [ $rc -eq 0 ]; then row plan "OK — $(printf '%s' "$out" | tail -1)"
elif printf '%s' "$out" | grep -q 'PLAN-STALE'; then row plan "FAIL — a generated plan diverged from its generator (invariant 46)"; fails=$((fails+1))
else row plan "PENDING — $(printf '%s' "$out" | head -1)"; pend=$((pend+1)); fi

out=$("$HERE/onboard-qa.sh" --asof "$ASOF" 2>&1); rc=$?
case $rc in
  0) row qa "OK — $(printf '%s' "$out" | tail -1)" ;;
  3) row qa "SIGNAL — $(printf '%s' "$out" | grep BREACH | head -1)"; sig=$((sig+1)) ;;
  *) row qa "FAIL — $(printf '%s' "$out" | grep INVALID | head -1)"; fails=$((fails+1)) ;;
esac

out=$("$HERE/onboard-interim.sh" 2>&1); rc=$?
if [ $rc -eq 0 ]; then row interim "OK — $(printf '%s' "$out" | tail -1)"
else row interim "FAIL — a gate row is invalid"; fails=$((fails+1)); fi

out=$("$HERE/onboard-deadline.sh" --asof "$ASOF" 2>&1); rc=$?
case $rc in
  0) row deadline "OK — $(printf '%s' "$out" | tail -1)" ;;
  3) row deadline "SIGNAL — $(printf '%s' "$out" | tail -1)"; sig=$((sig+1)) ;;
  *) row deadline "FAIL — $(printf '%s' "$out" | grep INVALID | head -1)"; fails=$((fails+1)) ;;
esac

if [ "$fails" -eq 0 ]; then
  echo "ONBOARDING-TRACK GATE OK fails=0 pending=$pend signals=$sig asof=$ASOF"; exit 0
else
  echo "ONBOARDING-TRACK GATE FAIL fails=$fails pending=$pend signals=$sig asof=$ASOF"; exit 1
fi
GATE
