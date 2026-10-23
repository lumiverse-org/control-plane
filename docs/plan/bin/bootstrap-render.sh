#!/usr/bin/env sh
# =============================================================================
# bootstrap-render.sh — L0-owned (docs/plan/bin, master/08 Section 2.1).
# Renders docs/bootstrap/exceptions/EXC-BOOT-NNN.yaml from gate-register.tsv.
# Field names and order: MasterSpec v4.0 Section 54.1 (spec L4752-4785) as used
# by the Section 95.2 bootstrap exhibit (spec L8648-8672).
# Exit 0 rendered / 2 configuration error — FAIL CLOSED (Section 64).
# Env: CP  repository root (default: $PWD)
# =============================================================================
set -u
CP="${CP:-$PWD}"
REG="$CP/docs/bootstrap/gate-register.tsv"
SCOPE="$CP/docs/bootstrap/repo-scope.tsv"
OUT="$CP/docs/bootstrap/exceptions"
TAB=$(printf '\t')
cfgfail() { printf 'BOOTSTRAP-RENDER FAIL: configuration error — %s\n' "$1"; exit 2; }
[ -f "$REG" ]   || cfgfail "gate-register.tsv not found at $REG"
[ -f "$SCOPE" ] || cfgfail "repo-scope.tsv not found at $SCOPE"
awk -F"$TAB" '!/^#/ && NF>0 && NF!=14 {bad++} END{exit(bad?1:0)}' "$REG" \
  || cfgfail "gate-register.tsv has a row that is not exactly 14 tab-separated fields"
REPOS=$(awk -F"$TAB" '!/^#/ && $2=="bootstrap" {printf "%s%s", sep, $1; sep=", "}' "$SCOPE")
[ -n "$REPOS" ] || cfgfail "no repository is in bootstrap mode; there is nothing to except"
mkdir -p "$OUT" || cfgfail "cannot create $OUT"
COMMON='full CI verification contract on every push; append-only history, nothing rewritten; production deploys still require the explicit approval event'
n=0
while IFS="$TAB" read -r id thr scope policy risk extra trig start expiry review renewals closure closed line; do
  case "${id:-}" in ''|\#*) continue ;; esac
  comp="$COMMON"
  [ "$extra" = "-" ] || comp="$comp; $extra"
  if [ "$closure" = "-" ]; then clo="null"; else clo="$closure"; fi
  {
    printf '# %s — RENDERED by docs/plan/bin/bootstrap-render.sh from docs/bootstrap/gate-register.tsv.\n' "$id"
    printf '# DO NOT HAND-EDIT. Edit the register and re-render; docs/plan/bin/bootstrap-check.sh compares.\n'
    printf '# Fields: MasterSpec v4.0 Section 54.1 (spec L4752-4785). Bootstrap shape: Section 95.2 (spec L8648-8672).\n'
    printf '# Gate source: spec %s. Threshold: %s (docs/bootstrap/activation-checklist.tsv).\n' "$line" "$thr"
    printf -- '- id: %s\n' "$id"
    printf '  type: bootstrap\n'
    printf '  scope: %s\n' "$scope"
    printf '  affected:\n'
    printf '    repositories: [%s]\n' "$REPOS"
    printf '  policy: %s\n' "$policy"
    printf '  reason: no second context-holding human holds Write on these repositories during the solo build\n'
    printf '  risk_accepted: %s\n' "$risk"
    printf '  compensating_control: %s\n' "$comp"
    printf '  compensating_control_record: CI run history on the named repositories\n'
    printf '  compensating_control_cadence: per-push\n'
    printf '  requester: founder\n'
    printf '  authority: founder\n'
    printf '  owner: founder\n'
    printf '  start: %s\n' "$start"
    printf '  expiry: %s\n' "$expiry"
    printf '  review_date: %s\n' "$review"
    printf '  renewals: %s\n' "$renewals"
    printf '  deactivation_trigger: %s\n' "$trig"
    printf '  closure: %s\n' "$clo"
  } > "$OUT/$id.yaml" || cfgfail "cannot write $OUT/$id.yaml"
  n=$((n + 1))
done < "$REG"
printf 'BOOTSTRAP-RENDER OK: %s exception(s) into %s\n' "$n" "$OUT"
exit 0
