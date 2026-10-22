#!/usr/bin/env sh
# =============================================================================
# onboard-aigate.sh — L0-owned. The S10 and S19 AI-safety gates.
# MasterSpec v4.0 Section 96.6 L8817 (S10) and L8825 (S19), both verbatim:
# "No AI-assisted session opens the repository until the S<n> check passes —
# universal floor". Section 33 restates the S10 half; invariant 111 (L9597)
# names the S19 intake gate as one of the three no-customer-data detectors.
# FAIL-CLOSED: UNSET is BLOCKED, never "not applicable".
# usage: onboard-aigate.sh [--slot NN] [--verdict NN]
# =============================================================================
set -u
OB="${OB_ROOT:-docs/onboarding}"
ONLY=""; VERDICT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --slot)    ONLY="$2";    shift 2 ;;
    --verdict) VERDICT="$2"; shift 2 ;;
    *) echo "usage: onboard-aigate.sh [--slot NN] [--verdict NN]" >&2; exit 2 ;;
  esac
done

is_date() { case "$1" in [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) return 0 ;; *) return 1 ;; esac; }
kv() { awk -F'\t' -v k="$2" '$1==k{print $2; f=1} END{if(!f) print "UNSET"}' "$1"; }

invalid=0; blocked=0; permitted=0
[ -n "$VERDICT" ] && ONLY="$VERDICT"

for d in "$OB"/products/*/; do
  slot=$(basename "$d")
  [ -z "$ONLY" ] || [ "$ONLY" = "$slot" ] || continue
  g="$d/gates.tsv"
  [ -f "$g" ] || { echo "AIGATE slot=$slot verdict=INVALID reason=no-gates-file"; invalid=$((invalid+1)); continue; }

  s10s=$(kv "$g" s10_status);   s10r=$(kv "$g" s10_rotation)
  s10i=$(kv "$g" s10_incident_record); s10c=$(kv "$g" s10_checked_on)
  s19s=$(kv "$g" s19_status);   s19rm=$(kv "$g" s19_removed_on)
  s19n=$(kv "$g" s19_notification); s19o=$(kv "$g" s19_deletion_obligation); s19c=$(kv "$g" s19_checked_on)

  s10="BLOCKED"; s10why="s10-gate"
  if [ "$s10s" = "pass" ]; then
    if ! is_date "$s10c"; then s10="INVALID"; s10why="s10-pass-without-check-date"
    elif [ "$s10r" = "not-applicable" ] && [ "$s10i" != "none" ]; then s10="INVALID"; s10why="s10-no-exposure-but-incident-record-claimed"
    elif [ "$s10r" = "done" ] && { [ "$s10i" = "none" ] || [ "$s10i" = "UNSET" ]; }; then s10="INVALID"; s10why="s10-rotation-without-incident-record"
    elif [ "$s10r" != "done" ] && [ "$s10r" != "not-applicable" ]; then s10="INVALID"; s10why="s10-pass-without-rotation-disposition"
    else s10="PASS"; s10why="-"; fi
  elif [ "$s10s" = "fail" ]; then s10why="s10-gate-failed"
  fi

  s19="BLOCKED"; s19why="s19-gate"
  if [ "$s19s" = "pass" ]; then
    if ! is_date "$s19c"; then s19="INVALID"; s19why="s19-pass-without-check-date"
    elif ! is_date "$s19rm" && [ "$s19rm" != "not-applicable" ]; then s19="INVALID"; s19why="s19-no-removal-there-is-no-rotation-equivalent-remedy"
    elif [ "$s19n" != "done" ] && [ "$s19n" != "not-required-by-classification" ] && [ "$s19n" != "not-applicable" ]; then s19="INVALID"; s19why="s19-notification-disposition-missing"
    elif [ "$s19o" = "UNSET" ]; then s19="INVALID"; s19why="s19-deletion-obligation-not-recorded"
    else s19="PASS"; s19why="-"; fi
  elif [ "$s19s" = "fail" ]; then s19why="s19-gate-failed"
  fi

  if [ "$s10" = "INVALID" ] || [ "$s19" = "INVALID" ]; then
    v="INVALID"; why=$([ "$s10" = "INVALID" ] && echo "$s10why" || echo "$s19why"); invalid=$((invalid+1))
  elif [ "$s10" = "PASS" ] && [ "$s19" = "PASS" ]; then
    v="PERMITTED"; why="-"; permitted=$((permitted+1))
  else
    v="BLOCKED"; why=$([ "$s10" != "PASS" ] && echo "$s10why" || echo "$s19why"); blocked=$((blocked+1))
  fi
  echo "AIGATE slot=$slot s10=$s10 s19=$s19 verdict=$v reason=$why"
done

echo "AIGATE-SUMMARY permitted=$permitted blocked=$blocked invalid=$invalid"
[ "$invalid" -eq 0 ] || exit 1
exit 0
