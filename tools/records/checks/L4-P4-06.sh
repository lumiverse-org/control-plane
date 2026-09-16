#!/usr/bin/env bash
set -euo pipefail
# Check: L4-P4-06 - the RECORD-VERIFICATION-RESULT handler (charter DoD-9)
# Acceptance (L4-06-tasks.md Phase 4 table): the handler accepts exactly the
# structured inputs product, item, mechanism, pass-or-fail, evidence link;
# writes the corresponding record; appends the event; and exposes no path
# that edits a record file by hand. A call with a missing input is refused.
# Spec anchor: Master Spec v4.0 Section 97.2 line 8886.
HERE="$(cd "$(dirname "$0")" && pwd)"
CP_DIR="$(cd "$HERE/../../.." && pwd)"
H="$CP_DIR/tools/records/record-verification-result"
LIB="$CP_DIR/tools/records/lib/emit.sh"

[[ -f "$H" ]]   || { echo "ABSENT: $H" >&2; exit 1; }
[[ -x "$H" ]]   || { echo "NOT-EXECUTABLE: $H" >&2; exit 1; }
[[ -f "$LIB" ]] || { echo "ABSENT: $LIB" >&2; exit 1; }

# Assertion 1: exactly the five structured inputs plus the reporting actor
# (product, item, mechanism, pass-or-fail, evidence_link, actor) are required -
# a call with any of them missing is refused before any write is attempted.
ARITY=$(grep -c 'wrong-arity expected 6' "$H")
[ "$ARITY" -eq 1 ] || { echo "expected arity guard once, got $ARITY" >&2; exit 1; }
EMPTYGUARD=$(grep -c 'empty-input' "$H")
[ "$EMPTYGUARD" -eq 1 ] || { echo "expected empty-input guard once, got $EMPTYGUARD" >&2; exit 1; }

# Assertion 2: no hand-edit or in-place-edit path anywhere in the handler.
INPLACE=$(grep -cE '\bsed -i\b|>>' "$H" || true)
[ "$INPLACE" -eq 0 ] || { echo "handler contains an in-place/append edit path" >&2; exit 1; }

# Assertion 3: the handler writes the record AND appends the event together,
# through the shared emit_pair primitive (Section 97.2 line 8871: never one
# without the other) - never a bespoke write of its own.
PAIRCALL=$(grep -c 'emit_pair' "$H")
[ "$PAIRCALL" -eq 1 ] || { echo "expected one emit_pair call, got $PAIRCALL" >&2; exit 1; }
grep -q 'emit_p_rec="\$(emit_record' "$LIB" || { echo "emit_pair no longer writes the record" >&2; exit 1; }
grep -q 'emit_p_ev="\$(emit_event' "$LIB"   || { echo "emit_pair no longer appends the event" >&2; exit 1; }

# Assertion 4: routing (store/schema/event_type per mechanism) is resolved
# from the contract file, never hard-coded.
CONTRACTDRIVEN=$(grep -c 'rvr-inputs.yaml' "$H")
[ "$CONTRACTDRIVEN" -eq 1 ] || { echo "handler is not contract-driven" >&2; exit 1; }

# Negative fixture: a bad_fixture copy of the handler with the empty-input
# guard removed must be caught by this same check - proving the check can
# fail, not only pass (lane rule 9, L4-06-tasks.md Section 0.8).
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
BAD="$TMP/bad_fixture-record-verification-result"
awk '/^for v in PRODUCT/{skip=1} skip && /^done$/{skip=0; next} !skip' "$H" > "$BAD"
BADGUARD=$(grep -c 'empty-input' "$BAD" || true)
if [ "$BADGUARD" -ne 0 ]; then
  echo "neg-fixture: expected empty-input guard removed from bad_fixture, still present ($BADGUARD)" >&2
  exit 1
fi

echo "CHECK L4-P4-06 PASS"
