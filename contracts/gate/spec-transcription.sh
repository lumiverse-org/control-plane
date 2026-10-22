#!/usr/bin/env sh
# =============================================================================
# spec-transcription.sh - L0-owned (contracts/gate/**, L0D-IG-1).
# Proves (a) the frozen id sets are a true transcription of the specification and
# (b) every FROZEN ANOMALY in spec-anomalies.tsv is STILL PRESENT (L0D-IG-4).
# Last line on stdout is the verdict. Exit 0 pass, 1 fail, 2 config error.
# =============================================================================
set -eu
GD="$(dirname "$0")"
SPEC="${GATE_SPEC:-$(cat "$GD/SPEC_PATH" 2>/dev/null || true)}"
fail_cfg() { echo "SPEC-TRANSCRIPTION FAIL: $1" ; exit 2; }
[ -n "$SPEC" ] && [ -f "$SPEC" ] || fail_cfg "specification not found at '$SPEC'"
[ -f "$GD/SPEC.sha256" ] || fail_cfg "SPEC.sha256 missing"
[ -f "$GD/spec-anomalies.tsv" ] || fail_cfg "spec-anomalies.tsv missing"

OUT="${GATE_OUT:-.gate}"; mkdir -p "$OUT"
DET="$OUT/spec-transcription.txt"; : > "$DET"

HAVE=$(sha256sum "$SPEC" | cut -d' ' -f1)
WANT=$(cat "$GD/SPEC.sha256")
if [ "$HAVE" != "$WANT" ]; then
  echo "spec digest have=$HAVE want=$WANT" >> "$DET"
  echo "SPEC-TRANSCRIPTION FAIL digest_match=0 anomalies=0/0"
  exit 1
fi

# --- Section 100 slice: preamble line to the line before Section 101 ----------
S100_BEG=$(grep -n '^## Section 100\.' "$SPEC" | head -1 | cut -d: -f1)
S100_END=$(grep -n '^## Section 101\.' "$SPEC" | head -1 | cut -d: -f1)
[ -n "$S100_BEG" ] && [ -n "$S100_END" ] || fail_cfg "Section 100/101 headings not found"
sed -n "${S100_BEG},$((S100_END-1))p" "$SPEC" > "$OUT/s100.raw"

ROWS=$(grep -c '^| AT-[0-9][0-9][0-9] |' "$OUT/s100.raw" || true)
UNIQ=$(grep -o '^| AT-[0-9][0-9][0-9] ' "$OUT/s100.raw" | tr -d '| ' | sort -u | wc -l | tr -d ' ')
CELLS=$(grep -o '| AT-[0-9][0-9][0-9] |' "$OUT/s100.raw" | wc -l | tr -d ' ')
printf 'section100 rows=%s unique=%s cells=%s\n' "$ROWS" "$UNIQ" "$CELLS" >> "$DET"

# --- the frozen id set must equal the specification's UNIQUE id set -----------
grep -o '^| AT-[0-9][0-9][0-9] ' "$OUT/s100.raw" | tr -d '| ' | sort -u > "$OUT/s100.ids"
if diff -q "$GD/at-index.tsv" "$OUT/s100.ids" >/dev/null 2>&1; then IDSET=1; else IDSET=0
  diff "$GD/at-index.tsv" "$OUT/s100.ids" >> "$DET" || true
fi

# --- every frozen anomaly must STILL be found --------------------------------
TOTAL=0; FOUND=0
while IFS='	' read -r id sec kind sig; do
  case "$id" in ''|\#*) continue ;; esac
  TOTAL=$((TOTAL+1))
  hit=0
  case "$kind" in
    duplicated-id-cell)
      # exactly one more id cell than unique ids, and the surplus is AT-110
      if [ "$CELLS" -eq $((UNIQ+1)) ] && grep -q '^| AT-109 |.*| AT-110 |' "$OUT/s100.raw"; then hit=1; fi
      ;;
    *) hit=0 ;;
  esac
  if [ "$hit" -eq 1 ]; then FOUND=$((FOUND+1)); printf '%s FOUND (%s)\n' "$id" "$sig" >> "$DET"
  else printf '%s ABSENT - parser stopped looking, or the input changed (%s)\n' "$id" "$sig" >> "$DET"; fi
done < "$GD/spec-anomalies.tsv"

# --- an anomaly nobody declared is new drift ---------------------------------
SURPLUS=$((CELLS - UNIQ - TOTAL))
[ "$SURPLUS" -lt 0 ] && SURPLUS=0

if [ "$IDSET" -eq 1 ] && [ "$FOUND" -eq "$TOTAL" ] && [ "$SURPLUS" -eq 0 ]; then
  printf 'SPEC-TRANSCRIPTION PASS digest_match=1 idset_match=1 anomalies=%s/%s undeclared=0\n' "$FOUND" "$TOTAL"
  exit 0 # exit 0 = gate ARMED (FD-035)
fi
printf 'SPEC-TRANSCRIPTION FAIL digest_match=1 idset_match=%s anomalies=%s/%s undeclared=%s\n' \
  "$IDSET" "$FOUND" "$TOTAL" "$SURPLUS"
exit 1
