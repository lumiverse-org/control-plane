#!/usr/bin/env sh
# reg-close.sh — L0-owned. Close one register entry. L0 ONLY (L0D-DR-3).
# Usage: ./docs/decisions/bin/reg-close.sh <REG-nnn> <closed|declined|withdrawn> <subject-file>
#   <subject-file> is a plain-text file whose lines become options_considered and evidence.
# Last line: REG-CLOSE OK <REG-nnn> -> <state> <record-path>
set -eu
D="$(dirname "$0")/.."
R="$D/register.tsv"
ID="${1:?REG id required}"; STATE="${2:?state required}"; SUBJ="${3:?subject file required}"
TODAY="$(date -u +%F)"

case "$STATE" in closed|declined|withdrawn) ;; *) echo "REG-CLOSE FAIL: bad state $STATE"; exit 2 ;; esac
grep -q "^$ID	" "$R" || { echo "REG-CLOSE FAIL: $ID not in register"; exit 2; }
[ "$(awk -F'\t' -v i="$ID" '$1==i{print $6}' "$R")" = "open" ] || { echo "REG-CLOSE FAIL: $ID is not open"; exit 2; }
[ -f "$SUBJ" ] || { echo "REG-CLOSE FAIL: subject file $SUBJ missing"; exit 2; }

TITLE="$(awk -F'\t' -v i="$ID" '$1==i{print $4}' "$R")"
OPENED="$(awk -F'\t' -v i="$ID" '$1==i{print $10}' "$R")"
REC="docs/decisions/closed/$ID.yaml"

# The Section 97.2 decision-record field set, exactly. record_schema_version is
# deliberately absent until L0-DR-D2 is answered; pending_schema stands in its place.
{
  printf 'id: %s\n' "$ID"
  printf 'decider: founder\n'
  printf 'prompt_received: %s\n' "$OPENED"
  printf 'decided: %s\n' "$TODAY"
  printf 'subject: %s\n' "$TITLE"
  printf 'state: %s\n' "$STATE"
  printf 'options_considered:\n'
  sed -n 's/^option: /  - /p' "$SUBJ"
  printf 'evidence:\n'
  sed -n 's/^evidence: /  - /p' "$SUBJ"
  printf 'review_date: %s\n' "$(sed -n 's/^review_date: //p' "$SUBJ")"
  printf 'pending_schema: L0-DR-D2\n'
} > "$REC"

grep -c '^  - ' "$REC" >/dev/null
[ "$(sed -n 's/^review_date: //p' "$REC" | grep -c '^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}$')" = "1" ] \
  || { rm -f "$REC"; echo "REG-CLOSE FAIL: review_date must be an ISO date (Section 97.2)"; exit 2; }
[ "$(sed -n '/^options_considered:/,/^evidence:/p' "$REC" | grep -c '^  - ')" -ge 2 ] \
  || { rm -f "$REC"; echo "REG-CLOSE FAIL: at least two options_considered are required"; exit 2; }

awk -F'\t' -v OFS='\t' -v i="$ID" -v st="$STATE" -v rec="$REC" \
  '$1==i{$6=st; $9=rec} {print}' "$R" > "$R.new" && mv "$R.new" "$R"

echo "REG-CLOSE OK $ID -> $STATE $REC"
