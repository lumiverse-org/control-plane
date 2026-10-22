#!/usr/bin/env sh
# reg-status.sh — L0-owned. The decision queue, ordered for the standing decision window.
# Usage: ./docs/decisions/bin/reg-status.sh [<phase-token>]
#   With no argument: the whole queue.
#   With a phase token: only entries gating at or before that phase, which is what
#   `make decisions-gate` asks before a promotion (L0D-DR-7).
# Last line: REG-STATUS open=<n> p0=<n> p1=<n> p2=<n> p3=<n> overdue=<n>
set -eu
D="$(dirname "$0")/.."
R="$D/register.tsv"
PH="${1:-}"
[ -f "$R" ] || { echo "REG-STATUS FAIL: register.tsv missing"; exit 2; }

# Phase ordinal. Foundation Ph0..Ph7 = 0..7, EH = 8, G1..G8 = 10..17, P1..P8 = 20..27.
ord() {
  case "$1" in
    Ph[0-7]) echo $(( $(printf '%s' "$1" | cut -c3-) )) ;;
    EH)      echo 8 ;;
    G[1-8])  echo $(( 9  + $(printf '%s' "$1" | cut -c2-) )) ;;
    P[1-8])  echo $(( 19 + $(printf '%s' "$1" | cut -c2-) )) ;;
    *)       echo 99 ;;
  esac
}

CUT=99
[ -n "$PH" ] && CUT="$(ord "$PH")"

echo "id       band gates state    title"
awk -F'\t' '!/^#/ && $6=="open"' "$R" | sort -t'	' -k2,2 -k3,3 | while IFS='	' read -r id band gates title decider state blocks sources record opened; do
  printf '%-8s %-4s %-5s %-8s %s\n' "$id" "$band" "$gates" "$state" "$title"
done

OPEN=$(awk -F'\t' '!/^#/ && $6=="open"' "$R" | wc -l | tr -d ' ')
P0=$(awk -F'\t' '!/^#/ && $2=="P0"' "$R" | wc -l | tr -d ' ')
P1=$(awk -F'\t' '!/^#/ && $2=="P1"' "$R" | wc -l | tr -d ' ')
P2=$(awk -F'\t' '!/^#/ && $2=="P2"' "$R" | wc -l | tr -d ' ')
P3=$(awk -F'\t' '!/^#/ && $2=="P3"' "$R" | wc -l | tr -d ' ')

OVERDUE=0
if [ "$CUT" -eq 99 ]; then
  OVERDUE=$OPEN
else
  for g in $(awk -F'\t' '!/^#/{print $3}' "$R"); do
    [ "$(ord "$g")" -le "$CUT" ] && OVERDUE=$((OVERDUE+1))
  done
fi

echo "REG-STATUS open=$OPEN p0=$P0 p1=$P1 p2=$P2 p3=$P3 overdue=$OVERDUE"
