#!/usr/bin/env sh
# =============================================================================
# onboard-assess.sh — L0-owned. The Section 96.6 intake gap assessment checker.
# "Onboarding therefore begins with a recorded intake gap assessment per
# product, authored from the named template artifact in the control plane
# (templates/intake-gap-assessment.md) ... the recorded assessment is always
# written by the human assessor (D72)." (spec L8783)
# The template itself has NO owning lane — DR-L0-07-A. This script consumes it
# by version string only and never writes it.
# usage: onboard-assess.sh [--slot NN]
# =============================================================================
set -u
OB="${OB_ROOT:-docs/onboarding}"
ONLY=""
[ $# -ge 2 ] && [ "$1" = "--slot" ] && ONLY="$2"

kv() { awk -F'\t' -v k="$2" '$1==k{print $2; f=1} END{if(!f) print "UNSET"}' "$1"; }
is_date() { case "$1" in [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) return 0 ;; *) return 1 ;; esac; }

recorded=0; notrec=0; invalid=0
for d in "$OB"/products/*/; do
  slot=$(basename "$d")
  [ -z "$ONLY" ] || [ "$ONLY" = "$slot" ] || continue
  a="$d/assessment.tsv"; sh_="$d/standard.tsv"; fa="$d/facts.tsv"
  st=$(kv "$a" status); by=$(kv "$a" recorded_by); on=$(kv "$a" recorded_on)
  tv=$(kv "$a" template_version); ml=$(kv "$a" maturity_level_at_intake)
  md=$(kv "$a" machine_drafted)
  prof=$(kv "$fa" conformance_profile)

  if [ "$st" != "recorded" ]; then
    r="no-recorded-assessment"
    [ "$st" = "machine-drafted" ] && r="machine-draft-is-not-an-assessment-D72"
    echo "ASSESS slot=$slot verdict=NOT-RECORDED reason=$r"; notrec=$((notrec+1)); continue
  fi

  why=""
  [ "$by" = "UNSET" ]                 && why="recorded-without-a-human-assessor-D72"
  [ -z "$why" ] && ! is_date "$on"    && why="recorded-without-a-date"
  [ -z "$why" ] && [ "$tv" = "UNSET" ] && why="no-template-version-DR-L0-07-A"
  if [ -z "$why" ]; then
    case "$ml" in 0|1|2|3|4|5|6|7) : ;; *) why="maturity-level-outside-0-7-Section-65" ;; esac
  fi
  if [ -z "$why" ] && [ ! -f "$sh_" ]; then why="no-coverage-sheet"; fi

  gaps=0; equivs=0
  if [ -z "$why" ]; then
    n=$(awk -F'\t' '!/^#/' "$sh_" | wc -l | tr -d ' ')
    [ "$n" -eq 10 ] || why="coverage-sheet-is-$n-rows-not-10"
  fi
  if [ -z "$why" ]; then
    OIFS=$IFS; IFS=$(printf '\t')
    while read -r id v ev disp; do
      case "$id" in \#*|'') continue ;; esac
      case "$v" in
        met) : ;;
        gap) gaps=$((gaps+1))
             case "$disp" in scheduled-step|accepted-risk) : ;;
               *) why="gap-$id-has-no-disposition"; break ;; esac ;;
        equivalent) equivs=$((equivs+1))
             [ "$ev" != "UNSET" ] || { why="equivalent-$id-names-no-evidence"; break; }
             [ "$prof" != "service" ] || { why="equivalent-$id-on-a-service-profile"; break; } ;;
        *) why="row-$id-unanswered"; break ;;
      esac
    done < "$sh_"
    IFS=$OIFS
  fi

  if [ -n "$why" ]; then
    echo "ASSESS slot=$slot verdict=INVALID reason=$why"; invalid=$((invalid+1))
  else
    echo "ASSESS slot=$slot verdict=RECORDED by=$by maturity=$ml gaps=$gaps equivalents=$equivs drafted=$md"
    recorded=$((recorded+1))
  fi
done

echo "ASSESS-SUMMARY recorded=$recorded not_recorded=$notrec invalid=$invalid"
[ "$invalid" -eq 0 ] || exit 1
exit 0
ASSESS
