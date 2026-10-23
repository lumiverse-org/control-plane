#!/usr/bin/env sh
# =============================================================================
# bootstrap-check.sh — L0-owned. The pre-flight L0 runs before CI does.
# Implements the Phase 1 minimal rule set (expiry, owner, deactivation trigger —
# MasterSpec v4.0 Section 95.2, spec L8677) plus the bootstrap-specific rules of
# Section 95.1/95.2 and the renewal rule of Section 54.2 (spec L4791).
# It does NOT replace L1's registry validator; it catches the same class of fault
# one step earlier, on L0's authored source.
# Exit 0 BOOTSTRAP-CHECK OK / 1 violations / 2 configuration error — FAIL CLOSED.
# Env: CP repository root; BOOT_TODAY ISO date for expiry comparison (tests only).
# =============================================================================
set -u
CP="${CP:-$PWD}"
REG="$CP/docs/bootstrap/gate-register.tsv"
SCOPE="$CP/docs/bootstrap/repo-scope.tsv"
DIR="$CP/docs/bootstrap/exceptions"
DEC="$CP/docs/plan/decisions"
TODAY="${BOOT_TODAY:-$(date -u +%F)}"
TAB=$(printf '\t')
V=0
cfgfail() { printf 'BOOTSTRAP-CHECK FAIL: configuration error — %s\n' "$1"; exit 2; }
viol()    { printf 'BOOTSTRAP-VIOLATION [%s] %s: %s\n' "$1" "$2" "$3"; V=$((V + 1)); }

[ -f "$REG" ]   || cfgfail "gate-register.tsv not found at $REG"
[ -f "$SCOPE" ] || cfgfail "repo-scope.tsv not found at $SCOPE"
[ -d "$DIR" ]   || cfgfail "exceptions directory not found at $DIR"
awk -F"$TAB" '!/^#/ && NF>0 && NF!=14 {bad++} END{exit(bad?1:0)}' "$REG" \
  || cfgfail "gate-register.tsv has a row that is not exactly 14 tab-separated fields"
awk -F"$TAB" '!/^#/ && NF>0 && NF!=3 {bad++} END{exit(bad?1:0)}' "$SCOPE" \
  || cfgfail "repo-scope.tsv has a row that is not exactly 3 tab-separated fields"
command -v diff >/dev/null || cfgfail "diff not available; the render comparison cannot run"

# B9 — one exception per relaxed gate (Section 95.2 L8646; invariant 77 same-scope rule)
for s in $(awk -F"$TAB" '!/^#/{print $3}' "$REG" | sort | uniq -d); do
  viol SCOPE-DUPLICATE "$s" "two exceptions name one gate; Section 95.2 L8646 says one per relaxed gate"
done

TD=$(printf '%s' "$TODAY" | tr -d '-')
while IFS="$TAB" read -r id thr scope policy risk extra trig start expiry review renewals closure closed line; do
  case "${id:-}" in ''|\#*) continue ;; esac
  case "$id" in EXC-BOOT-[0-9][0-9][0-9]) : ;; *) viol ID-SHAPE "$id" "id must match EXC-BOOT-NNN" ;; esac
  [ -f "$DIR/$id.yaml" ] || viol NOT-RENDERED "$id" "no rendered record at docs/bootstrap/exceptions/$id.yaml"
  # B3 — expiry mandatory (invariant 77, spec L9554)
  case "$expiry" in
    [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) : ;;
    *) viol NO-EXPIRY "$id" "expiry must be YYYY-MM-DD; invariant 77 rejects an exception without one" ;;
  esac
  # B5 — deactivation trigger mandatory (Section 95.2, spec L8676)
  case "${trig:-}" in ''|-|null) viol NO-TRIGGER "$id" "deactivation_trigger is mandatory (Section 95.2 L8676)" ;; esac
  # B10 — renewals numeric
  case "$renewals" in ''|*[!0-9]*) viol RENEWALS "$id" "renewals must be a non-negative integer" ;; esac
  # B7 — an expiry in the past with the gate still unarmed is SIG-39 (spec L4568)
  if [ "$closure" = "-" ]; then
    _e=$(printf '%s' "$expiry" | tr -d '-')
    case "$_e" in
      [0-9]*) [ "$_e" -ge "$TD" ] || viol SIG-39 "$id" "expired $expiry with the gate still unarmed; Red on the Founder view" ;;
    esac
  else
    case "$closure" in
      expired|remediated|promoted_to_policy|trigger_satisfied) : ;;
      *) viol CLOSURE "$id" "closure must be one of expired|remediated|promoted_to_policy|trigger_satisfied (Section 54.1 L4782)" ;;
    esac
    case "$closed" in
      [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) : ;;
      *) viol CLOSURE-DATE "$id" "a closed exception carries closed_on as YYYY-MM-DD" ;;
    esac
  fi
  # B11 — third renewal requires the re-affirmation record (Section 54.2, spec L4791)
  if [ "$closure" = "-" ] && [ "${renewals:-0}" -ge 3 ] 2>/dev/null; then
    ls "$DEC"/*reaffirm-"$id".md >/dev/null 2>&1 \
      || viol REAFFIRM "$id" "renewals=$renewals with no docs/plan/decisions/*reaffirm-$id.md; Section 54.2 L4791 forces remediate, promote or re-affirm"
  fi
done < "$REG"

# B4/B6 — owner present, and every named repository is in bootstrap mode (Section 95.2 L8678)
for f in "$DIR"/*.yaml; do
  [ -e "$f" ] || continue
  b=$(basename "$f" .yaml)
  [ "$(grep -c '^  owner: ' "$f")" = "1" ] || viol NO-OWNER "$b" "exactly one owner line is required (Section 95.2 L8676)"
  reps=$(sed -n 's/^    repositories: \[\(.*\)\]$/\1/p' "$f" | tr ',' '\n' | sed 's/^ *//; s/ *$//')
  [ -n "$reps" ] || viol NO-REPOS "$b" "the exception names no repository; Section 95.2 L8676 requires it"
  for r in $reps; do
    m=$(awk -F"$TAB" -v r="$r" '!/^#/ && $1==r {print $2}' "$SCOPE")
    [ "$m" = "bootstrap" ] || viol FOREIGN-REPO "$b" "repository '$r' has mode '${m:-armed}'; Section 95.2 L8678 forbids covering it"
  done
done

# B1 — the rendered tree must be exactly what the register renders (no hand-edits)
TMP=$(mktemp -d 2>/dev/null || mktemp -d -t bck) || cfgfail "mktemp failed"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/docs/bootstrap" "$TMP/docs/plan/bin"
cp "$REG" "$SCOPE" "$TMP/docs/bootstrap/" || cfgfail "cannot stage the register"
CP="$TMP" sh "$CP/docs/plan/bin/bootstrap-render.sh" >/dev/null || cfgfail "bootstrap-render.sh failed on the staged copy"
if ! diff -r "$DIR" "$TMP/docs/bootstrap/exceptions" >/dev/null 2>&1; then
  diff -r "$DIR" "$TMP/docs/bootstrap/exceptions" 2>&1 | sed 's/^/  /'
  viol HAND-EDITED "docs/bootstrap/exceptions" "a rendered record differs from what the register renders; re-render, do not edit"
fi

printf '\n'
if [ "$V" -eq 0 ]; then printf 'BOOTSTRAP-CHECK OK\n'; exit 0; fi
printf 'BOOTSTRAP-CHECK FAIL: %s violation(s)\n' "$V"
exit 1
