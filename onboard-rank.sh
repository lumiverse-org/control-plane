#!/usr/bin/env sh
# =============================================================================
# onboard-rank.sh — L0-owned. The Section 96.5 sequencing rule (spec L8779):
# "highest classification.reliability_criticality first ... Within equal
# criticality, sequence by business.criticality, then by expected onboarding
# cost, cheapest first."
# Key 4 (slot ascending) is this plan's tie-break, so the order is total.
# Writes docs/onboarding/rank/NN.tsv. GENERATED — never hand-edited.
# usage: onboard-rank.sh [--check]
# =============================================================================
set -u
OB="${OB_ROOT:-docs/onboarding}"
CHECK=0
[ $# -ge 1 ] && [ "$1" = "--check" ] && CHECK=1

kv() { awk -F'\t' -v k="$2" '$1==k{print $2; f=1} END{if(!f) print "UNSET"}' "$1"; }
relk() { case "$1" in critical) echo 1;; high) echo 2;; medium) echo 3;; low) echo 4;; *) echo 9;; esac; }
busk() { case "$1" in high) echo 1;; medium) echo 2;; low) echo 3;; *) echo 9;; esac; }
cstk() { case "$1" in S) echo 1;; M) echo 2;; L) echo 3;; XL) echo 4;; *) echo 9;; esac; }

blocked=0
lines=""
for d in "$OB"/products/*/; do
  slot=$(basename "$d")
  f="$d/facts.tsv"
  r=$(kv "$f" reliability_criticality); b=$(kv "$f" business_criticality); c=$(kv "$f" onboarding_cost_band)
  for pair in "reliability_criticality=$r" "business_criticality=$b" "onboarding_cost_band=$c"; do
    case "$pair" in *=UNSET) echo "RANK-BLOCKED slot=$slot field=${pair%%=*} — DR-L0-07-D"; blocked=$((blocked+1)) ;; esac
  done
  rk=$(relk "$r"); bk=$(busk "$b"); ck=$(cstk "$c")
  for pair in "reliability_criticality=$r:$rk" "business_criticality=$b:$bk" "onboarding_cost_band=$c:$ck"; do
    case "$pair" in *:9)
      v=${pair%%=*}; val=${pair#*=}; val=${val%:9}
      case "$val" in UNSET) : ;; *) echo "RANK-INVALID slot=$slot field=$v value=$val"; blocked=$((blocked+1)) ;; esac ;;
    esac
  done
  lines="$lines$rk $bk $ck $slot
"
done

if [ "$blocked" -gt 0 ]; then
  echo "RANK-SUMMARY blocked=$blocked — no rank written"
  exit 1
fi

mkdir -p "$OB/rank"
order=""
k=0
printf '%s' "$lines" | sort -k1,1n -k2,2n -k3,3n -k4,4 | while read -r rk bk ck slot; do
  [ -n "$slot" ] || continue
  k=$((k+1)); kk=$(printf '%02d' "$k")
  if [ "$CHECK" -eq 0 ]; then
    printf 'rank\t%s\nslot\t%s\nreliability_key\t%s\nbusiness_key\t%s\ncost_key\t%s\n' "$kk" "$slot" "$rk" "$bk" "$ck" \
      > "$OB/rank/$kk.tsv"
  fi
  echo "$slot" >> "$OB/rank/.order.$$"
done
order=$(tr '\n' ',' < "$OB/rank/.order.$$" | sed 's/,$//')
rm -f "$OB/rank/.order.$$"
echo "RANK order=$order"
exit 0
RANK
