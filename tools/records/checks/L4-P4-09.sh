#!/usr/bin/env bash
set -euo pipefail
# Check: L4-P4-09 -- writer negative suite (Master Spec Section 0.8 rules 3 and 7):
#   1) a hand-authored file dropped into a machine-only store is refused (no hand-edit path)
#   2) an in-place correction of an existing record is refused (no in-place edit)
#   3) an unvalidated (schema-failing) record is refused at write time
#   4) an untyped (undeclared) event is refused at write time
# Each case below is a neg_fixture: a deliberately bad input that MUST be rejected.
HERE="$(cd "$(dirname "$0")" && pwd)"
CP_DIR="$(cd "$HERE/../../.." && pwd)"
GUARD="$CP_DIR/tools/records/validate-human-record.sh"
[[ -x "$GUARD" ]] || { echo "ABSENT: $GUARD" >&2; exit 1; }

TMPDIRS=()
cleanup() { for d in "${TMPDIRS[@]:-}"; do [[ -n "$d" ]] && rm -rf "$d"; done; }
trap cleanup EXIT

export CP_ROOT="$CP_DIR"

# --- Cases 1 & 2: the no-hand-edit guard, over a throwaway git sandbox (mirrors L4-T315) ---
S="$(mktemp -d)"; TMPDIRS+=("$S")
mkdir -p "$S/records/postmortems" "$S/records/uat" "$S/events"
git -C "$S" init -q
git -C "$S" config user.email "check@test.invalid"
git -C "$S" config user.name "check"
git -C "$S" config core.autocrlf false
printf 'record_schema_version: 1\nid: PM-CHECK-001\nproduct: demoprod\ntimestamp: 2026-09-01T09:00:00+00:00\n' \
  > "$S/records/postmortems/PM-CHECK-001.yaml"
git -C "$S" add -A && git -C "$S" commit -q -m c0
export CPR_ROOT="$S"

# neg_fixture 1: hand-authored bad_fixture landing straight in a machine-only store (uat)
B1="$(git -C "$S" rev-parse HEAD)"
printf 'record_schema_version: 1\nid: HANDMADE\nproduct: demoprod\ntimestamp: 2026-09-01T09:00:00+00:00\n' \
  > "$S/records/uat/HANDMADE.yaml"
git -C "$S" add -A && git -C "$S" commit -q -m c1
CASE_MACHINE="$("$GUARD" "$B1" | head -1)" || true
[[ "$CASE_MACHINE" == "HUMAN-RECORD FAIL hand-authored-in-machine-store"* ]] \
  || { echo "neg_fixture 1 FAILED: hand-edit path was accepted: $CASE_MACHINE" >&2; exit 1; }

# neg_fixture 2: an in-place correction (M) of the existing postmortem record
B2="$(git -C "$S" rev-parse HEAD)"
printf 'corrected: true\n' >> "$S/records/postmortems/PM-CHECK-001.yaml"
git -C "$S" add -A && git -C "$S" commit -q -m c2
CASE_EDIT="$("$GUARD" "$B2" | head -1)" || true
[[ "$CASE_EDIT" == "HUMAN-RECORD FAIL in-place-edit"* ]] \
  || { echo "neg_fixture 2 FAILED: in-place correction was accepted: $CASE_EDIT" >&2; exit 1; }

# --- Case 3: an unvalidated record (fails the record envelope) is refused by record-write ---
export CPR_ROOT="$(mktemp -d)"; TMPDIRS+=("$CPR_ROOT")
mkdir -p "$CPR_ROOT/records/postmortems" "$CPR_ROOT/events"
BAD_BODY="$(mktemp)"; TMPDIRS+=("$BAD_BODY")
printf 'this: is-not-a-valid-postmortem-record\n' > "$BAD_BODY"
if OUT="$("$CP_DIR/tools/records/record-write" postmortems PM-BAD-001 "$BAD_BODY" postmortem.schema.json 2>&1)"; then
  echo "neg_fixture 3 FAILED: an unvalidated record was accepted: $OUT" >&2; exit 1
fi
grep -q 'invalid-record' <<<"$OUT" \
  || { echo "neg_fixture 3 FAILED: unexpected rejection reason: $OUT" >&2; exit 1; }

# --- Case 4: an untyped (undeclared) event is refused at write time ---
if OUT="$("$CP_DIR/tools/records/event-append" this.is.not.a.declared.event.type someone demoprod \
       records/postmortems/PM-CHECK-001.yaml 2>&1)"; then
  echo "neg_fixture 4 FAILED: an untyped event was accepted: $OUT" >&2; exit 1
fi
grep -q 'unknown-event-type' <<<"$OUT" \
  || { echo "neg_fixture 4 FAILED: unexpected rejection reason: $OUT" >&2; exit 1; }

echo "CHECK L4-P4-09 PASS"
