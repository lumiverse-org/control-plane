#!/usr/bin/env sh
# =============================================================================
# lane-guard.sh — v2 — L0-owned root file (PARTITION.md: "root files").
# Enforces PARTITION.md rule 1: ONE OWNER PER PATH.
#
# Usage:  ./lane-guard.sh <lane 0..5> <base-ref> <head-ref>
#
# Exit codes:
#   0  no violations                       (last line: "LANE-GUARD OK")
#   1  one or more violations              (last line: "LANE-GUARD FAIL: N violation(s)")
#   2  configuration error — FAIL CLOSED   (last line: "LANE-GUARD FAIL: configuration error")
#
# Environment overrides. The CI workflow sets these to copies taken from the
# BASE ref, so that a pull request can never supply the rules that judge it
# (MasterSpec v4.0 §53.1: no control rewritable by what it inspects).
#   LG_MAP     path to lane-paths.tsv             default: alongside this script
#   LG_OWNERS  path to lane-owners.tsv            default: alongside this script
#   LG_EXC     path to lane-guard-exceptions.tsv  default: alongside this script
#   LG_PR      pull-request number, for exception matching   default: none
#   LG_TODAY   ISO date used for expiry comparison           default: date -u +%F
# =============================================================================
set -eu

TAB=$(printf '\t')
SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MAP="${LG_MAP:-$SELF_DIR/lane-paths.tsv}"
OWN="${LG_OWNERS:-$SELF_DIR/lane-owners.tsv}"
EXC="${LG_EXC:-$SELF_DIR/lane-guard-exceptions.tsv}"
PR="${LG_PR:-none}"
TODAY="${LG_TODAY:-$(date -u +%Y-%m-%d)}"

CRITICAL="CODEOWNERS Makefile contracts.sha256 lane-paths.tsv lane-owners.tsv
lane-guard.sh lane-guard-exceptions.tsv lane-guard-selftest.sh codeowners-gen.sh
lane-guard-ruleset.json .github/workflows/lane-guard.yml
contracts/ci/lane-guard.yml.frozen contracts/ci/lane-guard.contract.md"

cfgfail() {
  printf 'LANE-GUARD CONFIGURATION ERROR: %s\n' "$*"
  printf 'The guard cannot prove the partition holds, so it refuses to pass.\n'
  printf 'This is an L0 matter. Open BLOCKER: lane-guard configuration.\n'
  printf 'LANE-GUARD FAIL: configuration error\n'
  exit 2
}

lane_name() {
  case "$1" in
    0) printf 'L0 Integrator' ;;
    1) printf 'L1 Registries & Contracts' ;;
    2) printf 'L2 Pipeline & Evidence' ;;
    3) printf 'L3 Reconciler & Provisioning' ;;
    4) printf 'L4 Records, Events & Metrics' ;;
    5) printf 'L5 Access, Infra & Ops' ;;
    X) printf 'UNASSIGNED - no lane owns this (L0D-04)' ;;
    *) printf 'UNKNOWN LANE' ;;
  esac
}

reviewer_of() {
  _l="$1"; _r=""
  if [ -f "$OWN" ]; then
    while IFS="$TAB" read -r _ln _login _disp; do
      case "$_ln" in ''|\#*) continue ;; esac
      if [ "$_ln" = "$_l" ]; then _r="$_login"; break; fi
    done < "$OWN"
  fi
  if [ -n "$_r" ]; then printf '%s' "$_r"; else printf '(no reviewer declared for lane %s)' "$_l"; fi
}

# owner_of <path> -> sets OWNER_LANE, OWNER_LINE, OWNER_PAT. No subshell.
owner_of() {
  _f="$1"; OWNER_LANE="X"; OWNER_LINE="0"; OWNER_PAT="(no rule matched)"; _n=0
  while IFS="$TAB" read -r _lane _pat; do
    _n=$((_n + 1))
    case "$_lane" in ''|\#*) continue ;; esac
    [ -n "${_pat:-}" ] || continue
    # shellcheck disable=SC2254
    case "$_f" in
      $_pat) OWNER_LANE="$_lane"; OWNER_LINE="$_n"; OWNER_PAT="$_pat"; return 0 ;;
    esac
  done < "$MAP"
  return 0
}

