#!/usr/bin/env sh
# lane-guard.sh — L0-owned. Enforces PARTITION.md rule 1: one owner per path.
# Usage: ./lane-guard.sh <lane 0..5> <base-ref> <head-ref>
set -eu
LANE="${1:?lane required}"; BASE="${2:?base ref required}"; HEAD="${3:?head ref required}"
MAP="$(dirname "$0")/lane-paths.tsv"
[ -f "$MAP" ] || { echo "LANE-GUARD FAIL: lane-paths.tsv missing"; exit 2; }

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
    echo "LANE-GUARD VIOLATION: $f is an UNASSIGNED path (escalate to L0, L0D-04)"; VIOL=$((VIOL+1))
  elif [ "$o" != "$LANE" ]; then
    echo "LANE-GUARD VIOLATION: $f is owned by lane $o, not lane $LANE"; VIOL=$((VIOL+1))
  fi
done

if [ "$VIOL" -eq 0 ]; then echo "LANE-GUARD OK"; exit 0; fi
echo "LANE-GUARD FAIL: $VIOL violation(s)"; exit 1
