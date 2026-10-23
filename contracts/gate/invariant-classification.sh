#!/usr/bin/env sh
# =============================================================================
# invariant-classification.sh - L0-owned (contracts/gate/**, L0D-IG-1). IG-06.
# Row format: invariant<TAB>class<TAB>reference<TAB>note
#   class: mechanical | policy | review-held | unclassified
#   mechanical -> reference must be a check id in expected-checks.txt
#                 or an AT id in at-activation.tsv
#   policy     -> reference must be a live entry key in registries/policies.yaml
# Last line on stdout is the verdict. Exit 0 pass, 1 fail, 2 config error.
# =============================================================================
set -eu
GD="$(dirname "$0")"
OUT="${GATE_OUT:-.gate}"; mkdir -p "$OUT"; DET="$OUT/invariant-classification.txt"; : > "$DET"
MAP="$GD/invariant-classification.tsv"
[ -f "$MAP" ] || { echo "INVARIANT-CLASSIFICATION FAIL: map missing - fail closed"; exit 2; }

DECL=$(awk -F'\t' '$1=="inv"{print $2}' "$GD/COUNTS.tsv")
ROWS=$(grep -vc '^#' "$MAP")
CLASSIFIED=0; MECH=0; DANGLING=0; UNCLASS=0
CHECKS="$GD/expected-checks.txt"; ATS=$(cut -f2 "$GD/at-activation.tsv" | grep '^AT-' | sort -u)
POL="registries/policies.yaml"

while IFS='	' read -r inv cls ref note; do
  case "$inv" in ''|\#*) continue ;; esac
  case "$cls" in
    mechanical)
      CLASSIFIED=$((CLASSIFIED+1)); MECH=$((MECH+1))
      if grep -qxF "$ref" "$CHECKS" || printf '%s\n' "$ATS" | grep -qxF "$ref"; then :
      else DANGLING=$((DANGLING+1)); printf 'inv %s mechanical -> %s DANGLING\n' "$inv" "$ref" >> "$DET"; fi ;;
    policy)
      CLASSIFIED=$((CLASSIFIED+1))
      if [ -f "$POL" ] && grep -q "^ *${ref}:" "$POL"; then :
      else DANGLING=$((DANGLING+1)); printf 'inv %s policy -> %s DANGLING (subsystem O, L0-IG-D3)\n' "$inv" "$ref" >> "$DET"; fi ;;
    review-held)
      CLASSIFIED=$((CLASSIFIED+1))
      [ -n "$ref" ] && [ "$ref" != "-" ] || { DANGLING=$((DANGLING+1)); printf 'inv %s review-held names no review\n' "$inv" >> "$DET"; } ;;
    *)
      UNCLASS=$((UNCLASS+1)); printf 'inv %s UNCLASSIFIED\n' "$inv" >> "$DET" ;;
  esac
done < "$MAP"

[ "$UNCLASS" -eq 0 ] || printf 'L0-IG-D3 UNRESOLVED: %s invariants unclassified; policies.yaml belongs to subsystem O, unassigned in PARTITION v1; section 101 authors the map at Phase G2\n' "$UNCLASS" >> "$DET"

if [ "$ROWS" = "$DECL" ] && [ "$CLASSIFIED" = "$DECL" ] && [ "$DANGLING" -eq 0 ] && [ "$UNCLASS" -eq 0 ]; then
  printf 'INVARIANT-CLASSIFICATION PASS classified=%s/%s mechanical=%s dangling_refs=0 unclassified=0\n' "$CLASSIFIED" "$DECL" "$MECH"
  exit 0 # exit 0 = gate ARMED (FD-035)
fi
printf 'INVARIANT-CLASSIFICATION FAIL classified=%s/%s mechanical=%s dangling_refs=%s unclassified=%s\n' \
  "$CLASSIFIED" "$DECL" "$MECH" "$DANGLING" "$UNCLASS"
exit 1
