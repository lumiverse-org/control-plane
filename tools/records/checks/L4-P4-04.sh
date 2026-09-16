#!/usr/bin/env bash
set -euo pipefail
# Check: L4-P4-04 - Event id and date-partition path convention
# Master Spec v4.0 Section 97.3, line 8929: events/<YYYY-MM-DD>/<event_id>.yaml,
# one file per event, never a concurrent append to a shared period file.
CP_DIR="$(git rev-parse --show-toplevel)"
EP="$CP_DIR/tools/records/lib/eventpath.py"

# Positive: the library exists
[[ -f "$EP" ]] || { echo "ABSENT: $EP" >&2; exit 1; }

# Assertion 1: the path shape is exactly events/<YYYY-MM-DD>/<event_id>.yaml
P1="$(python3 "$EP" EVT-2026-09-16-000001 2026-09-16T10:00:00+00:00)"
echo "$P1" | grep -qE '^events/2026-09-16/EVT-2026-09-16-000001\.yaml$' \
  || { echo "unexpected path: $P1" >&2; exit 1; }

# Assertion 2: two distinct events on the same date produce two distinct files,
# sharing one date-partition directory, never a shared period file.
P2="$(python3 "$EP" EVT-2026-09-16-000002 2026-09-16T10:05:00+00:00)"
[ "$P1" != "$P2" ] || { echo "same-date events collided on one file: $P1" >&2; exit 1; }
[ "$(dirname "$P1")" = "$(dirname "$P2")" ] \
  || { echo "same-date events did not share a date partition" >&2; exit 1; }

# Negative fixture: an occurred_at with no UTC offset must be rejected
# (Section 97.1 line 8839; L4-06-tasks.md section 0.8 rule 8).
# bad_fixture: offset-free timestamp, expected to fail closed.
if python3 "$EP" EVT-BAD-FIXTURE 2026-09-16T10:00:00 >/dev/null 2>&1; then
  echo "expected rejection of offset-free occurred_at, got success" >&2
  exit 1
fi

# Negative fixture: an empty event_id must also be rejected.
if python3 "$EP" "" 2026-09-16T10:00:00+00:00 >/dev/null 2>&1; then
  echo "expected rejection of empty event_id, got success" >&2
  exit 1
fi

echo "CHECK L4-P4-04 PASS"
