#!/usr/bin/env sh
# =============================================================================
# onboard-interim.sh — L0-owned. The Section 96.6 interim rule (spec L8830).
# Manual feature work continues under the recorded accepted risks of the
# pre-onboarding block; only AI-assisted feature work waits for the
# verification contract (portfolio invariant 1, spec L9451).
# S10/S19 are consulted FIRST: they close the repository to every AI-assisted
# session, not merely to feature work (Section 96.6 L8817, L8825).
# usage: onboard-interim.sh [--slot NN]
# exit: 0 (BLOCKED is a legitimate state) | 1 if a gate row is INVALID
# =============================================================================
set -u
OB="${OB_ROOT:-docs/onboarding}"
HERE=$(dirname "$0")
ONLY=""
[ $# -ge 2 ] && [ "$1" = "--slot" ] && ONLY="$2"
kv() { awk -F'\t' -v k="$2" '$1==k{print $2; f=1} END{if(!f) print "UNSET"}' "$1"; }

manual_ok=0; ai_ok=0; invalid=0
for d in "$OB"/products/*/; do
  slot=$(basename "$d")
  [ -z "$ONLY" ] || [ "$ONLY" = "$slot" ] || continue
  i="$d/interim.tsv"
  bp=$(kv "$i" block_present); ar=$(kv "$i" accepted_risks_recorded); vc=$(kv "$i" verification_contract)

  # ---- question 1: manual feature work
  if [ "$bp" != "yes" ]; then m="BLOCKED"; mr="no-pre-onboarding-block"
  elif [ "$ar" != "yes" ]; then m="BLOCKED"; mr="no-recorded-accepted-risks"
  else m="PERMITTED"; mr="-"; manual_ok=$((manual_ok+1)); fi

  # ---- question 2: AI-assisted feature work
  g=$(OB_ROOT="$OB" "$HERE/onboard-aigate.sh" --slot "$slot" | head -1)
  s10=$(printf '%s' "$g" | awk '{print $3}'); s19=$(printf '%s' "$g" | awk '{print $4}')
  case "$g" in *" s10="*) : ;; *) s10="s10=INVALID" ;; esac    # e.g. no gates.tsv at all
  if [ "$s10" = "s10=INVALID" ] || [ "$s19" = "s19=INVALID" ]; then
    a="INVALID"; ar2="gate-row-invalid-see-onboard-aigate"; invalid=$((invalid+1))
  elif [ "$s10" != "s10=PASS" ]; then a="BLOCKED"; ar2="s10-gate"
  elif [ "$s19" != "s19=PASS" ]; then a="BLOCKED"; ar2="s19-gate"
  elif [ "$vc" != "present" ]; then a="BLOCKED"; ar2="no-verification-contract"
  else a="PERMITTED"; ar2="-"; ai_ok=$((ai_ok+1)); fi

  echo "INTERIM slot=$slot manual=$m reason=$mr ai=$a reason=$ar2"
done

echo "INTERIM-SUMMARY manual_permitted=$manual_ok ai_permitted=$ai_ok invalid=$invalid"
[ "$invalid" -eq 0 ] || exit 1
exit 0
INTERIM
