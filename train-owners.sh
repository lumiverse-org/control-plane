#!/usr/bin/env sh
# train-owners.sh — L0-owned. Every path in a range must resolve to an ASSIGNED lane.
# Used by the promotion gate, where the diff spans all five lanes and lane-guard.sh
# (which checks one lane at a time) cannot be applied.
# Usage: ./train-owners.sh <base-ref> <head-ref>
set -eu
BASE="${1:?base ref required}"; HEAD="${2:?head ref required}"
MAP="$(dirname "$0")/lane-paths.tsv"
if [ ! -f "$MAP" ]; then echo "TRAIN-OWNERS FAIL: lane-paths.tsv missing"; exit 2; fi

owner_of() {
  _f="$1"; _own=""
  while IFS='	' read -r _lane _pat; do
    case "$_lane" in ''|\#*) continue ;; esac
    # shellcheck disable=SC2254
    case "$_f" in $_pat) _own="$_lane"; break ;; esac
  done < "$MAP"
  echo "${_own:-X}"
}

VIOL=0
for f in $(git diff --name-only "$BASE"..."$HEAD"); do
  o=$(owner_of "$f")
  if [ "$o" = "X" ]; then
    echo "TRAIN-OWNERS VIOLATION: $f is an UNASSIGNED path (L0D-04)"
    VIOL=$((VIOL+1))
  fi
done

if [ "$VIOL" -eq 0 ]; then echo "TRAIN-OWNERS OK"; exit 0; fi
echo "TRAIN-OWNERS FAIL: $VIOL unassigned path(s)"
exit 1
