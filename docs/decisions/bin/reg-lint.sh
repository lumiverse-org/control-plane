#!/usr/bin/env sh
# reg-lint.sh — L0-owned. Integrity of the decision register.
# Usage: ./docs/decisions/bin/reg-lint.sh
# Last line is one of:
#   REG-LINT OK checks=8
#   REG-LINT FAIL <check-id>
# Exit 0 on pass, 1 on any failure. Fail-closed: a missing input is a FAIL, never a skip.
set -eu
D="$(dirname "$0")/.."
R="$D/register.tsv"; C="$D/concordance.tsv"
fail() { echo "REG-LINT FAIL $1"; exit 1; }

[ -f "$R" ] || fail L1-register-missing
[ -f "$C" ] || fail L3-concordance-missing

# L1 shape: 60 rows, 10 fields, no empty field
[ "$(grep -vc '^#' "$R")" = "60" ] || fail L1-row-count
[ "$(awk -F'\t' '!/^#/ && NF!=10' "$R" | wc -l | tr -d ' ')" = "0" ] || fail L1-field-count
[ "$(awk -F'\t' '!/^#/{for(i=1;i<=10;i++) if($i=="") print}' "$R" | wc -l | tr -d ' ')" = "0" ] || fail L1-empty-field

# L2 id space: unique and contiguous REG-001..REG-060 (L0D-DR-1).
# Runs BEFORE L3 because a broken id space also breaks the derived concordance,
# and the root cause must be the reported one.
awk -F'\t' '!/^#/{print $1}' "$R" | sort > /tmp/reg_have.txt
seq -f 'REG-%03g' 1 60 | sort > /tmp/reg_want.txt
diff -q /tmp/reg_have.txt /tmp/reg_want.txt >/dev/null 2>&1 || fail L2-id-space

# L3 concordance is a pure function of the register
awk -F'\t' '!/^#/{n=split($8,s,","); for(i=1;i<=n;i++){p=index(s[i],"@");
  printf "%s\t%s\t%s\n", substr(s[i],1,p-1), substr(s[i],p+1), $1}}' "$R" | sort > /tmp/reg_expect.tsv
grep -v '^#' "$C" | sort > /tmp/reg_actual.tsv
diff -q /tmp/reg_expect.tsv /tmp/reg_actual.tsv >/dev/null 2>&1 || fail L3-concordance-stale

# L4 vocabulary: priority, state, decider (L0D-DR-4, L0D-DR-5)
[ "$(awk -F'\t' '!/^#/ && $2 !~ /^P[0-3]$/' "$R" | wc -l | tr -d ' ')" = "0" ] || fail L4-priority
[ "$(awk -F'\t' '!/^#/ && $6 !~ /^(open|closed|declined|withdrawn)$/' "$R" | wc -l | tr -d ' ')" = "0" ] || fail L4-state
[ "$(awk -F'\t' '!/^#/ && $5!="L0"' "$R" | wc -l | tr -d ' ')" = "0" ] || fail L4-decider

# L5 phase tokens are from the closed set
[ "$(awk -F'\t' '!/^#/ && $3 !~ /^(Ph[0-7]|EH|G[1-8]|P[1-8])$/' "$R" | wc -l | tr -d ' ')" = "0" ] || fail L5-phase-token

# L6 record field agrees with state (L0D-DR-3)
[ "$(awk -F'\t' '!/^#/ && $6=="open" && $9!="-"' "$R" | wc -l | tr -d ' ')" = "0" ] || fail L6-open-has-record
MISSING=$(awk -F'\t' '!/^#/ && $6!="open" && $9!="-"{print $9}' "$R" \
  | while read -r f; do [ -f "$f" ] || echo x; done | wc -l | tr -d ' ')
[ "$MISSING" = "0" ] || fail L6-record-missing

# L7 no closure carries a fabricated record_schema_version (L0-DR-D2)
if [ -d "$D/closed" ]; then
  [ "$(grep -rl 'record_schema_version' "$D/closed" 2>/dev/null | wc -l | tr -d ' ')" = "0" ] || fail L7-fabricated-schema-version
fi

# L8 the rendered open/ files are exactly what the register renders
[ -x "$D/bin/reg-render.sh" ] || fail L8-renderer-missing
rm -rf /tmp/reg_render && mkdir -p /tmp/reg_render
"$D/bin/reg-render.sh" /tmp/reg_render >/dev/null
diff -rq "$D/open" /tmp/reg_render >/dev/null 2>&1 || fail L8-render-drift

echo "REG-LINT OK checks=8"