# --- validate configuration, fail closed -------------------------------------
[ -f "$MAP" ] || cfgfail "lane-paths.tsv not found at $MAP"
[ -f "$OWN" ] || cfgfail "lane-owners.tsv not found at $OWN"
awk -F"$TAB" '!/^#/ && NF>0 && NF!=2 {bad++} END{exit(bad?1:0)}' "$MAP" \
  || cfgfail "lane-paths.tsv has a row that is not exactly two tab-separated fields"

LANE="${1:-}"; BASE="${2:-}"; HEAD="${3:-}"
[ -n "$LANE" ] && [ -n "$BASE" ] && [ -n "$HEAD" ] \
  || cfgfail "usage: lane-guard.sh <lane 0..5> <base-ref> <head-ref>"
case "$LANE" in 0|1|2|3|4|5) : ;; *) cfgfail "lane must be 0,1,2,3,4 or 5 — got '$LANE'" ;; esac

# --- validate the exception register, fail closed -----------------------------
if [ -f "$EXC" ]; then
  _n=0
  while IFS="$TAB" read -r _id _lane _path _pr _exp _owner _trig _reason; do
    _n=$((_n + 1))
    case "${_id:-}" in ''|\#*) continue ;; esac
    [ -n "${_reason:-}" ] || cfgfail "$EXC line $_n: needs 8 tab-separated fields (id lane path pr expiry owner trigger reason)"
    case "$_id"    in EXC-LG-[0-9][0-9][0-9]) : ;; *) cfgfail "$EXC line $_n: id must match EXC-LG-NNN — got '$_id'" ;; esac
    case "$_lane"  in 0|1|2|3|4|5) : ;; *) cfgfail "$EXC line $_n: lane must be 0..5 — got '$_lane'" ;; esac
    case "$_path"  in *[*?[]*) cfgfail "$EXC line $_n: path must be literal, no glob characters — got '$_path'" ;; esac
    case "$_pr"    in ''|*[!0-9]*) cfgfail "$EXC line $_n: pr must be a pull-request number — got '$_pr'" ;; esac
    case "$_exp"   in [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) : ;; *) cfgfail "$EXC line $_n: expiry must be YYYY-MM-DD — got '$_exp'" ;; esac
    case "$_owner" in @?*) : ;; *) cfgfail "$EXC line $_n: owner must be an @github-login — got '$_owner'" ;; esac
    [ -n "$_trig" ] || cfgfail "$EXC line $_n: deactivation_trigger is mandatory (MasterSpec v4.0 §54.2)"
    for _c in $CRITICAL; do
      [ "$_path" = "$_c" ] && cfgfail "$EXC line $_n: '$_path' is guard-critical and can never be excepted"
    done
  done < "$EXC"
fi

exception_for() {   # exception_for <path> <lane> -> prints "ID|EXPIRY|OWNER" or ""
  _p="$1"; _l="$2"
  [ -f "$EXC" ] || return 0
  _t=$(printf '%s' "$TODAY" | tr -d '-')
  while IFS="$TAB" read -r _id _lane _path _pr _exp _owner _trig _reason; do
    case "${_id:-}" in ''|\#*) continue ;; esac
    [ "$_path" = "$_p" ] || continue
    [ "$_lane" = "$_l" ] || continue
    [ "$_pr" = "$PR" ]   || continue
    _e=$(printf '%s' "$_exp" | tr -d '-')
    [ "$_e" -ge "$_t" ]  || continue
    printf '%s|%s|%s' "$_id" "$_exp" "$_owner"
    return 0
  done < "$EXC"
  return 0
}

TMP=$(mktemp -d 2>/dev/null || mktemp -d -t lg)
trap 'rm -rf "$TMP"' EXIT
: > "$TMP/viol"; : > "$TMP/over"

