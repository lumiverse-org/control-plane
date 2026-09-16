#!/usr/bin/env python3
"""tools/records/lib/eventpath.py
Event id and date-partition path convention (L4-06-tasks.md row L4-P4-04;
Master Spec v4.0 Section 97.3, line 8929).

Every event resolves to its own file:

    events/<YYYY-MM-DD>/<event_id>.yaml

One file per event. There is never a concurrent append to a shared period
file, and two events landing on the same date produce two distinct files
because each carries its own unique event_id.

This module computes the path only; it does not write anything. The writer
that mints event_id and performs the write is tools/records/lib/emit.sh
(L4-T305). This module is the independently testable path-resolution
primitive named by the L4-P4-04 task row.

CLI usage:
    eventpath.py <event_id> <occurred_at>

Prints the relative path on success and exits 0. Exits 1 with a message on
stderr if occurred_at carries no UTC offset (Section 97.1, line 8839) or if
event_id is empty or unsafe as a path component.
"""
import re
import sys

OFFSET_RE = re.compile(r"(Z|[+-]\d{2}:\d{2})$")
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})T\d{2}:\d{2}:\d{2}")
ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def event_path(event_id, occurred_at):
    """Return the events/<YYYY-MM-DD>/<event_id>.yaml path for one event.

    Raises ValueError if:
      - event_id is empty, or contains anything but [A-Za-z0-9._-] (would
        escape its date-partition directory or collide across events), or
      - occurred_at carries no UTC offset (Section 97.1 line 8839), or
      - occurred_at does not parse as a YYYY-MM-DDTHH:MM:SS... instant.
    """
    if not event_id or not ID_RE.match(event_id):
        raise ValueError("invalid-event-id:%s" % event_id)
    if not OFFSET_RE.search(occurred_at):
        raise ValueError("timestamp-without-utc-offset:%s" % occurred_at)
    m = DATE_RE.match(occurred_at)
    if not m:
        raise ValueError("unparseable-occurred_at:%s" % occurred_at)
    date = m.group(1)
    return "events/%s/%s.yaml" % (date, event_id)


def main(argv):
    if len(argv) != 3:
        print("EVENTPATH ERROR usage: eventpath.py <event_id> <occurred_at>", file=sys.stderr)
        return 3
    try:
        print(event_path(argv[1], argv[2]))
    except ValueError as exc:
        print("EVENTPATH FAIL %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
