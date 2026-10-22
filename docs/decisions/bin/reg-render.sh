#!/usr/bin/env sh
# reg-render.sh — L0-owned. Render one markdown file per entry.
# Usage: ./docs/decisions/bin/reg-render.sh [<output-dir>]   default: docs/decisions/open
# Idempotent by construction: the output is a pure function of register.tsv.
# Last line: REG-RENDER OK files=<n>
set -eu
D="$(dirname "$0")/.."
R="$D/register.tsv"
OUT="${1:-$D/open}"
[ -f "$R" ] || { echo "REG-RENDER FAIL: register.tsv missing"; exit 2; }
rm -f "$OUT"/REG-*.md 2>/dev/null || true
mkdir -p "$OUT"

awk -F'\t' '!/^#/' "$R" | while IFS='	' read -r id band gates title decider state blocks sources record opened; do
  {
    printf '# %s — %s\n\n' "$id" "$title"
    printf '| | |\n|---|---|\n'
    printf '| Priority | %s |\n' "$band"
    printf '| Gates | %s |\n' "$gates"
    printf '| Decided by | %s |\n' "$decider"
    printf '| State | %s |\n' "$state"
    printf '| Opened | %s |\n\n' "$opened"
    printf '**Blocks.** %s\n\n' "$(printf '%s' "$blocks" | tr ',' ' ')"
    printf '**Raised as.** %s\n\n' "$(printf '%s' "$sources" | tr ',' ' ')"
    printf '**Full statement, with the option set and the interim behaviour in force:**\n'
    printf 'implementation/lanes/L0-04-decisions-register.md, section 3, entry %s.\n\n' "$id"
    printf 'RENDERED FILE — do not edit. Edit docs/decisions/register.tsv (L0D-DR-2).\n'
  } > "$OUT/$id.md"
done

echo "REG-RENDER OK files=$(ls -1 "$OUT"/REG-*.md 2>/dev/null | wc -l | tr -d ' ')"