git diff --raw --no-renames "$BASE...$HEAD" > "$TMP/raw" 2>/dev/null \
  || git diff --raw --no-renames "$BASE"..."$HEAD" > "$TMP/raw" \
  || cfgfail "git diff failed between '$BASE' and '$HEAD'"

report() {   # report <class> <path> <ownerlane> <detail>
  _cls="$1"; _p="$2"; _o="$3"; _d="$4"
  printf '\n'
  printf 'LANE-GUARD VIOLATION [%s]\n' "$_cls"
  printf '  path         : %s\n' "$_p"
  printf '  your lane    : %s  (%s)\n' "$LANE" "$(lane_name "$LANE")"
  printf '  owner lane   : %s  (%s)\n' "$_o" "$(lane_name "$_o")"
  printf '  matched rule : lane-paths.tsv line %s  ->  %s%s%s\n' "$OWNER_LINE" "$OWNER_LANE" "$TAB" "$OWNER_PAT"
  printf '  reviewer     : %s\n' "$(reviewer_of "$_o")"
  printf '  why          : %s\n' "$_d"
  printf '  fix          : remove this path from your branch. Lane %s may not write it.\n' "$LANE"
  printf '                   git checkout %s -- "%s"     # restore the base version\n' "$BASE" "$_p"
  printf '                   git rm --cached -- "%s"     # if you added it\n' "$_p"
  printf '  need it?     : you may NOT edit it yourself. File a Contract Change Request\n'
  printf '                 (docs/escalation/CCR.md) or a blocker (docs/escalation/BLOCKER.md).\n'
  printf '                 Override requires L0 and is described in docs/lane-guard.md.\n'
  printf '  authority    : PARTITION.md rule 1 - one owner per path. No exceptions without L0.\n'
  if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
    printf '::error file=%s,title=lane-guard %s::%s is owned by lane %s (%s), not lane %s. PARTITION.md rule 1.\n' \
      "$_p" "$_cls" "$_p" "$_o" "$(lane_name "$_o")" "$LANE"
  fi
  printf '%s %s\n' "$_cls" "$_p" >> "$TMP/viol"
}

report_plain() {   # report_plain <class> <path> <detail>
  _cls="$1"; _p="$2"; _d="$3"
  printf '\n'
  printf 'LANE-GUARD VIOLATION [%s]\n' "$_cls"
  printf '  path         : %s\n' "$_p"
  printf '  your lane    : %s  (%s)\n' "$LANE" "$(lane_name "$LANE")"
  printf '  why          : %s\n' "$_d"
  printf '  fix          : remove this entry from your branch and push again.\n'
  printf '  authority    : PARTITION.md rule 1 - one owner per path. No exceptions without L0.\n'
  if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
    printf '::error file=%s,title=lane-guard %s::%s\n' "$_p" "$_cls" "$_d"
  fi
  printf '%s %s\n' "$_cls" "$_p" >> "$TMP/viol"
}

printf 'lane-guard v2 — lane %s (%s) — base %s — head %s — pr %s\n' \
  "$LANE" "$(lane_name "$LANE")" "$BASE" "$HEAD" "$PR"
printf 'manifest %s — %s rules\n' "$MAP" "$(grep -vc '^#' "$MAP")"

