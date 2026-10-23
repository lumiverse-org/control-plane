#!/usr/bin/env sh
# =============================================================================
# onboard-stream.sh — L0-owned. The DevOps-capacity serialiser.
# MasterSpec v4.0 Section 73.1 (spec L6005): "Brownfield onboarding and platform
# work serialise on DevOps capacity — only one such stream can proceed at a
# time — and the staffing diagnosis treats this serialisation as its own
# constraint shape, distinct from aggregate engineering demand."
# Occupying phases (this plan section 4.1): OT-P4, OT-P6, platform.
# Append-only: a claim writes one file; a release writes another. Nothing edits.
# usage: onboard-stream.sh holder | check
#        onboard-stream.sh claim <product|platform> <ref> <OT-P4|OT-P6|platform> <YYYY-MM-DD>
#        onboard-stream.sh release <seq> <YYYY-MM-DD>
# =============================================================================
set -u
OB="${OB_ROOT:-docs/onboarding}"
C="$OB/stream/claims"; R="$OB/stream/releases"
is_date() { case "$1" in [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) return 0 ;; *) return 1 ;; esac; }
kv() { awk -F'\t' -v k="$2" '$1==k{print $2; f=1} END{if(!f) print "UNSET"}' "$1"; }

held() {                       # prints the seq of every unreleased claim
  for f in "$C"/*.tsv; do
    [ -f "$f" ] || continue
    s=$(kv "$f" seq)
    [ -f "$R/$s.tsv" ] || echo "$s"
  done
}

case "${1:-}" in
  holder)
    n=0
    for s in $(held); do
      n=$((n+1))
      f=$(ls "$C"/"$s"-*.tsv 2>/dev/null | head -1)
      echo "STREAM HOLDER seq=$s kind=$(kv "$f" kind) ref=$(kv "$f" ref) phase=$(kv "$f" phase) since=$(kv "$f" claimed_on)"
    done
    [ "$n" -eq 0 ] && echo "STREAM FREE"
    exit 0 ;;
  check)
    n=$(held | wc -l | tr -d ' ')
    bad=0
    for f in "$C"/*.tsv; do
      [ -f "$f" ] || continue
      p=$(kv "$f" phase); k=$(kv "$f" kind)
      case "$p" in OT-P4|OT-P6|platform) : ;; *) echo "STREAM-INVALID seq=$(kv "$f" seq) phase=$p does not occupy the stream (section 4.1)"; bad=$((bad+1)) ;; esac
      case "$k" in product|platform) : ;; *) echo "STREAM-INVALID seq=$(kv "$f" seq) kind=$k"; bad=$((bad+1)) ;; esac
    done
    echo "STREAM-CHECK claims=$(ls "$C" 2>/dev/null | wc -l | tr -d ' ') open=$n invalid=$bad"
    { [ "$n" -le 1 ] && [ "$bad" -eq 0 ]; } || exit 1
    exit 0 ;;
  claim)
    [ $# -eq 5 ] || { echo "usage: onboard-stream.sh claim <kind> <ref> <phase> <date>" >&2; exit 2; }
    kind="$2"; ref="$3"; phase="$4"; when="$5"
    case "$kind"  in product|platform) : ;; *) echo "BAD-KIND $kind" >&2; exit 2 ;; esac
    case "$phase" in OT-P4|OT-P6|platform) : ;; *) echo "PHASE-DOES-NOT-OCCUPY-THE-STREAM $phase (section 4.1)" >&2; exit 2 ;; esac
    is_date "$when" || { echo "NOT-A-DATE $when" >&2; exit 2; }
    h=$(held | head -1)
    if [ -n "$h" ]; then
      hf=$(ls "$C"/"$h"-*.tsv 2>/dev/null | head -1)
      echo "STREAM BUSY holder=$h ref=$(kv "$hf" ref) phase=$(kv "$hf" phase) — Section 73.1 permits one stream at a time"
      exit 1
    fi
    n=$(ls "$C" 2>/dev/null | wc -l | tr -d ' '); n=$((n+1)); seq=$(printf '%03d' "$n")
    printf 'seq\t%s\nkind\t%s\nref\t%s\nphase\t%s\nclaimed_on\t%s\n' "$seq" "$kind" "$ref" "$phase" "$when" \
      > "$C/$seq-$kind-$ref.tsv"
    echo "STREAM CLAIMED seq=$seq kind=$kind ref=$ref phase=$phase on=$when"
    exit 0 ;;
  release)
    [ $# -eq 3 ] || { echo "usage: onboard-stream.sh release <seq> <date>" >&2; exit 2; }
    seq="$2"; when="$3"
    is_date "$when" || { echo "NOT-A-DATE $when" >&2; exit 2; }
    ls "$C"/"$seq"-*.tsv >/dev/null 2>&1 || { echo "NO-SUCH-CLAIM $seq" >&2; exit 1; }
    [ -f "$R/$seq.tsv" ] && { echo "ALREADY-RELEASED $seq" >&2; exit 1; }
    printf 'seq\t%s\nreleased_on\t%s\n' "$seq" "$when" > "$R/$seq.tsv"
    echo "STREAM RELEASED seq=$seq on=$when"
    exit 0 ;;
  *) echo "usage: onboard-stream.sh holder|check|claim|release" >&2; exit 2 ;;
esac
STREAM
