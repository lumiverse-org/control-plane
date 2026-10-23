#!/usr/bin/env sh
# =============================================================================
# onboard-qa.sh — L0-owned. The Section 96.6 QA-takeover SLA clock (spec L8830):
# "initial calibrated value: two weeks from the AI-drafted suite landing to QA
# having reviewed, corrected and taken ownership - and a breached SLA is a
# QA-capacity signal at the weekly review, never a personal one."
# Signal on breach: SIG-08 (spec L4537). NEVER prints a person on a breach line.
# The 14 is calibrated configuration: changing it is L0D-17, not an edit here.
# usage: onboard-qa.sh [--asof YYYY-MM-DD] [--slot NN]
# exit: 0 clean | 3 breach present (a signal, not a defect) | 1 invalid clock
# =============================================================================
set -u
OB="${OB_ROOT:-docs/onboarding}"
ASOF=$(date -u +%Y-%m-%d); ONLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --asof) ASOF="$2"; shift 2 ;;
    --slot) ONLY="$2"; shift 2 ;;
    *) echo "usage: onboard-qa.sh [--asof YYYY-MM-DD] [--slot NN]" >&2; exit 2 ;;
  esac
done
kv() { awk -F'\t' -v k="$2" '$1==k{print $2; f=1} END{if(!f) print "UNSET"}' "$1"; }
is_date() { case "$1" in [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) return 0 ;; *) return 1 ;; esac; }
days_between() { a=$(date -u -d "$1" +%s); b=$(date -u -d "$2" +%s); echo $(( (b - a) / 86400 )); }

breach=0; invalid=0; landed=0; owned=0; waiting=0
for d in "$OB"/products/*/; do
  slot=$(basename "$d")
  [ -z "$ONLY" ] || [ "$ONLY" = "$slot" ] || continue
  f="$d/qa.tsv"
  ld=$(kv "$f" suite_landed_on); to=$(kv "$f" taken_over_on)
  by=$(kv "$f" taken_over_by);   sla=$(kv "$f" sla_days)

  case "$sla" in ''|*[!0-9]*) echo "QA-INVALID slot=$slot reason=sla_days-not-a-number"; invalid=$((invalid+1)); continue ;; esac

  if [ "$ld" = "UNSET" ]; then
    if [ "$to" != "UNSET" ]; then
      echo "QA-INVALID slot=$slot reason=ownership-recorded-before-any-suite-landed"; invalid=$((invalid+1))
    else
      echo "QA slot=$slot state=not-landed"
    fi
    continue
  fi
  is_date "$ld" || { echo "QA-INVALID slot=$slot reason=suite_landed_on-not-a-date"; invalid=$((invalid+1)); continue; }
  landed=$((landed+1))

  if [ "$to" != "UNSET" ]; then
    is_date "$to" || { echo "QA-INVALID slot=$slot reason=taken_over_on-not-a-date"; invalid=$((invalid+1)); continue; }
    [ "$by" != "UNSET" ] || { echo "QA-INVALID slot=$slot reason=ownership-without-an-owner"; invalid=$((invalid+1)); continue; }
    n=$(days_between "$ld" "$to")
    [ "$n" -ge 0 ] || { echo "QA-INVALID slot=$slot reason=taken-over-before-the-suite-landed"; invalid=$((invalid+1)); continue; }
    owned=$((owned+1))
    if [ "$n" -gt "$sla" ]; then
      echo "QA-SLA BREACH slot=$slot days=$n sla=$sla signal=SIG-08 state=owned-late"
      breach=$((breach+1))
    else
      echo "QA slot=$slot state=owned days=$n sla=$sla"
    fi
  else
    n=$(days_between "$ld" "$ASOF")
    waiting=$((waiting+1))
    if [ "$n" -gt "$sla" ]; then
      echo "QA-SLA BREACH slot=$slot days=$n sla=$sla signal=SIG-08 state=awaiting-takeover"
      breach=$((breach+1))
    else
      echo "QA slot=$slot state=awaiting-takeover days=$n sla=$sla"
    fi
  fi
done

echo "QA-SUMMARY landed=$landed owned=$owned awaiting=$waiting breaches=$breach invalid=$invalid asof=$ASOF"
[ "$invalid" -eq 0 ] || exit 1
[ "$breach"  -eq 0 ] || exit 3
exit 0
QA