while IFS= read -r line; do
  [ -n "$line" ] || continue
  meta=${line%%"$TAB"*}
  path=${line#*"$TAB"}
  # meta is ":<srcmode> <dstmode> <srcsha> <dstsha> <status>"
  # shellcheck disable=SC2086
  set -- $meta
  dstmode="${2:-000000}"; status="${5:-M}"

  # --- illegal path shapes ---------------------------------------------------
  case "$path" in
    \"*)   report_plain "PATH-ILLEGAL" "$path" \
             "git quoted this path, so it contains non-ASCII or control bytes. The control plane is ASCII-only."
           continue ;;
    *" "*) report_plain "PATH-ILLEGAL" "$path" \
             "path contains a space. The control plane forbids spaces in tracked paths."
           continue ;;
    -*)    report_plain "PATH-ILLEGAL" "$path" \
             "path begins with '-' and is unsafe to pass to any tool."
           continue ;;
  esac

  # --- guard-critical --------------------------------------------------------
  if [ "$LANE" != "0" ]; then
    _hit=""
    for _c in $CRITICAL; do [ "$path" = "$_c" ] && _hit="$_c"; done
    if [ -n "$_hit" ]; then
      printf '\n'
      printf 'LANE-GUARD VIOLATION [GUARD-CRITICAL]\n'
      printf '  path         : %s\n' "$path"
      printf '  your lane    : %s  (%s)\n' "$LANE" "$(lane_name "$LANE")"
      printf '  owner lane   : 0  (L0 Integrator)\n'
      printf '  why          : this file IS the lane guard. A lane that can edit the guard\n'
      printf '                 is not guarded. MasterSpec v4.0 §53.1: no control that can be\n'
      printf '                 rewritten by what it inspects is a control.\n'
      printf '  fix          : git checkout %s -- "%s"\n' "$BASE" "$path"
      printf '  need it?     : NO OVERRIDE EXISTS for this class. File a Contract Change\n'
      printf '                 Request (docs/escalation/CCR.md). Only L0 may change it.\n'
      printf '  authority    : PARTITION.md rule 1 and rule 2; L0D-LG-2.\n'
      if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
        printf '::error file=%s,title=lane-guard GUARD-CRITICAL::%s is the lane guard itself. Lane %s may not edit it. No override exists.\n' \
          "$path" "$path" "$LANE"
      fi
      printf 'GUARD-CRITICAL %s\n' "$path" >> "$TMP/viol"
      continue
    fi
  fi

  # --- ownership -------------------------------------------------------------
  owner_of "$path"
  if [ "$OWNER_LANE" != "$LANE" ]; then
    _exc=$(exception_for "$path" "$LANE")
    if [ -n "$_exc" ]; then
      _eid=${_exc%%|*}; _rest=${_exc#*|}; _eexp=${_rest%%|*}; _eown=${_rest#*|}
      printf '\n'
      printf 'LANE-GUARD OVERRIDE: %s permitted for lane %s by %s (expires %s, owner %s, pr %s)\n' \
        "$path" "$LANE" "$_eid" "$_eexp" "$_eown" "$PR"
      printf '%s\n' "$_eid" >> "$TMP/over"
    elif [ "$OWNER_LANE" = "X" ]; then
      report "UNASSIGNED-PATH" "$path" "X" \
        "no rule in lane-paths.tsv claims this path. Unassigned paths are blocked for everyone and escalate to L0 (L0D-04)."
    else
      report "FOREIGN-PATH" "$path" "$OWNER_LANE" \
        "PARTITION.md assigns this path to another lane, exclusively."
    fi
    continue
  fi

  # --- entry kind, inside your own tree --------------------------------------
  if [ "$status" != "D" ]; then
    case "$dstmode" in
      120000) report_plain "SYMLINK-ADDED" "$path" \
                "symlinks are forbidden: a symlink inside your tree can point at another lane's tree, which defeats the partition." ;;
      160000) report_plain "SUBMODULE-ADDED" "$path" \
                "gitlinks/submodules are forbidden in the control-plane repository." ;;
    esac
  fi
done < "$TMP/raw"

V=$(grep -c . "$TMP/viol" 2>/dev/null || printf '0')
O=$(grep -c . "$TMP/over" 2>/dev/null || printf '0')
V=$(printf '%s' "$V" | tr -d ' \n'); O=$(printf '%s' "$O" | tr -d ' \n')

printf '\n'
if [ "$V" -eq 0 ]; then
  if [ "$O" -gt 0 ]; then
    printf 'LANE-GUARD: %s override(s) applied under L0 authority. Each expires; see lane-guard-exceptions.tsv.\n' "$O"
  fi
  printf 'LANE-GUARD OK\n'
  exit 0
fi
printf 'LANE-GUARD SUMMARY\n'
sort "$TMP/viol" | awk '{c[$1]++} END{for(k in c) printf "  %-16s %d\n", k, c[k]}'
printf 'LANE-GUARD FAIL: %s violation(s)\n' "$V"
exit 1
