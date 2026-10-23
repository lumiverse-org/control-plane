#!/usr/bin/env sh
# train-row.sh — L0-owned. Renders one cycle record as one markdown table row.
set -eu
F="${1:?cycle file required}"
val() { awk -F'\t' -v k="$1" '$1==k{print $2; exit}' "$F"; }
lane() { v=$(awk -F'\t' -v k="$1" '$1==k{print $2; exit}' "$F"); echo "${v:-NONE}"; }
printf '| %s | %s | %s | %s | %s | %s | %s | %s | %s |\n' \
  "$(val cycle)" "$(val date)" \
  "$(lane L1)" "$(lane L4)" "$(lane L2)" "$(lane L3)" "$(lane L5)" \
  "$(val promoted)" "$(val notes)"
