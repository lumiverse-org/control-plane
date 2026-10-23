#!/usr/bin/env sh
# train-admit.sh — L0-owned. Admission check for ONE lane PR in the current cycle.
# Prints exactly one line ending in verdict=ADMIT|REBASE|GATE-FAIL|HALT.
# Usage: ./train-admit.sh <lane 1..5> <pr-number>
set -eu
LANE="${1:?lane 1..5 required}"; PR="${2:?pr number required}"
MAXAGE_H=24   # initial value; the "< 1 day old" rule of PARTITION.md. Changing it is L0D-07.

git fetch --prune origin >/dev/null 2>&1

BR=$(gh pr view "$PR" --json headRefName -q .headRefName)
BASEREF=$(gh pr view "$PR" --json baseRefName -q .baseRefName)
DRAFT=$(gh pr view "$PR" --json isDraft -q .isDraft)
MSTATE=$(gh pr view "$PR" --json mergeStateStatus -q .mergeStateStatus)

case "$BR" in lane/"$LANE"/*) PFX=YES ;; *) PFX=NO ;; esac

if git merge-base --is-ancestor origin/integration "origin/$BR" 2>/dev/null
then REB=YES; else REB=NO; fi

NOW=$(date +%s)
TIP=$(git log -1 --format=%ct "origin/$BR")
AGE=$(( (NOW - TIP) / 3600 ))

GUARD=$(./lane-guard.sh "$LANE" origin/integration "origin/$BR" 2>&1 | tail -1)
case "$GUARD" in "LANE-GUARD OK") G=OK ;; *) G=FAIL ;; esac

CHKOUT=$(gh pr checks "$PR" --required 2>&1) && CHK=PASS || CHK=FAIL
case "$CHKOUT" in
  *"no checks reported"*|*"no required checks"*|*"No checks reported"*) CHK=ABSENT ;;
esac

V=GATE-FAIL
if [ "$BASEREF" != "integration" ] || [ "$PFX" = "NO" ]; then
  V=HALT
elif [ "$REB" = "NO" ] || [ "$MSTATE" = "BEHIND" ] || [ "$AGE" -gt "$MAXAGE_H" ]; then
  V=REBASE
elif [ "$G" = "OK" ] && [ "$DRAFT" = "false" ] && [ "$MSTATE" = "CLEAN" ] \
     && [ "$CHK" = "PASS" ]; then
  V=ADMIT
fi

printf 'lane=%s pr=%s branch=%s base=%s draft=%s rebased=%s age_h=%s guard=%s checks=%s mergestate=%s verdict=%s\n' \
  "$LANE" "$PR" "$BR" "$BASEREF" "$DRAFT" "$REB" "$AGE" "$G" "$CHK" "$MSTATE" "$V"
