#!/usr/bin/env sh
# =============================================================================
# onboard-deadline.sh — L0-owned. The Section 96.2 named deadline (floor item
# F5, spec L8730: "A dated onboarding completion target; missing it is a Red
# signal, not a silent slip"), resolved from its EXPRESSION (D99, L10192) and
# graded against SIG-38 (spec L4567: Amber; Red past deadline).
# Section 10.4: a slot carrying S3 with cd-gate pattern=none must carry the
# SHORTEST deadline in the portfolio (Section 96.6 L8810).
# usage: onboard-deadline.sh [--asof YYYY-MM-DD] [--write]
# exit: 0 clean | 3 signal present (missing or breached) | 1 store contradiction
# =============================================================================
set -u
OB="${OB_ROOT:-docs/onboarding}"
HERE=$(dirname "$0")
ASOF=$(date -u +%Y-%m-%d); WRITE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --asof)  ASOF="$2"; shift 2 ;;
    --write) WRITE=1;   shift ;;
    *) echo "usage: onboard-deadline.sh [--asof YYYY-MM-DD] [--write]" >&2; exit 2 ;;
  esac
done
kv() { awk -F'\t' -v k="$2" '$1==k{print $2; f=1} END{if(!f) print "UNSET"}' "$1"; }
is_date() { case "$1" in [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) return 0 ;; *) return 1 ;; esac; }

missing=0; breached=0; invalid=0; resolved_n=0; minres=""
for d in "$OB"/products/*/; do
  slot=$(basename "$d"); f="$d/deadline.tsv"
  ex=$(kv "$f" source_expr)
  if [ "$ex" = "UNSET" ]; then
    echo "DEADLINE MISSING slot=$slot — floor item F5 is open (Section 96.2 L8730)"; missing=$((missing+1)); continue
  fi
  r=$(OB_ROOT="$OB" "$HERE/onboard-when.sh" resolve "$ex")
  if [ "$WRITE" -eq 1 ]; then
    printf 'source_expr\t%s\nresolved\t%s\nentered\t%s\nstatus\t%s\n' \
      "$ex" "$r" "$(kv "$f" entered)" "$(kv "$f" status)" > "$f"
  fi
  case "$r" in
    UNANCHORED) echo "DEADLINE UNANCHORED slot=$slot expr=$ex — correct until L0 declares the anchor (D99)"; continue ;;
    UNKNOWN-TOKEN|BAD-EXPRESSION|BAD-ANCHOR)
      echo "DEADLINE-INVALID slot=$slot expr=$ex reason=$r"; invalid=$((invalid+1)); continue ;;
  esac
  is_date "$r" || { echo "DEADLINE-INVALID slot=$slot expr=$ex reason=not-a-date"; invalid=$((invalid+1)); continue; }
  resolved_n=$((resolved_n+1))
  if [ -z "$minres" ]; then minres="$r"; else minres=$(printf '%s\n%s\n' "$minres" "$r" | sort | head -1); fi
  st=$(kv "$f" status)
  if [ "$st" != "complete" ] && [ "$r" != "$ASOF" ] && [ "$(printf '%s\n%s\n' "$r" "$ASOF" | sort | head -1)" = "$r" ]; then
    echo "DEADLINE BREACH slot=$slot resolved=$r asof=$ASOF signal=SIG-38 grade=Red"; breached=$((breached+1))
  fi
done

# Section 10.4 — the S3-without-a-CD-gate rule.
for d in "$OB"/products/*/; do
  slot=$(basename "$d")
  case ",$(kv "$d/states.tsv" states)," in *,S3,*) : ;; *) continue ;; esac
  pat="none"; [ -f "$d/cd-gate.tsv" ] && pat=$(kv "$d/cd-gate.tsv" pattern)
  [ "$pat" = "none" ] || continue
  r=$(kv "$d/deadline.tsv" resolved)
  is_date "$r" || continue
  if [ "$r" != "$minres" ]; then
    echo "DEADLINE-INVALID slot=$slot reason=s3-with-no-cd-gate-must-carry-the-shortest-deadline-in-the-portfolio min=$minres has=$r"
    invalid=$((invalid+1))
  fi
done

echo "DEADLINE-SUMMARY resolved=$resolved_n missing=$missing breached=$breached invalid=$invalid earliest=${minres:-none} asof=$ASOF"
[ "$invalid" -eq 0 ] || exit 1
{ [ "$missing" -eq 0 ] && [ "$breached" -eq 0 ]; } || exit 3
exit 0
DL
