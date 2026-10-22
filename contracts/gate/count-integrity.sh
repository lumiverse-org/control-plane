#!/usr/bin/env sh
# =============================================================================
# count-integrity.sh - L0-owned (contracts/gate/**, L0D-IG-1). D44 made mechanical.
#   --scope lane --lane <N>   the LG-08 form
#   --scope integration       the IG-05 form (adds the reconciler comparison ratchet)
# Last line on stdout is the verdict. Exit 0 pass, 1 fail, 2 config error.
# =============================================================================
set -eu
GD="$(dirname "$0")"; SCOPE=""; LANE=""
while [ $# -gt 0 ]; do case "$1" in
  --scope) SCOPE="$2"; shift 2 ;;
  --lane)  LANE="$2";  shift 2 ;;
  *) echo "COUNT-INTEGRITY FAIL: unknown argument '$1'"; exit 2 ;;
esac; done
[ "$SCOPE" = "lane" ] || [ "$SCOPE" = "integration" ] || { echo "COUNT-INTEGRITY FAIL: --scope lane|integration required"; exit 2; }
CPR="${CPR_ROOT:-$(cd "$GD/../../.." && pwd)/control-plane-records}"
OUT="${GATE_OUT:-.gate}"; mkdir -p "$OUT"; DET="$OUT/count-integrity.txt"; : > "$DET"
NARROW=0

decl() { awk -F'\t' -v k="$1" '!/^#/ && $1==k {print $2; exit}' "$GD/COUNTS.tsv"; }

# triple <label> <declared> <unique> <cells>
triple() {
  printf '%s declared=%s unique=%s cells=%s\n' "$1" "$2" "$3" "$4" >> "$DET"
  if [ "$2" = "$3" ] && [ "$3" = "$4" ]; then return 0; fi
  NARROW=$((NARROW+1)); return 1
}

# --- acceptance tests: one file per test, generated from the id set ----------
AT_D=$(decl at)
AT_DIR="$CPR/records/acceptance"
if [ -d "$AT_DIR" ]; then
  AT_CELLS=$(find "$AT_DIR" -name 'AT-*.yaml' | wc -l | tr -d ' ')
  AT_UNIQ=$(grep -h '^id:' "$AT_DIR"/AT-*.yaml 2>/dev/null | awk '{print $2}' | sort -u | wc -l | tr -d ' ')
else
  AT_CELLS=0; AT_UNIQ=0
fi
triple at "$AT_D" "$AT_UNIQ" "$AT_CELLS" || true

# --- invariants and edge cases: frozen L0 id sets, two-way ------------------
INV_D=$(decl inv); INV_C=$(grep -c . "$GD/inv-index.tsv"); INV_U=$(sort -u "$GD/inv-index.tsv" | grep -c .)
EC_D=$(decl ec);   EC_C=$(grep -c . "$GD/ec-index.tsv");   EC_U=$(sort -u "$GD/ec-index.tsv" | grep -c .)
[ "$INV_D" = "$INV_U" ] && [ "$INV_U" = "$INV_C" ] || NARROW=$((NARROW+1))
[ "$EC_D" = "$EC_U" ]  && [ "$EC_U"  = "$EC_C" ]  || NARROW=$((NARROW+1))
printf 'inv declared=%s unique=%s cells=%s\nec declared=%s unique=%s cells=%s\n' \
  "$INV_D" "$INV_U" "$INV_C" "$EC_D" "$EC_U" "$EC_C" >> "$DET"

# --- gate checks ------------------------------------------------------------
CK_D=$(decl checks); CK_C=$(grep -c . "$GD/expected-checks.txt"); CK_U=$(sort -u "$GD/expected-checks.txt" | grep -c .)
[ "$CK_D" = "$CK_U" ] && [ "$CK_U" = "$CK_C" ] || NARROW=$((NARROW+1))

# --- the sum rules ----------------------------------------------------------
while IFS='	' read -r rid total addends _; do
  case "$rid" in ''|\#*) continue ;; esac
  t=$(decl "$total"); s=0
  for a in $(echo "$addends" | tr ',' ' '); do s=$((s + $(decl "$a"))); done
  if [ "$s" != "$t" ]; then NARROW=$((NARROW+1)); printf '%s BROKEN %s=%s sum=%s\n' "$rid" "$total" "$t" "$s" >> "$DET"
  else printf '%s OK %s=%s\n' "$rid" "$total" "$t" >> "$DET"; fi
done < "$GD/COUNTS.rules.tsv"

# --- L0-IG-D1: two declared pair counts is itself a narrowing risk -----------
if [ -n "$(decl ct_pairs_p00)" ] && [ -n "$(decl ct_pairs_p01)" ]; then
  NARROW=$((NARROW+1))
  echo "L0-IG-D1 UNRESOLVED: ct_pairs_p00=$(decl ct_pairs_p00) ct_pairs_p01=$(decl ct_pairs_p01)" >> "$DET"
fi

REG="n/a"
if [ "$SCOPE" = "integration" ]; then
  # Section 53.1: "Every run additionally records its per-registry comparison counts
  # ... so that a silently narrowed comparison is itself visible drift."
  RUN=$(ls -1 "$CPR"/records/reconciliation/*.yaml 2>/dev/null | LC_ALL=C sort | tail -1 || true)
  if [ -z "$RUN" ]; then
    REG="0/0"; NARROW=$((NARROW+1)); echo "no reconciliation run record found" >> "$DET"
  else
    RD=$(awk '/^ *declared_registries:/{print $2}' "$RUN"); RC=$(awk '/^ *compared_registries:/{print $2}' "$RUN")
    RD=${RD:-0}; RC=${RC:-0}; REG="$RC/$RD"
    [ "$RD" -gt 0 ] && [ "$RC" = "$RD" ] || { NARROW=$((NARROW+1)); echo "registry comparison narrowed $REG" >> "$DET"; }
    PREV=$(ls -1 "$CPR"/records/reconciliation/*.yaml 2>/dev/null | LC_ALL=C sort | tail -2 | head -1 || true)
    if [ "$PREV" != "$RUN" ] && [ -f "$PREV" ]; then
      PC=$(awk '/^ *compared_registries:/{print $2}' "$PREV"); PC=${PC:-0}
      [ "$RC" -ge "$PC" ] || { NARROW=$((NARROW+1)); echo "registry ratchet fell $PC -> $RC" >> "$DET"; }
    fi
  fi
fi

LBL="COUNT-INTEGRITY"
if [ "$NARROW" -eq 0 ]; then
  printf '%s PASS at=%s/%s/%s inv=%s/%s ec=%s/%s checks=%s/%s registries=%s narrowed=0\n' \
    "$LBL" "$AT_D" "$AT_UNIQ" "$AT_CELLS" "$INV_D" "$INV_U" "$EC_D" "$EC_U" "$CK_D" "$CK_U" "$REG"
  exit 0 # exit 0 = gate ARMED (FD-035)
fi
printf '%s FAIL at=%s/%s/%s inv=%s/%s ec=%s/%s checks=%s/%s registries=%s narrowed=%s\n' \
  "$LBL" "$AT_D" "$AT_UNIQ" "$AT_CELLS" "$INV_D" "$INV_U" "$EC_D" "$EC_U" "$CK_D" "$CK_U" "$REG" "$NARROW"
exit 1
