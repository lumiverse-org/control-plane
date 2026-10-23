#!/usr/bin/env sh
# =============================================================================
# bootstrap-log-gen.sh — L0-owned. The weekly bootstrap log entry of
# MasterSpec v4.0 Section 95.4 (spec L8708). Three fields; two generated.
# Usage: bootstrap-log-gen.sh [YYYY-MM-DD]   (default: today, UTC)
# Exit 0 written / 2 configuration error — FAIL CLOSED.
# =============================================================================
set -u
CP="${CP:-$PWD}"
D="${1:-$(date -u +%F)}"
REG="$CP/docs/bootstrap/gate-register.tsv"
MTX="$CP/docs/bootstrap/arming-matrix.tsv"
DIR="$CP/docs/plan/bootstrap-log"
OUT="$DIR/$D.md"
TAB=$(printf '\t')
cfgfail() { printf 'BOOTSTRAP-LOG FAIL: configuration error — %s\n' "$1"; exit 2; }
[ -f "$REG" ] || cfgfail "gate-register.tsv not found at $REG"
[ -f "$MTX" ] || cfgfail "arming-matrix.tsv not found at $MTX"
case "$D" in [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) : ;; *) cfgfail "date must be YYYY-MM-DD — got '$D'" ;; esac
mkdir -p "$DIR" || cfgfail "cannot create $DIR"
SINCE=$(date -u -d "$D -7 days" +%F) || cfgfail "date arithmetic failed"
{
  printf '# BOOTSTRAP LOG — week ending %s\n\n' "$D"
  printf 'Template: MasterSpec v4.0 Section 95.4 (spec L8708). Fields 1 and 2 are generated;\n'
  printf 'field 3 is seeded and L0 writes the result lines. Detector: Blocking drift when the\n'
  printf 'newest entry is older than the calibrated staleness window, initial value 7 days.\n\n'

  printf '## Field 1 — gates stubbed and armed  (GENERATED from docs/bootstrap/gate-register.tsv)\n\n'
  printf '| gate scope | threshold | state | expiry | renewals | closure |\n|---|---|---|---|---|---|\n'
  awk -F"$TAB" '!/^#/ && NF==14 { st = ($12=="-") ? "STUBBED" : "ARMED";
    printf "| %s | %s | %s | %s | %s | %s |\n", $3, $2, st, $9, $11, $12 }' "$REG"
  printf '\n'
  printf '| branch-protection setting | unarmed | armed | arms at |\n|---|---|---|---|\n'
  awk -F"$TAB" '!/^#/ && NF==7 && $5!="day-one" { printf "| %s | %s | %s | %s |\n", $2, $3, $4, $5 }' "$MTX"

  printf '\n## Field 2 — bootstrap exceptions opened and closed this week  (GENERATED)\n\n'
  printf '```\n'
  git -C "$CP" log --since="$SINCE" --date=short --format='%h %ad %s' \
      --name-status -- docs/bootstrap/exceptions/ docs/bootstrap/gate-register.tsv 2>/dev/null \
    || printf 'git log unavailable\n'
  printf '```\n'
  printf '\nOpen exceptions past their review_date, needing an L0 look this week:\n\n```\n'
  awk -F"$TAB" -v d="$D" '!/^#/ && NF==14 && $12=="-" && $10 <= d { printf "%s  %s  review_date %s  expiry %s\n", $1, $3, $10, $9 }' "$REG"
  printf '```\n'

  printf '\n## Field 3 — phase completion checks run this week, and their results  (SEEDED — L0 writes the result lines)\n\n'
  printf '```\n'
  gh run list --limit 100 --json name,headBranch,conclusion,createdAt \
     --jq ".[] | select(.createdAt >= \"$SINCE\") | [.createdAt, .name, .headBranch, .conclusion] | @tsv" 2>/dev/null \
    || printf 'gh unavailable — list the runs by hand\n'
  printf '```\n\n'
  printf 'RESULT LINES — one per completion check actually run this week. L0 writes these.\n\n'
  printf -- '- check: <the Section 98.2 phase and the named completion check>\n'
  printf -- '  evidence: <workflow run URL, or the command and its output>\n'
  printf -- '  result: <PASS | FAIL | NOT-RUN>\n'
  printf -- '  judgment: <one line. Automation writes state; humans write meaning (Section 94.9)>\n\n'
  printf 'OPEN ITEMS CARRIED (delete the line when it clears):\n\n'
  printf -- '- <e.g. Phase 1 exceptions-validator CI half: PENDING-L1 (L0-06-06)>\n'
} > "$OUT" || cfgfail "cannot write $OUT"
printf 'BOOTSTRAP-LOG WRITTEN %s\n' "$OUT"
exit 0
